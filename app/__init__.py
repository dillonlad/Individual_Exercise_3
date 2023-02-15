import os
from os.path import abspath, join, dirname

import requests
from flask import Flask, render_template
from flask_login import LoginManager
from flask_mail import Mail
from flask_mobility import Mobility

from flask_sqlalchemy import SQLAlchemy
from flask_sitemap import Sitemap
from flask_blogging import BloggingEngine


login_manager = LoginManager()
db = SQLAlchemy()
blogging_engine = BloggingEngine()
mobility = Mobility()
mail = Mail()
mail_sender = "inwaitoftomorrow@outlook.com"
mail_id = "In Wait Of Tomorrow"


def page_not_found_500():
    return render_template("500.html"), 500


def page_not_found_404():
    return render_template("404.html"), 404


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = '73WquRv_HFBhIVTmd4ARHQ'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    CWD = dirname(abspath(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + join(CWD, 'new_tomorrow')
    db.init_app(app)
    login_manager.init_app(app)


    # The following is needed if you want to map classes to an existing database
    with app.app_context():
        db.Model.metadata.reflect(db.engine)
        db.metadata.clear()
    # If you don't have a database with records that you created in ex1 then you all need to create the database tables by uncommenting the following lines
    # from app.models import <add the names of your model classes here>
    # with app.app_context():
        # db.create_all()

    # Register Blueprints
    from app.main.routes import bp_main
    app.register_blueprint(bp_main)


    from app.blogs.routes import bp_blogs
    app.register_blueprint(bp_blogs)


    from app.shop.routes import bp_shop
    app.register_blueprint(bp_shop)


    from app.shoptest.routes import bp_shoptest
    app.register_blueprint(bp_shoptest)

    from app.api.routes import bp_api
    app.register_blueprint(bp_api)

    from app.sitemaps.routes import bp_sitemaps
    app.register_blueprint(bp_sitemaps)

    from app.book.routes import bp_book
    app.register_blueprint(bp_book)


    from app.main.routes import ext
    app.config['SITEMAP_MAX_URL_COUNT'] = 10000
    app.config['SITEMAP_INCLUDE_RULES_WITHOUT_PARAMS'] = True
    app.config['SITEMAP_URL_SCHEME'] = "https"
    ext.init_app(app)

    app.config["BLOGGING_PERMISSIONS"] = True
    app.config["BLOGGING_ALLOW_FILEUPLOAD"] = True
    app.config["FILEUPLOAD_IMG_FOLDER"] = "fileupload"
    app.config["FILEUPLOAD_PREFIX"] = "/fileupload"
    app.config["FILEUPLOAD_ALLOWED_EXTENSIONS"] = ["png", "jpg", "jpeg", "gif"]

    app.config["MAIL_SERVER"] = 'smtp.office365.com'
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USE_SSL"] = False
    app.config["MAIL_USERNAME"] = 'inwaitoftomorrow@outlook.com'
    app.config["MAIL_PASSWORD"] = 'Kaylan14'
    app.config["MAIL_DEBUG"] = True
    app.config["MAIL_SUPPRESS_SEND"] = False

    mobility.init_app(app)
    app.jinja_env.cache = {}
    mail.init_app(app)

    return app


try:
    GA_TRACKING_ID = os.environ['GA_TRACKING_ID']
except KeyError:
    GA_TRACKING_ID = 'UA-159574205-1'


def track_event(category, action, label=None, value=0):
    data = {
        'v': '1',  # API Version.
        'tid': GA_TRACKING_ID,  # Tracking ID / Property ID.
        # Anonymous Client Identifier. Ideally, this should be a UUID that
        # is associated with particular user, device, or browser instance.
        'cid': '555',
        't': 'event',  # Event hit type.
        'ec': category,  # Event category.
        'ea': action,  # Event action.
        'el': label,  # Event label.
        'ev': value,  # Event value, must be an integer
        'ua': 'Opera/9.80 (Windows NT 6.0) Presto/2.12.388 Version/12.14'
    }

    response = requests.post(
        'https://www.google-analytics.com/collect', data=data)

    # If the request fails, this will raise a RequestException. Depending
    # on your application's needs, this may be a non-error and can be caught
    # by the caller.
    response.raise_for_status()