# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_required
from json import loads
from ..helpers import election_exists, send_vote_email
from ..models import Voter, Election, Authority, Candidate
from ..extensions import db
from cryptovote.protocols import stv_tally


blueprint = Blueprint('election', __name__)


@blueprint.route('/', subdomain='<election>')
@election_exists
def election_home(election):
    return render_template('election/election_home.html', election=election)


@blueprint.route('/voters', subdomain='<election>')
@election_exists
def voter_list(election):
    return render_template('election/voter_list.html', election=election)


@blueprint.route('/bulletin', subdomain='<election>')
@election_exists
def bulletin(election):
    return render_template('election/bulletin.html', election=election)


@blueprint.route('/authorities', subdomain='<election>')
@election_exists
def authority_list(election):
    return render_template('election/authority_list.html', election=election)


@blueprint.route('/results', subdomain='<election>')
@election_exists
def results(election):
    if not election.results:
        return redirect(url_for('election.election_home', election=election.name))
    elected_candidates = []
    for elected in election.results.split(','):
        candidate = Candidate.query.filter_by(id=elected).first()
        if not candidate:
            flash("The calculated results contain an error.")
            return redirect(url_for('election.election_home', election=election.name))
        elected_candidates.append(candidate)
    return render_template('election/results.html', election=election, elected_candidates=elected_candidates)


@blueprint.route('/register-voters', subdomain='<election>', methods=['GET', 'POST'])
@login_required
@election_exists
def register_voters(election):
    if request.method == 'GET':
        return render_template('election/register_voters.html', election=election)
    else:
        # Add the new voters to the database
        voter_emails = loads(request.form.get('voter_emails', ""))
        for email in voter_emails:
            # Ensure that the voter doesn't already exist
            user = Voter.query.filter(Voter.election == election,
                                      Voter.email == email).first()
            if not user:
                voter = Voter(email=email, election=election)
                db.session.add(voter)
                send_vote_email(voter, request.url_root)
        db.session.commit()
        # Redirect to the election homepage
        return redirect(url_for('election.election_home', election=election.name))


@blueprint.route('/candidates', subdomain='<election>')
@election_exists
def candidates(election):
    return render_template('election/candidates.html', election=election)


@blueprint.route('/tally-results', subdomain='<election>')
@login_required
@election_exists
def tally_results(election):
    return render_template("election/tally_results.html", election=election)


@blueprint.route('/compute-election', subdomain='<election>', methods=['POST'])
@login_required
@election_exists
def compute_election(election):
    if not election.seats:
        flash("Number of election seats not specified.")
        return jsonify({'success': False})
    authority = Authority.query.filter_by(election=election).first()
    if not authority:
        flash("Election has no authorities.")
        return jsonify({'success': False})
    if not authority.public_key or not authority.private_key_ring:
        flash("Authority missing valid key pair.")
        return jsonify({'success': False})
    ballots = []
    for voter in election.voters:
        if voter.ballot:
            ballots.append(voter.ballot)
    if not ballots:
        flash("No candidates have cast ballots.")
        return jsonify({'success': False})
    results = stv_tally(ballots,
                        election.seats,
                        -1,
                        authority.private_key_ring,
                        authority.public_key)
    election.results = ",".join(map(str,results))
    db.session.commit()
    return jsonify({'success': True})
