# -*- coding: utf-8 -*-
from flask import Blueprint, render_template

blueprint = Blueprint('home', __name__)

@blueprint.route('/')
def index():
    return render_template('home/index.html')

@blueprint.route('/about')
def about():
    return render_template('home/about.html')
