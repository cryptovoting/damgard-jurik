# -*- coding: utf-8 -*-
from flask import Blueprint, render_template

blueprint = Blueprint('create_election', __name__)

@blueprint.route('/create')
def create_name():
    return render_template('create_election/create_name.html')
