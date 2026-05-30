import os
from datetime import timedelta
from dotenv import load_dotenv
load_dotenv()

_DEFAULT_SECRET = 'dev_key_change_in_production'

class Config:
    """Configuration par défaut"""
    
    # Flask
    SECRET_KEY = os.environ.get('FLASK_SECRET', _DEFAULT_SECRET)
    DEBUG = os.environ.get('DEBUG', 'False') == 'True'
    TESTING = False
    
    # Base de données - Attributs directs
    DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'team_nobiel')
    DB_PORT = int(os.environ.get('DB_PORT', '3306'))
    
    # Construire l'URI SQLAlchemy
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Cookie/Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_HTTPONLY = True
    
    # CSRF - délai étendu pour les connexions mobiles lentes
    WTF_CSRF_TIME_LIMIT = 7200  # 2 heures
    
    # Upload files
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max (pour les vidéos)
    UPLOAD_FOLDER = 'app/static/uploads'

    # CinetPay (paiement mobile — Orange, MTN, Wave)
    CINETPAY_API_KEY = os.environ.get('CINETPAY_API_KEY', '')
    CINETPAY_SITE_ID = os.environ.get('CINETPAY_SITE_ID', '')
    CINETPAY_SECRET_KEY = os.environ.get('CINETPAY_SECRET_KEY', '')

    # Email (Flask-Mail)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@nobiel.ci')
    MAIL_SUPPRESS_SEND = not bool(os.environ.get('MAIL_USERNAME', ''))

class DevelopmentConfig(Config):
    """Configuration en développement"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """Configuration en production"""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_ECHO = False
    SESSION_COOKIE_SECURE = True  # HTTPS uniquement en production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', Config.SQLALCHEMY_DATABASE_URI)

    def __init_subclass__(cls, **kwargs):
        pass

    @classmethod
    def validate(cls):
        if cls.SECRET_KEY == _DEFAULT_SECRET:
            raise RuntimeError(
                "SECRET_KEY non configurée ! Définissez FLASK_SECRET dans .env avant de lancer en production."
            )

class TestingConfig(Config):
    """Configuration pour les tests"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
