# app/__init__.py
"""
Application factory module for the NASA PDF Tool.
Initialises the Flask application, configures security headers using Flask-Talisman,
and registers routes in compliance with NASA coding guidelines.
"""

import os
from flask import Flask
from flask_talisman import Talisman

from config import config

def create_app(config_name=None):
    """
    Create and configure the Flask application.
    
    :param config_name: The configuration name (e.g., 'development', 'production').
                        Defaults to the 'default' configuration.
    :return: A configured Flask application instance.
    """
    # Determine configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG') or 'default'
    
    # Create the Flask app instance
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Ensure the upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Set up security headers with Flask-Talisman
    # Force HTTPS if SESSION_COOKIE_SECURE is True (typically in production)
    Talisman(app,
             content_security_policy=app.config['TALISMAN_CONTENT_SECURITY_POLICY'],
             force_https=app.config.get('SESSION_COOKIE_SECURE', True))
    
    # Register the main blueprint containing our routes
    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    # Additional initialisations such as error handlers or logging can be added here
    return app