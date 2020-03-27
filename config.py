"""App configuration."""
from os import environ
import redis


class Config:
    """Set Flask configuration vars from .env file."""

    # General Config
    SECRET_KEY = 'r985l9ArEaKg&esQ&R3!Dm2@Q$hOVV7&$gHpwU' # environ.get('SECRET_KEY')
    FLASK_APP = 'app.py'
    FLASK_ENV = 'development'# environ.get('FLASK_APP')
    # FLASK_ENV = # environ.get('FLASK_ENV')

    # Flask-Session
    SESSION_TYPE = 'redis' # environ.get('SESSION_TYPE')
    SESSION_REDIS = redis.from_url('redis://:gGbAkJYrvH3MVEIMtdP57LgntVXSm0OC@redis-11200.c228.us-central1-1.gce.cloud.redislabs.com:11200') # environ.get('SESSION_REDIS')