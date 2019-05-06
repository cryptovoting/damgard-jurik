# -*- coding: utf-8 -*-
from flask import Blueprint, render_template
from flask_login import login_required
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


@blueprint.route('/authorities', subdomain='<election>')
@election_exists
def authority_list(election):
    return render_template('election/authority_list.html', election=election)


@blueprint.route('/results', subdomain='<election>')
@election_exists
def results(election):
    return render_template('election/results.html', election=election)

@blueprint.route('/manage', subdomain='<election>')
@login_required
@election_exists
def manage(election):
    return render_template('election/manage.html', election=election)
