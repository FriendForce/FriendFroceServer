import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'this-really-needs-to-be-changed'
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MIGRATION_DIR = os.path.join(basedir, 'migrations')
    FIREBASE_CREDENTIALS=os.path.join(basedir, 'friendforce-25851-firebase-adminsdk-z68w4-583b02825c.json')
    FIREBASE_DUMP=os.path.join(basedir, 'db.json')
    MAILGUN_DOMAIN_NAME="sandbox0999fe079ff549b2bddaaa6e2c81ec2a.mailgun.org"
    MAILGUN_API_KEY="key-180e3e48d159f0bc57fc104e291a2417"

class ProductionConfig(Config):
    DEBUG = False


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
