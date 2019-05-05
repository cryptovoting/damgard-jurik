import os
import webauthn

from flask import flash
from flask import jsonify
from flask import make_response
from flask import redirect
from flask import request
from flask import session
from flask import url_for
from flask import Blueprint
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user

from ..helpers import generate_challenge, generate_ukey
from ..models import Authority, Voter, Election
from ..settings import SERVER_NAME
from ..extensions import db

blueprint = Blueprint('auth', __name__)

ORIGIN = SERVER_NAME
RP_ID = SERVER_NAME.split(':')[0]

# Trust anchors (trusted attestation roots) should be
# placed in TRUST_ANCHOR_DIR.
TRUST_ANCHOR_DIR = '../trusted_attestation_roots'


@blueprint.route('/webauthn_begin_activate', subdomain='<election>', methods=['POST'])
def webauthn_begin_activate(election):

    if 'election_role' in session:
        split = session['election_role'].split('_')
        if len(split) == 2 and split[0] == election:
            session['role'] = split[1]
        else:
            session['role'] = "voter"
    else:
        session['role'] = "voter"

    email = session['email']
    name = session['name']
    role = session['role']

    if role != "authority" and role != "voter":
        return make_response(jsonify({'fail': 'Invalid role.'}), 401)

    if not len(email):
        return make_response(jsonify({'fail': 'Invalid email.'}), 401)
    if not len(name):
        return make_response(jsonify({'fail': 'Invalid  name.'}), 401)

    if Authority.query.filter(Election.name==election, Authority.email==email).first() or \
       Voter.query.filter(Election.name==election, Authority.email==email).first():
        return make_response(jsonify({'fail': 'User already exists.'}), 401)

    if 'register_ukey' in session:
        del session['register_ukey']
    if 'register_username' in session:
        del session['register_username']
    if 'register_display_name' in session:
        del session['register_display_name']
    if 'challenge' in session:
        del session['challenge']

    session['email'] = email
    session['name'] = name

    rp_name = RP_ID
    origin = f"http://{election}.{ORIGIN}"
    challenge = generate_challenge(32)
    ukey = generate_ukey()

    session['challenge'] = challenge
    session['register_ukey'] = ukey

    make_credential_options = webauthn.WebAuthnMakeCredentialOptions(
        challenge, rp_name, RP_ID, ukey, email, name, origin)

    return jsonify(make_credential_options.registration_dict)


@blueprint.route('/webauthn_begin_assertion', subdomain='<election>', methods=['POST'])
def webauthn_begin_assertion(election):
    email = request.form.get('email')

    if not len(email):
        return make_response(jsonify({'fail': 'Invalid email.'}), 401)

    role = "authority"
    user = Authority.query.filter_by(election=election, email=email).first()
    if not user:
        user = Voter.query.filter_by(election=election, email=email).first()
        role = "voter"
    if not user:
        return make_response(jsonify({'fail': 'User does not exist.'}), 401)
    if not user.credential_id:
        return make_response(jsonify({'fail': 'Unknown credential ID.'}), 401)

    if 'challenge' in session:
        del session['challenge']

    challenge = generate_challenge(32)

    session['challenge'] = challenge

    if 'role' in session:
        del session['role']
    session['role'] = role

    webauthn_user = webauthn.WebAuthnUser(
        user.ukey, user.username, user.display_name, user.icon_url,
        user.credential_id, user.pub_key, user.sign_count, user.rp_id)

    webauthn_assertion_options = webauthn.WebAuthnAssertionOptions(
        webauthn_user, challenge)

    return jsonify(webauthn_assertion_options.assertion_dict)


@blueprint.route('/verify_credential_info', subdomain='<election>', methods=['POST'])
def verify_credential_info(election):
    challenge = session['challenge']
    email = session['email']
    name = session['name']
    phone = session['phone']
    ukey = session['register_ukey']

    role = session['role']
    if role == "authority":
        User = Authority
    elif role == "voter":
        User = Voter
    else:
        return jsonify({'fail': 'Invalid role.'})

    registration_response = request.form
    trust_anchor_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), TRUST_ANCHOR_DIR)
    trusted_attestation_cert_required = True
    self_attestation_permitted = True
    none_attestation_permitted = True

    rp_name = RP_ID
    origin = f"http://{election}.{ORIGIN}"

    webauthn_registration_response = webauthn.WebAuthnRegistrationResponse(
        rp_name,
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

    # Step 17.
    #
    # Check that the credentialId is not yet registered to any other user.
    # If registration is requested for a credential that is already registered
    # to a different user, the Relying Party SHOULD fail this registration
    # ceremony, or it MAY decide to accept the registration, e.g. while deleting
    # the older registration.
    credential_id_exists = User.query.filter_by(
        credential_id=webauthn_credential.credential_id).first()
    if credential_id_exists:
        return make_response(
            jsonify({
                'fail': 'Credential ID already exists.'
            }), 401)

    existing_user = User.query.filter(Election.name==election, User.email==email).first()
    if not existing_user:
        webauthn_credential.credential_id = str(
            webauthn_credential.credential_id, "utf-8")
        # Create the election
        election_data = Election(election)
        # Create the user
        user = User(
            ukey=ukey,
            email=email,
            name=name,
            phone=phone,
            election = election_data,
            pub_key=webauthn_credential.public_key,
            credential_id=webauthn_credential.credential_id,
            sign_count=webauthn_credential.sign_count,
            rp_id=rp_name,
            icon_url=origin)
        db.session.add(user)
        db.session.commit()
    else:
        return make_response(jsonify({'fail': 'User already exists.'}), 401)

    return jsonify({'success': 'User successfully registered.'})


@blueprint.route('/verify_assertion', subdomain='<election>', methods=['POST'])
def verify_assertion(election):
    challenge = session.get('challenge')
    assertion_response = request.form
    credential_id = assertion_response.get('id')

    user = Authority.query.filter_by(election=election, credential_id=credential_id).first()
    if not user:
        user = Voter.query.filter_by(election=election, credential_id=credential_id).first()
    if not user:
        return make_response(jsonify({'fail': 'User does not exist.'}), 401)

    webauthn_user = webauthn.WebAuthnUser(
        user.ukey, user.username, user.display_name, user.icon_url,
        user.credential_id, user.pub_key, user.sign_count, user.rp_id)

    origin = f"http://{election}.{ORIGIN}"

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

    # Update counter.
    user.sign_count = sign_count
    db.session.add(user)
    db.session.commit()

    login_user(user)

    return jsonify({
        'success':
        'Successfully authenticated as {}'.format(user.username)
    })


@blueprint.route('/logout', subdomain='<election>')
@login_required
def logout(election):
    logout_user()
    return redirect(url_for('election.election_home', election=election))
