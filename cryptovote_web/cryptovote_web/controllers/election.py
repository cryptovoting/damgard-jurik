# -*- coding: utf-8 -*-
from flask import Blueprint, render_template
from ..helpers import election_exists
from ..models import Election

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
