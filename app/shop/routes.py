from datetime import timedelta, datetime
from urllib.parse import urlparse, urljoin

from flask import render_template, Blueprint, request, flash, redirect, url_for, Flask, make_response, abort, \
    render_template_string
from flask_login import login_required, current_user, logout_user, login_user
from flask_mail import Mail, Message
from flask_mobility import Mobility
from flask_mobility.decorators import mobile_template, mobilized
from sqlalchemy import null, desc
from sqlalchemy.exc import IntegrityError, OperationalError
from flask_sqlalchemy import SQLAlchemy
from os.path import abspath, join, dirname
from flask_sitemap import Sitemap, sitemap_page_needed


import app
from app import db
from app.main.forms import SignupForm, LoginForm, PostForm, BlogEditor, CreateArticle, SearchForm
from app.main.routes import bp_main

from app.models import Posts_two, Blogs, Profile, Categories, Series, Authors, Comments_dg_tmp, \
    mailing_list


bp_shop = Blueprint('shop', __name__, subdomain="shop")


@bp_shop.route('/', methods=['GET'])
def shop():
    return render_template_string("<h1>Shop coming very soon!</h1> Return <a href='{{ url_for('main.index') }}'>home</a>")


@bp_shop.errorhandler(404)
def pnf_404(error):
    return render_template("404.html"), 404


@bp_shop.errorhandler(500)
def pnf_500(error):
    return render_template("500.html"), 500