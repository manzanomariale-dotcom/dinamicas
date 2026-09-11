import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fyd_secret_key_2026_purple_agency_key'
    DATABASE = os.path.join(os.path.dirname(__file__), 'agencia_fyd.db')
    DEBUG = True