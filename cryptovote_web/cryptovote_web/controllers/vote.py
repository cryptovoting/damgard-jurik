# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, redirect, url_for, session, request, flash
from random import shuffle
from ..helpers import election_exists
from ..models import Voter, Candidate, Authority
from ..extensions import db
from cryptovote.ballots import CandidateOrderBallot

blueprint = Blueprint('vote', __name__)


@blueprint.route('/voter-registration', subdomain="<election>")
@election_exists
def voter_registration(election):
    if 'k' not in request.args:
        return redirect(url_for('election.election_home', election=election.name))
    voter = Voter.query.filter_by(email_key=request.args['k']).first()
    if not voter:
        return redirect(url_for('election.election_home', election=election.name))
    session['k'] = request.args['k']
    if not voter.name:
        return redirect(url_for('vote.confirm_name', election=election.name))
    else:
        return redirect(url_for('vote.vote', election=election.name))


@blueprint.route('/confirm-name', subdomain="<election>", methods=['GET', 'POST'])
@election_exists
def confirm_name(election):
    if 'k' not in session:
        return redirect(url_for('election.election_home', election=election.name))
    voter = Voter.query.filter_by(email_key=session['k']).first()
    if not voter:
        return redirect(url_for('election.election_home', election=election.name))
    if request.method == 'GET':
        return render_template('vote/confirm_name.html', election=election)
    else:
        name = request.form.get("name")
        if not name:
            flash("Must specify a name.")
            return render_template('vote/confirm_name.html', election=election)
        voter.name = name
        db.session.commit()
        return redirect(url_for('vote.vote', election=election.name))


@blueprint.route('/vote', subdomain="<election>", methods=['GET', 'POST'])
@election_exists
def vote(election):
    if 'k' not in session:
        return redirect(url_for('election.election_home', election=election.name))
    voter = Voter.query.filter_by(email_key=session['k']).first()
    if not voter:
        return redirect(url_for('election.election_home', election=election.name))
    if voter.ballot:
        flash("Your ballot has already been cast.")
        return redirect(url_for('election.election_home', election=election.name))
    candidates = election.candidates
    shuffle(candidates)
    if request.method == 'GET':
        return render_template('vote/vote.html', election=election, candidates=candidates)
    else:
        ballot = request.form.get("ballot")
        if not ballot:
            flash("No ballot submitted.")
            return render_template('vote/vote.html', election=election, candidates=candidates)
        authority = Authority.query.filter_by(election=election).first()
        if not authority:
            flash("Election is missing authorities.")
            return redirect(url_for('election.election_home', election=election.name))
        public_key = authority.public_key
        if not public_key:
            flash("Authority missing public key.")
            return redirect(url_for('election.election_home', election=election.name))
        preferences = []
        for candidate in ballot.split(','):
            c = Candidate.query.filter_by(election=election, name=candidate).first()
            if not c:
                flash("Invalid ballot.")
                return render_template('vote/vote.html', election=election, candidates=candidates)
            preferences.append(public_key.encrypt(c.id))
        candidates = []
        for candidate in election.candidates:
            candidates.append(candidate.id)
        weight = public_key.encrypt(1)
        voter.ballot = CandidateOrderBallot(candidates, preferences, weight)
        election.bulletin += f"{voter.id}: "
        for preference in preferences:
            election.bulletin += str(preference.value) + " "
        election.bulletin += "\n\n"
        db.session.commit()
        flash("Ballot cast successfully")
        return redirect(url_for('election.election_home', election=election.name))
