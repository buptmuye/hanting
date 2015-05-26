from flask import Flask
from flask.ext.bootstrap import Bootstrap
from flask.ext.mail import Mail
from flask.ext.moment import Moment
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.cache import Cache
from config import config
import os
import pylibmc as memcache
from flask_saestorage import SaeStorage

mc = memcache.Client()
mc.flush_all()
basedir = os.path.abspath(os.path.dirname(__file__))
formats = set(['jpg', 'jpeg', 'png'])

sae_storage = SaeStorage()
bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
cache = Cache(config={'CACHE_TYPE':'simple'})

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    app.config['SAE_BUCKET_NAME'] = 'hantingxian'
    #i limit the max size of upload files to 10MB.
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
    sae_storage.init_app(app)
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    app.config['SQLALCHEMY_POOL_RECYCLE'] = 5
    db.init_app(app)
    login_manager.init_app(app)
    cache.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    return app

