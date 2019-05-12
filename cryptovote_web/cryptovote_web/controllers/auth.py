import os
import webauthn
from flask import jsonify, make_response, redirect, request, session, url_for, Blueprint, render_template, flash
from flask_login import login_required, login_user, logout_user, current_user
from ..helpers import generate_challenge, generate_ukey, election_exists
from ..models import Authority, Election
from ..settings import SERVER_NAME
from ..extensions import db, login_manager, bcrypt

blueprint = Blueprint('auth', __name__)

ORIGIN = SERVER_NAME
RP_ID = SERVER_NAME.split(':')[0]

# Trust anchors (trusted attestation roots) should be
# placed in TRUST_ANCHOR_DIR.
TRUST_ANCHOR_DIR = '../trusted_attestation_roots'


@login_manager.user_loader
def load_user(user_id):
    return Authority.query.get(user_id)


@blueprint.route('/webauthn_begin_activate', subdomain='<election>', methods=['POST'])
def webauthn_begin_activate(election):
    email = session['email']
    name = session['name']

    if not len(email):
        return make_response(jsonify({'fail': 'Invalid email.'}), 401)
    if not len(name):
        return make_response(jsonify({'fail': 'Invalid  name.'}), 401)

    if Authority.query.filter(Election.name==election, Authority.email==email).first():
        return make_response(jsonify({'fail': 'User already exists.'}), 401)

    if 'register_ukey' in session:
        del session['register_ukey']
    if 'register_username' in session:
        del session['register_username']
    if 'register_display_name' in session:
        del session['register_display_name']
    if 'challenge' in session:
        del session['challenge']

    http = request.url.split("://")
    origin = f"{http[0]}://{election}.{ORIGIN}"
    challenge = generate_challenge(32)
    ukey = generate_ukey()

    session['challenge'] = challenge
    session['register_ukey'] = ukey

    make_credential_options = webauthn.WebAuthnMakeCredentialOptions(
        challenge, RP_ID, RP_ID, ukey, email, name, origin)

    return jsonify(make_credential_options.registration_dict)


@blueprint.route('/webauthn_begin_assertion', subdomain='<election>', methods=['POST'])
def webauthn_begin_assertion(election):
    email = request.form.get('email')

    if not len(email):
        return make_response(jsonify({'fail': 'Invalid email.'}), 401)

    user = Authority.query.filter(Election.name == election,
                                  Authority.email == email).first()
    if not user:
        return make_response(jsonify({'fail': 'User does not exist.'}), 401)
    if not user.webauthn:
        session['email'] = email
        return jsonify({'alt-login': 'password'})
    if not user.credential_id:
        return make_response(jsonify({'fail': 'Unknown credential ID.'}), 401)

    if 'challenge' in session:
        del session['challenge']
    challenge = generate_challenge(32)
    session['challenge'] = challenge

    webauthn_user = webauthn.WebAuthnUser(
        user.ukey, user.email, user.name, user.icon_url,
        user.credential_id, user.pub_key, user.sign_count, user.rp_id)

    webauthn_assertion_options = webauthn.WebAuthnAssertionOptions(
        webauthn_user, challenge)

    return jsonify(webauthn_assertion_options.assertion_dict)


@blueprint.route('/verify_credential_info', subdomain='<election>', methods=['POST'])
def verify_credential_info(election):
    challenge = session['challenge']
    email = session['email']
    name = session['name']
    ukey = session['register_ukey']

    registration_response = request.form
    trust_anchor_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), TRUST_ANCHOR_DIR)
    trusted_attestation_cert_required = True
    self_attestation_permitted = True
    none_attestation_permitted = True

    http = request.url.split("://")
    origin = f"{http[0]}://{election}.{ORIGIN}"

    webauthn_registration_response = webauthn.WebAuthnRegistrationResponse(
        RP_ID,
        origin,
        registration_response,
        challenge,
        trust_anchor_dir,
        trusted_attestation_cert_required,
        self_attestation_permitted,
        none_attestation_permitted,
        uv_required=False)  # User Verification

    try:
        webauthn_credential = webauthn_registration_response.verify()
    except Exception as e:
        return jsonify({'fail': 'Registration failed. Error: {}'.format(e)})

    credential_id_exists = Authority.query.filter_by(
        credential_id=webauthn_credential.credential_id).first()
    if credential_id_exists:
        return make_response(
            jsonify({
                'fail': 'Credential ID already exists.'
            }), 401)

    if not current_user.is_authenticated:
        if Election.query.filter_by(name=election).first():
            return make_response(jsonify({'fail': 'Attempted to create initial authority for existing election.'}), 401)

    existing_user = Authority.query.filter(
        Election.name == election, Authority.email == email).first()
    if not existing_user:
        webauthn_credential.credential_id = str(
            webauthn_credential.credential_id, "utf-8")
        # Create the election
        election_data = Election(election)
        # Create the user
        user = Authority(
            ukey=ukey,
            email=email,
            name=name,
            election=election_data,
            webauthn=True,
            pub_key=webauthn_credential.public_key,
            credential_id=webauthn_credential.credential_id,
            sign_count=webauthn_credential.sign_count,
            rp_id=RP_ID,
            icon_url=origin)
        db.session.add(election_data)
        db.session.add(user)
        db.session.commit()
    else:
        return make_response(jsonify({'fail': 'User already exists.'}), 401)

    login_user(user)

    return jsonify({'success': 'User successfully registered.'})


@blueprint.route('/verify_assertion', subdomain='<election>', methods=['POST'])
def verify_assertion(election):
    challenge = session.get('challenge')
    assertion_response = request.form
    credential_id = assertion_response.get('id')

    user = Authority.query.filter(Election.name == election,
                                  Authority.credential_id == credential_id).first()
    if not user:
        return make_response(jsonify({'fail': 'User does not exist.'}), 401)

    webauthn_user = webauthn.WebAuthnUser(
        user.ukey, user.email, user.name, user.icon_url,
        user.credential_id, user.pub_key, user.sign_count, user.rp_id)

    http = request.url.split("://")
    origin = f"{http[0]}://{election}.{ORIGIN}"

    webauthn_assertion_response = webauthn.WebAuthnAssertionResponse(
        webauthn_user,
        assertion_response,
        challenge,
        origin,
        uv_required=False)  # User Verification

    try:
        sign_count = webauthn_assertion_response.verify()
    except Exception as e:
        return jsonify({'fail': 'Assertion failed. Error: {}'.format(e)})

    # Update counter
    user.sign_count = sign_count
    db.session.add(user)
    db.session.commit()

    login_user(user)

    return jsonify({
        'success':
        'Successfully authenticated as {}'.format(user.email)
    })


@blueprint.route('/logout', subdomain='<election>')
@login_required
@election_exists
def logout(election):
    logout_user()
    return redirect(url_for('election.election_home', election=election.name))


@blueprint.route('/login', subdomain='<election>')
@election_exists
def login(election):
    return render_template('auth/authority_login.html', election=election)


@blueprint.route('/login-password', subdomain='<election>', methods=['GET','POST'])
@election_exists
def login_password(election):
    if 'email' not in session:
        return redirect(url_for('election.election_home', election=election.name))
    user = Authority.query.filter(Election.name==election.name, Authority.email==session['email']).first()
    if not user:
        flash("User does not exist.")
        return redirect(url_for('election.election_home', election=election.name))
    if request.method == 'GET':
        return render_template('auth/authority_login_password.html', election=election)
    else:
        password = request.form.get("password")
        if not password:
            flash("Password not submitted.")
            return render_template('auth/authority_login_password.html', election=election)
        if not bcrypt.check_password_hash(user.pw_hash, password):
            flash("Invalid password.")
            return render_template('auth/authority_login_password.html', election=election)
        login_user(user)
        if 'next' in request.args:
            return redirect(request.args['next'])
        return redirect(url_for('election.election_home', election=election.name))
