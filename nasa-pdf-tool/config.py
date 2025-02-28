# config.py
"""
Configuration module for the NASA PDF Tool web application.
This configuration adheres to strict security practices and robust coding guidelines,
ensuring safe operations for file handling, session management, and overall application behaviour.
"""

import os

class BaseConfig:
    """
    Base configuration with default settings.
    
    Key settings:
    - SECRET_KEY: Used for session management and CSRF protection.
    - DEBUG: Should be False in production.
    - TALISMAN_CONTENT_SECURITY_POLICY: Defines a secure Content Security Policy.
    - MAX_CONTENT_LENGTH: Limits the maximum upload size (e.g., 20 MB for PDFs).
    - UPLOAD_FOLDER: Directory for temporarily storing uploaded files.
    - FILE_RETENTION_TIME: Time in seconds before an uploaded file is auto-deleted (2 minutes).
    - SESSION_COOKIE_SECURE: Ensures session cookies are sent only over HTTPS.
    """
    # Use a secure random key in production; override with an environment variable
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'replace_this_with_a_secure_random_value'
    
    # Disable debug mode by default for security
    DEBUG = False
    
    # Flask-Talisman Content Security Policy settings for enhanced security
    TALISMAN_CONTENT_SECURITY_POLICY = {
        'default-src': [
            "'self'",
            # Include trusted CDN sources if needed (e.g., for fonts or CSS frameworks)
            'https://maxcdn.bootstrapcdn.com',
            'https://cdnjs.cloudflare.com',
            'https://ajax.googleapis.com'
        ]
    }
    
    # Maximum allowed upload size set to 20 MB
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20 MB in bytes
    
    # Directory to store uploaded PDF files temporarily (ensure this directory exists and is secure)
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or os.path.join(os.getcwd(), 'uploads')
    
    # Time (in seconds) after which uploaded files are automatically deleted (2 minutes)
    FILE_RETENTION_TIME = 120  # seconds
    
    # Enforce secure cookies to prevent session hijacking (only transmitted over HTTPS)
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

class DevelopmentConfig(BaseConfig):
    """
    Development configuration settings.
    
    Note: In development mode, we might relax some settings (like secure cookies)
    for easier local testing, but security is still a priority.
    """
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # May allow insecure cookies in development
    REMEMBER_COOKIE_SECURE = False

class ProductionConfig(BaseConfig):
    """
    Production configuration settings.
    
    This configuration follows NASA's strict security guidelines.
    Debugging is disabled and secure cookies are enforced.
    """
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

# Mapping configuration names to classes for easy selection in our app factory
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}