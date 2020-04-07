from datetime import timedelta
from urllib.parse import urlparse, urljoin

from flask import render_template, Blueprint, request, flash, redirect, url_for, Flask, make_response, abort, \
    render_template_string
from flask_login import login_required, current_user, logout_user, login_user
from sqlalchemy import null, desc
from sqlalchemy.exc import IntegrityError, OperationalError
from flask_sqlalchemy import SQLAlchemy
from os.path import abspath, join, dirname
from flask_sitemap import Sitemap
from flask_mysqldb import MySQL


import app
from app import db, mysql
from app.main.forms import CommentForm, SignupForm, LoginForm, PostForm, BlogEditor, CreateArticle, SearchForm

from app.models import Comments, Posts_two, Blogs, Profile, Categories

bp_main = Blueprint('main', __name__)
bp_blogs = Blueprint('blogs', __name__, url_prefix='/blogs')
ext = Sitemap()


def is_safe_url(target):
    host_url = urlparse(request.host_url)
    redirect_url = urlparse(urljoin(request.host_url, target))
    return redirect_url.scheme in ('http', 'https') and host_url.netloc == redirect_url.netloc

def get_safe_redirect():
    url = request.args.get('next')
    if url and is_safe_url(url):
        return url
    url = request.referrer
    if url and is_safe_url(url):
        return url
    return '/'


@app.login_manager.user_loader
def load_user(user_id):
    """Check if user is logged-in on every page load."""
    if user_id is not None:
        return Profile.query.get(user_id)
    return None


@app.login_manager.unauthorized_handler
def unauthorized():
    """Redirect unauthorized users to Login page."""
    flash('You must be logged in to view that page.')
    return redirect(url_for('main.login'))


@bp_main.route('/', methods=['POST', 'GET'])
def index():
    form = SearchForm(request.form)
    categories = Categories.query.all()
    if request.method == 'POST' and form.validate():
        search = form.Search.data
        posts = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.Title.contains(search)).all()
    else:
        posts = Blogs.query.order_by(desc(Blogs.article_id)).limit(5).all()
    return render_template('homepage.html', posts=posts, form=form, categories=categories)


@bp_main.route('/linkinbio', methods=['GET'])
def show_blog_linkinbio():
    categories = Categories.query.all()
    posts = Blogs.query.order_by(desc(Blogs.article_id)).all()
    return render_template("blog_results_linkinbio.html", posts=posts, categories=categories)


@bp_main.route('/articles', methods=['POST', 'GET'])
def show_blog():
    form = SearchForm(request.form)
    categories = Categories.query.all()
    if request.method == 'POST' and form.validate():
        search = form.Search.data
        posts = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.Title.contains(search)).all()
    else:
        posts = Blogs.query.order_by(desc(Blogs.article_id)).all()
    return render_template("blog_results.html", posts=posts, categories=categories, form=form)


@bp_main.route('/<category>', methods=['POST', 'GET'])
def show_blog_category(category):
    form = SearchForm(request.form)
    categories = Categories.query.all()
    if request.method == 'POST' and form.validate():
        search = form.Search.data
        posts = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.category.contains(category)).filter(Blogs.Title.contains(search)).all()
    else:
        posts = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.category.contains(category)).all()
    article_category = category
    return render_template("blog_results.html", posts=posts, categories=categories, article_category=article_category, form=form)


@bp_blogs.route('/Biotech', methods=['POST', 'GET'])
def biotech_blog():
    form = CommentForm(request.form)
    all_comments = Comments.query.filter(Comments.blog_name.contains("Biotech")).all()
    if request.method == 'POST' and form.validate():
        user_comment = Comments(name=form.name.data, comment=form.comment.data, blog_name="Biotech", date=form.date.data)
        try:
            cur = mysql.connection.cursor()
            db.session.commit()
            flash('Thanks for the comment!')
            return redirect(url_for('main.biotech_blog'))
        except IntegrityError:
            db.session.rollback()
            flash('ERROR commenting')
        except OperationalError:
            db.session.rollback()
            flash('There was an error when commenting! Thanks for trying!')
            return redirect(url_for('main.biotech_blog'))
    return render_template("blogs/Biotech.html", form=form, comments=all_comments)


@bp_main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('You are logged in')
        return redirect(url_for('main.index'))
    form = LoginForm()
    if request.method == 'POST' and form.validate():
        user = Profile.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email/password combination', 'error')
            return redirect(url_for('main.login'))
        login_user(user, duration=timedelta(minutes=1))
        next = request.args.get('next')
        if not is_safe_url(next):
            return abort(400)
        profiles = Profile.query.filter(Profile.username != current_user.username).all()
        flash('Welcome {}'.format(current_user.username))
        return redirect(next or url_for('main.index'))
    return render_template('login.html', form=form)


@bp_main.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@bp_main.route('/register/', methods=['POST', 'GET'])
def register():
    if current_user.is_authenticated:
        flash('You are logged in')
        return redirect(url_for('main.index'))
    form = SignupForm(request.form)
    if request.method == 'POST' and form.validate():
        user = Profile(username=form.username.data, email=form.email.data, password=form.password.data)
        user.set_password(form.password.data)
        try:
            db.session.add(user)
            response = make_response(redirect(url_for('main.index')))
            response.set_cookie("username", form.username.data)
            user = Profile.query.filter_by(email=form.email.data).first()
            login_user(user)
            db.session.commit()
            flash('registered successfully')
            return response
        except IntegrityError:
            db.session.rollback()
            flash('Unable to register {}. Please try again.'.format(form.username.data), 'error')
        except OperationalError:
            db.session.rollback()
            flash('Register feature not working')
    return render_template('register.html', form=form)


@bp_main.route('/add_post/', methods=['POST', 'GET'])
@login_required
def add_post():
    form = BlogEditor(request.form)
    if request.method == 'POST' and form.validate():
        post = Blogs(Title=form.title.data, Content=form.text.data)
        try:
            db.session.add(post)
            response = make_response(redirect('main.index'))
            db.session.commit()
            flash('Upload successful')
            return response
        except IntegrityError:
            db.session.rollback()
            flash('did not work')
        except OperationalError:
            db.session.rollback()
            flash("This is currently under construction and won't work")
    return render_template("blogs/editor.html", form=form)


@bp_main.route('/new_post/', methods=['POST', 'GET'])
@login_required
def new_post():
    form = CreateArticle(request.form)
    if request.method == 'POST' and form.validate():
        post = Blogs(Title=form.Title.data, Post_ID=form.Post_ID.data, Description=form.Description.data, Image_root=form.Image_root.data, url_=form.url_.data, Content=form.Content.data, Time=form.Time.data, Date=form.Date.data, category=form.category.data, author=form.author.data)
        try:
            db.session.add(post)
            response = make_response(redirect(url_for('main.index')))
            db.session.commit()
            return response
        except IntegrityError:
            db.session.rollback()
            flash('did not work')
        except OperationalError:
            db.session.rollback()
            flash('did not work')
    return render_template("blogs/add_post.html", form=form)


@bp_main.errorhandler(500)
def page_not_found(e):
    return render_template("500.html"), 500


@bp_blogs.route('/<Post_ID>', methods=['GET'])
def post(Post_ID):
    categories = Categories.query.all()
    post = Blogs.query.filter_by(Post_ID=Post_ID).all()
    return render_template("blogs/post.html", post=post, categories=categories)
