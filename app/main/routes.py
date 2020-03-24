from flask import render_template, Blueprint, request, flash, redirect, url_for, Flask
from sqlalchemy import null, desc
from sqlalchemy.exc import IntegrityError, OperationalError
from flask_sqlalchemy import SQLAlchemy
from os.path import abspath, join, dirname
from flask_sitemap import Sitemap



import app
from app import db
from app.main.forms import CommentForm

from app.models import Comments, Posts_two

bp_main = Blueprint('main', __name__)
bp_blogs = Blueprint('blogs', __name__, url_prefix='/blogs')
ext = Sitemap()


@bp_main.route('/', methods=['GET'])
def index():
    posts = Posts_two.query.order_by(desc(Posts_two.article_id)).all()
    return render_template('homepage.html', posts=posts)


@bp_main.route('/blog_results', methods=['GET'])
def show_blog():
    posts = Posts_two.query.order_by(desc(Posts_two.article_id)).all()
    return render_template("blog_results.html", posts=posts)


@bp_blogs.route('/Biotech', methods=['POST', 'GET'])
def biotech_blog():
    form = CommentForm(request.form)
    all_comments = Comments.query.filter(Comments.blog_name.contains("Biotech")).all()
    if request.method == 'POST' and form.validate():
        user_comment = Comments(name=form.name.data, comment=form.comment.data, blog_name="Biotech", date=form.date.data)
        try:
            db.session.add(user_comment)
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


@bp_blogs.route('/COVID19', methods=['POST', 'GET'])
def Covid_blog():
    form = CommentForm(request.form)
    all_comments = Comments.query.filter(Comments.blog_name.contains("COVID19")).all()
    if request.method == 'POST' and form.validate():
        user_comment = Comments(name=form.name.data, comment=form.comment.data, blog_name="Biotech", date=form.date.data)
        try:
            db.session.add(user_comment)
            db.session.commit()
            flash('Thanks for the comment!')
            return redirect(url_for('blogs.Covid_blog'))
        except IntegrityError:
            db.session.rollback()
            flash('ERROR commenting')
        except OperationalError:
            db.session.rollback()
            flash('There was an error when commenting! Thanks for trying!')
            return redirect(url_for('main.biotech_blog'))
    return render_template("blogs/COVID19.html", form=form, comments=all_comments)


@bp_blogs.route('/AI_in_COVID19', methods=['POST', 'GET'])
def AI_Covid_blog():
    form = CommentForm(request.form)
    all_comments = Comments.query.filter(Comments.blog_name.contains("AI_in_COVID19")).all()
    if request.method == 'POST' and form.validate():
        user_comment = Comments(name=form.name.data, comment=form.comment.data, blog_name="Biotech", date=form.date.data)
        try:
            db.session.add(user_comment)
            db.session.commit()
            flash('Thanks for the comment!')
            return redirect(url_for('blogs.AI_Covid_blog'))
        except IntegrityError:
            db.session.rollback()
            flash('ERROR commenting')
        except OperationalError:
            db.session.rollback()
            flash('There was an error when commenting! Thanks for trying!')
            return redirect(url_for('main.biotech_blog'))
    return render_template("blogs/AI_for_COVID.html", form=form, comments=all_comments)

@bp_blogs.route('/Deepfakes', methods=['POST', 'GET'])
def Deepfakes():
    form = CommentForm(request.form)
    all_comments = Comments.query.filter(Comments.blog_name.contains("Deepfakes")).all()
    if request.method == 'POST' and form.validate():
        user_comment = Comments(name=form.name.data, comment=form.comment.data, blog_name="Biotech", date=form.date.data)
        try:
            db.session.add(user_comment)
            db.session.commit()
            flash('Thanks for the comment!')
            return redirect(url_for('blogs.Deepfakes'))
        except IntegrityError:
            db.session.rollback()
            flash('ERROR commenting')
        except OperationalError:
            db.session.rollback()
            flash('There was an error when commenting! Thanks for trying!')
            return redirect(url_for('main.biotech_blog'))
    return render_template("blogs/Deepfakes.html", form=form, comments=all_comments)

@bp_main.errorhandler(500)
def page_not_found(e):
    return render_template("500.html"), 500