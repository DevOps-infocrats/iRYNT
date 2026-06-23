import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    WTF_CSRF_TIME_LIMIT = None
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    DRIVER_DOCUMENT_UPLOAD_FOLDER = os.environ.get('DRIVER_DOCUMENT_UPLOAD_FOLDER') or os.path.join(os.path.dirname(__file__), 'instance', 'driver_documents')

    # JWT configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=20)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=14)
    JWT_TOKEN_LOCATION = ['headers']
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_CSRF_PROTECT = True

    PASSWORD_RESET_TOKEN_EXPIRES = int(os.environ.get('PASSWORD_RESET_TOKEN_EXPIRES', 3600))
    ACCOUNT_LOCK_THRESHOLD = int(os.environ.get('ACCOUNT_LOCK_THRESHOLD', 5))
    ACCOUNT_LOCK_DURATION_MINUTES = int(os.environ.get('ACCOUNT_LOCK_DURATION_MINUTES', 15))
    PASSWORD_EXPIRE_DAYS = int(os.environ.get('PASSWORD_EXPIRE_DAYS', 90))
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or "postgresql://postgres:1234@localhost:5432/VILdatabase"

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
