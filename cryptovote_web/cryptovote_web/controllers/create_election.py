import re
from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from ..models import Election
from ..extensions import db

blueprint = Blueprint('create_election', __name__)


@blueprint.route('/create', methods=['GET', 'POST'])
def create_election_name():
    for key in ['election', 'name', 'email', 'phone']:
        if key in session:
            del session[key]
    if request.method == 'GET':
        return render_template('create_election/election_name.html')
    else:
        election = request.form.get('election')
        election = re.sub(r'[^a-z0-9\-]+', '', election.lower().replace(' ', '-'))
        if not election:
            flash("Must specify an election name.")
            return render_template('create_election/election_name.html')
        session['election'] = election
        session['election_role'] = f"{election}_authority"
        return redirect(url_for('create_election.verify_name'))


@blueprint.route('/verify-name', methods=['GET', 'POST'])
def verify_name():
    for key in ['name', 'email', 'phone']:
        if key in session:
            del session[key]
    if 'election' not in session:
        flash('Election name not specified.')
        return redirect(url_for('create_election.create_election_name'))
    if request.method == 'GET':
        return render_template('create_election/verify_name.html')
    else:
        name = request.form.get('name')
        if not name:
            flash("Must specify a name.")
            return render_template('create_election/verify_name.html')
        session['name'] = name
        return redirect(url_for('create_election.verify_email'))


@blueprint.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    for key in ['email', 'phone']:
        if key in session:
            del session[key]
    if 'election' not in session:
        flash('Election name not specified.')
        return redirect(url_for('create_election.create_election_name'))
    if 'name' not in session:
        flash('Name not specified.')
        return redirect(url_for('create_election.verify_name'))
    if request.method == 'GET':
        return render_template('create_election/verify_email.html')
    else:
        email = request.form.get('email')
        if not email:
            flash("Must specify an email address.")
            return render_template('create_election/verify_email.html')
        session['email'] = email
        return redirect(url_for('create_election.verify_phone'))


@blueprint.route('/verify-phone', methods=['GET', 'POST'])
def verify_phone():
    if 'phone' in session:
        del session['phone']
    if 'election' not in session:
        flash('Election name not specified.')
        return redirect(url_for('create_election.create_election_name'))
    if 'name' not in session:
        flash('Name not specified.')
        return redirect(url_for('create_election.verify_name'))
    if 'email' not in session:
        flash('Email not specified.')
        return redirect(url_for('create_election.verify_email'))
    if request.method == 'GET':
        return render_template('create_election/verify_phone.html')
    else:
        phone = request.form.get('phone')
        if not phone:
            flash("Must specify a phone number.")
            return render_template('create_election/verify_phone.html')
        session['phone'] = phone

        # Create the election in the database
        if Election.query.filter_by(name=session['election']).first():
            flash(f"Election \'{session['election']}\' already exists.")
            return redirect(url_for('create_election.create_election_name'))
        election = Election(session['election'])
        db.session.add(election)
        db.session.commit()
        return redirect(url_for('create_election.register_identity',
                                election=session['election']))


@blueprint.route('/setup', subdomain='<election>')
def register_identity(election):
    return render_template('create_election/register_identity.html')


@blueprint.route('/register-authorities', subdomain='<election>')
def register_authorities(election):
    return render_template('create_election/register_authorities.html')


@blueprint.route('/register-voters', subdomain='<election>')
def register_voters(election):
    return render_template('create_election/register_voters.html')
