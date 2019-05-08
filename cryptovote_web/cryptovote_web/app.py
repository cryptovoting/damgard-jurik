import os

from flask import Flask, render_template
from flask_migrate import Migrate
from . import settings, controllers, models
from .extensions import db, install_secret_key, login_manager, title, suppress_none

project_dir = os.path.dirname(os.path.abspath(__file__))


def create_app(config_object=settings):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)

    register_extensions(app)
    register_blueprints(app)
    register_errorhandlers(app)
    return app


def register_extensions(app):
    """Register Flask extensions."""
    # Load a secret key for web sessions
    install_secret_key(app)
    # Initialize databse
    db.init_app(app)
    # Create any database tables that don't exist
    with app.app_context():
        db.create_all()
    # Add support for database migrations
    Migrate(app, db)
    # Add support for users logging in
    login_manager.init_app(app)
    # Add custom HTML rendering filters
    app.jinja_env.filters["title"] = title
    app.jinja_env.filters["suppress_none"] = suppress_none
    return None


def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(controllers.home.blueprint)
    app.register_blueprint(controllers.create_election.blueprint)
    app.register_blueprint(controllers.election.blueprint)
    app.register_blueprint(controllers.auth.blueprint)
    app.register_blueprint(controllers.vote.blueprint)
    return None


def register_errorhandlers(app):
    """Register error handlers."""
    @app.errorhandler(401)
    def internal_error(error):
        return render_template('401.html'), 401

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('500.html'), 500

    return None
