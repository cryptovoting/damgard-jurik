import re
from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from flask_login import login_required
from ..models import Election, UnconfirmedAuthority, Authority
from ..helpers import send_authority_confirm_email, election_exists
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

        if Election.query.filter_by(name=session['election']).first():
            flash(f"Election \'{session['election']}\' already exists.")
            return redirect(url_for('create_election.create_election_name'))
        # Confirm email address
        user = UnconfirmedAuthority(election_name=session['election'],
                                    name=session['name'],
                                    email=session['email'])
        db.session.add(user)
        db.session.commit()
        send_authority_confirm_email(user, request.url_root)
        return render_template('create_election/check_email.html')


@blueprint.route('/confirm-email')
def confirm_email():
    if 'k' not in request.args:
        print("Missing k")
        return redirect(url_for('home.index'))
    user = UnconfirmedAuthority.query.filter_by(email_key=request.args['k']).first()
    if not user:
        return redirect(url_for('home.index'))
    if Authority.query.filter(Election.name == user.election_name, Authority.email == user.email).first():
        return redirect(url_for('election.election_home', election=user.election_name))
    session['election'] = user.election_name
    session['email'] = user.email
    session['name'] = user.name
    session['k'] = user.email_key
    return redirect(url_for('create_election.register_identity', election=user.election_name))


@blueprint.route('/setup', subdomain='<election>')
def register_identity(election):
    for key in ['election', 'name', 'email', 'k']:
        if key not in session:
            return redirect(url_for('home.index'))
    user = UnconfirmedAuthority.query.filter_by(email_key=session['k']).first()
    if not user:
        return redirect(url_for('home.index'))
    if Authority.query.filter(Election.name == user.election_name, Authority.email == user.email).first():
        return redirect(url_for('election.election_home', election=user.election_name))
    session['election'] = user.election_name
    session['email'] = user.email
    session['name'] = user.name
    return render_template('create_election/register_identity.html')


@blueprint.route('/add-candidates', subdomain='<election>', methods=['GET', 'POST'])
@login_required
@election_exists
def add_candidates(election):
    if request.method == 'GET':
        return render_template('create_election/add_candidates.html', election=election)
    else:
        candidates = request.form.get("candidates", "")
        election.candidates = candidates
        db.session.commit()
        return redirect(url_for('election.register_voters', election=election.name))
