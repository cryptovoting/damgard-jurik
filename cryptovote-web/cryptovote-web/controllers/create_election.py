# -*- coding: utf-8 -*-
from flask import Blueprint, render_template

blueprint = Blueprint('create_election', __name__)

@blueprint.route('/create')
def create_name():
    return render_template('create_election/election_name.html')


@blueprint.route('/verify-email')
def verify_email():


    return render_template('create_election/verify_email.html')
@blueprint.route('/verify-phone')
def verify_phone():
    return render_template('create_election/verify_phone.html')
