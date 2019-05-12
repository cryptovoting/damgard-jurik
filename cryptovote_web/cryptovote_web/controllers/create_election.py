import re
from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from flask_login import login_required, logout_user, login_user, current_user
from ..models import Election, UnconfirmedAuthority, Authority, Candidate
from ..helpers import send_authority_confirm_email, election_exists
from ..extensions import db, bcrypt

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


@blueprint.route('/create-password', subdomain='<election>', methods=['GET','POST'])
def create_password(election):
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
    if request.method == 'GET':
        return render_template('create_election/create_password.html', election=election)
    if request.method == 'POST':
        print(request.form)
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if not password or not confirm_password:
            flash("Password must be specified.")
            return render_template('create_election/create_password.html', election=election)
        if password != confirm_password:
            flash("Passwords do not match.")
            return render_template('create_election/create_password.html', election=election)
        if current_user.is_authenticated:
            logout_user(current_user)
        if Election.query.filter_by(name=election).first():
            flash("Election already exists.")
            return redirect(url_for('home.index'))
        existing_user = Authority.query.filter(
            Election.name == election, Authority.email == user.email).first()
        if existing_user:
            flash("User already exists.")
            return redirect(url_for('election.election_home', election=election))
        # Create the election
        election_data = Election(election)
        # Create the user
        pw_hash = bcrypt.generate_password_hash(password)
        authority = Authority(
            email=user.email,
            name=user.name,
            election=election_data,
            webauthn=False,
            pw_hash=pw_hash
            )
        db.session.add(election_data)
        db.session.add(authority)
        db.session.commit()
        # Login the new user
        login_user(authority)
        return redirect(url_for('create_election.seats', election=election))


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
    return render_template('create_election/register_identity.html', election=election)


@blueprint.route('/add-candidates', subdomain='<election>', methods=['GET', 'POST'])
@login_required
@election_exists
def add_candidates(election):
    if request.method == 'GET':
        return render_template('create_election/add_candidates.html', election=election)
    else:
        candidates = request.form.get("candidates", "").split(",")
        for candidate in candidates:
            c = Candidate(name=candidate.strip(), election=election)
            db.session.add(c)
        db.session.commit()
        return redirect(url_for('election.register_voters', election=election.name))


@blueprint.route('/seats', subdomain='<election>', methods=['GET', 'POST'])
@login_required
@election_exists
def seats(election):
    if election.seats:
        flash("The number of seats has already been set for this election.")
        return redirect(url_for('election.election_home', election=election.name))
    if request.method == 'GET':
        return render_template('create_election/seats.html', election=election)
    else:
        seats = request.form.get('seats')
        if not seats or not seats.isdigit() or int(seats) < 1:
            flash("Invalid number of seats.")
            return render_template('create_election/seats.html', election=election)
        election.seats = int(seats)
        db.session.commit()
        return redirect(url_for('create_election.add_candidates', election=election.name))
