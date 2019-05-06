import re
from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from ..models import Election
from ..extensions import db

blueprint = Blueprint('create_election', __name__)


@blueprint.route('/create', methods=['GET', 'POST'])
def create_election_name():
    for key in ['election', 'name', 'email']:
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
        election_data = Election.query.filter_by(name=election).first()
        if election_data:
            flash(f"Election \"{election}\" already exists.")
            return render_template('create_election/election_name.html')
        session['election'] = election
        return redirect(url_for('create_election.verify_name'))


@blueprint.route('/verify-name', methods=['GET', 'POST'])
def verify_name():
    for key in ['name', 'email']:
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
    if 'email' in session:
        del session['email']
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

        # Create the election in the database
        if Election.query.filter_by(name=session['election']).first():
            flash(f"Election \'{session['election']}\' already exists.")
            return redirect(url_for('create_election.create_election_name'))
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
