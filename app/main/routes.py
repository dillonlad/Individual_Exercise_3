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
from app.main.forms import CommentForm, SignupForm, LoginForm, PostForm, BlogEditor, CreateArticle, SearchForm, \
    SubmitNewsletter

from app.models import Posts_two, Blogs, Profile, Categories, Series, Authors, Comments_dg_tmp, \
    mailing_list

bp_main = Blueprint('main', __name__)
bp_blogs = Blueprint('blogs', __name__, url_prefix='/blogs')
ext = Sitemap()
ADMINS = ['inwaitoftomorrow@gmail.com']
NEWSLETTER_TEST = ['dlad82434@gmail.com']



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


def has_no_underscore():
    underscore = request.host
    if "_" in underscore:
        underscore.replace("_","-")


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


@bp_main.route('/robots.txt', methods=['GET'])
def robots_file():
    response = make_response(open('robots.txt').read())
    response.headers["Content-type"] = "text/plain"
    return response


@bp_main.route('/sitemap-index.xml')
def sitemap_index():
    return render_template('sitemap_index.xml')


@bp_main.route('/articles-sitemap.xml', methods=['GET'])
def articles_sitemap():
    categories = Categories.query.all()
    articles = Blogs.query.all()
    return render_template('sitemap_blogs.xml', categories=categories, articles=articles)


@bp_main.route('/', methods=['POST', 'GET'])
def index():
    host = request.host
    if "www" in host:
        return redirect('https://inwaitoftomorrow.appspot.com', code=301)
    elif "inwaitoftomorrow.com" in host:
        return redirect('https://inwaitoftomorrow.appspot.com', code=301)
    elif request.url.startswith('http://') and '127' not in host:
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)
    else:
        if current_user.is_authenticated:
            profile = Profile.query.filter(Profile.username==current_user.username).all()
            return render_template('landing.html', profile=profile)
        else:
            app.track_event(category='Homepage', action='Homepage visit')
            form = SearchForm(request.form)
            categories = Categories.query.all()
            series = Series.query.all()
            posts = Blogs.query.order_by(desc(Blogs.article_id)).limit(5).all()
            latest_article = Blogs.query.order_by(desc(Blogs.article_id)).limit(1).all()
            if request.method == 'POST' and form.validate():
                search = form.Search.data
                if len(search) == 0:
                    posts = Blogs.query.order_by(desc(Blogs.article_id)).limit(5).all()
                else:
                    posts = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.Title.contains(search)).all()
                    posts_two = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.Content.contains(search)).all()
                    for post in posts_two:
                        if post not in posts:
                            posts.append(post)
                return render_template('homepage.html', posts=posts, form=form, categories=categories, series=series)
            return render_template('homepage.html', latest_article=latest_article, posts=posts, form=form, categories=categories, series=series)


@bp_main.route('/linkinbio', methods=['POST', 'GET'])
def show_blog_linkinbio():
    app.track_event(category="Instagram hit", action='Blog read')
    form = SearchForm(request.form)
    categories = Categories.query.all()
    page = request.args.get('page',1,type=int)
    posts = Blogs.query.order_by(desc(Blogs.article_id)).paginate(page,5,False)
    next_url = url_for('main.show_blog_linkinbio', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.show_blog_linkinbio', page=posts.prev_num) \
        if posts.has_prev else None
    if request.method == 'POST' and form.validate():
        search = form.Search.data
        if len(search) == 0:
            posts = Blogs.query.order_by(desc(Blogs.article_id)).all()
        else:
            posts = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.Title.contains(search)).all()
            posts_two = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.Content.contains(search)).all()
            for post in posts_two:
                if post not in posts:
                    posts.append(post)
        return render_template("mobile/blog_results.html", article_category=search, posts=posts, categories=categories, form=form)
    return render_template("mobile/blog_results.html", posts=posts.items, categories=categories, form=form, next_url=next_url, prev_url=prev_url)


@bp_main.route('/articles', methods=['POST', 'GET'])
def show_blog():
    form = SearchForm(request.form)
    categories = Categories.query.all()
    posts = Blogs.query.order_by(desc(Blogs.article_id)).all()
    if request.method == 'POST' and form.validate():
        search = form.Search.data
        if len(search) == 0:
            posts = Blogs.query.order_by(desc(Blogs.article_id)).all()
        else:
            posts = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.Title.contains(search)).all()
            posts_two = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.Content.contains(search)).all()
            for post in posts_two:
                if post not in posts:
                    posts.append(post)
        return render_template("mobile/blog_results.html", posts=posts, categories=categories, form=form)
    return render_template("mobile/blog_results.html", posts=posts, categories=categories, form=form)


@bp_main.route('/<category>', methods=['POST', 'GET'])
def show_blog_category(category):
        form = SearchForm(request.form)
        categories = Categories.query.all()
        if Categories.query.filter(Categories.category_name.contains(category)).all():
            posts = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.category.contains(category)).all()
            if request.method == 'POST' and form.validate():
                search = form.Search.data
                if len(search) == 0:
                    posts = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.category.contains(category)).all()
                else:
                    posts = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.category.contains(category)).filter(
                        Blogs.Title.contains(search)).all()
                    posts_two = Blogs.query.order_by(desc(Blogs.article_id)).filter(
                        Blogs.category.contains(category)).filter(Blogs.Content.contains(search)).all()
                    for post in posts_two:
                        if post not in posts:
                            posts.append(post)
                article_category = category
                return render_template("mobile/blog_results.html", posts=posts, categories=categories,
                                       article_category=article_category, form=form)
            article_category = category
            return render_template("mobile/blog_results.html", posts=posts, categories=categories,
                                   article_category=article_category, form=form)
        return redirect(url_for('main.show_blog'))


@bp_main.route('/<series_key>', methods=['POST', 'GET'])
def show_blog_series(series_key):
    form = SearchForm(request.form)
    categories = Categories.query.all()
    episode = Series.query.filter(Series.series_key.contains(series_key)).all().split()
    if request.method == 'POST' and form.validate():
        search = form.Search.data
        posts = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.series.contains(episode.series_name)).filter(Blogs.Title.contains(search)).all()
        posts_two = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.series.contains(episode.series_name)).filter(Blogs.Content.contains(search)).all()
        for post in posts_two:
            if post not in posts:
                posts.append(post)
    else:
        posts = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.series.contains(episode.series_name)).all()
    article_category = episode.series_name
    return render_template("mobile/blog_results.html", posts=posts, categories=categories, article_category=article_category, form=form)



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
        return redirect(url_for('main.index'), code=303)
    else:
        if form.is_submitted():
            form.method = 'POST'
            if len(form.email.data) > 0 and len(form.password.data) > 0:
                user = Profile.query.filter_by(email=form.email.data).first()
                if user is None or not user.check_password(form.password.data):
                    flash('Invalid email/password combination', 'error')
                    return redirect(url_for('main.login'))
                login_user(user, duration=timedelta(minutes=1))
                next = request.args.get('next')
                if not is_safe_url(next):
                    return abort(400)
                profiles = Profile.query.filter(Profile.username != current_user.username).all()
                return redirect(url_for('main.index'), code=303)
            else:
                return redirect(url_for('main.login'), code=302)
        else:
            return render_template('login.html', form=form)


@bp_main.route('/logout/')
@login_required
def logout():
    logout_user()
    flash('You have successfully logged off')
    return redirect(url_for('main.index'))


@bp_main.route('/register/', methods=['POST', 'GET'])
def register():
    host = request.host
    if '127' not in host:
        flash('This view is restricted')
        return redirect(url_for('main.index'))
    else:
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
    authors = Authors.query.all()
    time_date = datetime.now()
    if request.method == 'POST' and form.validate():
        post = Blogs(Title=form.Title.data, Post_ID=form.Post_ID.data, Description=form.Description.data, Image_root=form.Image_root.data, url_=form.url_.data, Content=form.Content.data, Time="{}:{}:{}".format(time_date.strftime("%H"), time_date.strftime("%M"), time_date.strftime("%S")), Date="{}-{}-{}".format(time_date.strftime("%Y"), time_date.strftime("%m"), time_date.strftime("%d")), category=form.category.data, author=form.author.data, keywords=form.keywords.data)
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
    return render_template("blogs/add_post.html", form=form, authors=authors)


@bp_main.errorhandler(500)
def page_not_found(e):
    return render_template("500.html"), 500


@bp_main.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@bp_blogs.route('/<Post_ID>', methods=['POST', 'GET'])
def post(Post_ID):
    host = request.host
    if "_" in Post_ID:
        return redirect(url_for('blogs.post', Post_ID=Post_ID.replace("_","-")), 301)
    elif request.url.startswith('http://') and '127' not in host:
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)
    else:
        if Blogs.query.filter(Blogs.Post_ID.contains(Post_ID)).all():
            categories = Categories.query.all()
            post = Blogs.query.filter_by(Post_ID=Post_ID).all()
            quiz_of_the_week = render_template('blogs/quiz.html')
            latest_articles = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.Post_ID!=Post_ID).limit(5).all()
            if len(post) == 0:
                return redirect(url_for('main.show_blog'))
            comments = Comments_dg_tmp.query.order_by(desc(Comments_dg_tmp.comment_id)).filter(Comments_dg_tmp.blog_name.contains(Post_ID)).all()
            number_of_comments = len(comments)
            app.track_event(category="Blog read: {}".format(Post_ID), action='{}'.format(Post_ID))
            form = CommentForm(request.form)
            if request.method == 'POST' and form.validate():
                with app.mail.connect() as conn:
                    time_date = datetime.now()
                    msg = Message('{} - comment'.format(form.name.data), sender=ADMINS[0], recipients=ADMINS)
                    msg.body = '{}'.format(form.comment.data)
                    user_email = form.email.data
                    if user_email == "":
                        user_email = "not provided"
                    msg.html = '<b>{}</b> says {} about {} at this time {}:{}:{} on this date {}-{}-{}. User said {} to posting on the page and {} to newsletter, with the email {}. An overall rating of {}'.format(
                        form.name.data, form.comment.data, Post_ID, time_date.strftime("%H"), time_date.strftime("%M"),
                        time_date.strftime("%S"), time_date.strftime("%Y"), time_date.strftime("%m"),
                        time_date.strftime("%d"),
                        form.post_on_page.data, form.newsletter.data, user_email, form.rating.data)
                    conn.send(msg)
                flash('Thanks for the reply!')
                return redirect(url_for('blogs.post', Post_ID=Post_ID), code=303)
            else:
                if form.is_submitted():
                    form.method ='POST'
                    if len(form.name.data) > 0 and len(form.comment.data) > 0:
                        with app.mail.connect() as conn:
                            time_date = datetime.now()
                            msg = Message('{} - comment'.format(form.name.data), sender=ADMINS[0], recipients=ADMINS)
                            msg.body = '{}'.format(form.comment.data)
                            user_email = form.email.data
                            if user_email == "":
                                user_email = "not provided"
                            msg.html = '<b>{}</b> says {} about {} at this time {}:{}:{} on this date {}-{}-{}. User said {} to posting on the page and {} to newsletter, with the email {}. User gave the rating {}'.format(
                                form.name.data, form.comment.data, Post_ID, time_date.strftime("%H"),
                                time_date.strftime("%M"),
                                time_date.strftime("%S"), time_date.strftime("%Y"), time_date.strftime("%m"),
                                time_date.strftime("%d"),
                                form.post_on_page.data, form.newsletter.data, user_email, form.rating.data)
                            conn.send(msg)
                        flash('Thanks for the reply!')
                        return redirect(url_for('blogs.post', Post_ID=Post_ID), code=303)
                    else:
                        flash('Thanks for the reply')
                        return redirect(url_for('blogs.post', Post_ID=Post_ID), code=302)
                else:
                    return render_template("blogs/post.html", post=post, categories=categories, comments=comments, number_of_comments=number_of_comments, latest_articles=latest_articles, quiz_of_the_week=quiz_of_the_week, form=form)
        else:
            flash("The article you tried to find does not exist, at least not with that URL, try using the search box to find what you're looking for")
            return redirect(url_for('main.show_blog'))


@bp_blogs.route('/email', methods=['GET', 'POST'])
@login_required
def send_newsletter():
    form = SubmitNewsletter(request.form)
    if request.method == 'POST':
        latest_post = Blogs.query.order_by(desc(Blogs.article_id)).limit(1).all()
        second_latest_post = Blogs.query.order_by(desc(Blogs.article_id)).offset(1).limit(1).all()
        opening_message = form.specific_message_one.data
        closing_message = form.specific_message_two.data
        for fella in mailing_list.query.order_by(desc(mailing_list.recipient_id)).all():
            recp = fella.email.split()
            msg = Message(sender=ADMINS[0], recipients=recp)
            msg.subject = "Latest | In Wait of Tomorrow"
            msg.html = render_template("email.html", latest_post=latest_post, fella=fella, second_latest_post=second_latest_post, opening_message=opening_message, closing_message=closing_message)
            app.mail.send(msg)
        flash('Your email has been sent, please logout by at https://inwaitoftomorrow.appspot.com/logout')
        return redirect(url_for('main.index'), code=303)
    else:
        if form.is_submitted():
            form.method = 'POST'
            if len(form.specific_message_one.data) > 0 and len(form.specific_message_two.data) > 0:
                latest_post = Blogs.query.order_by(desc(Blogs.article_id)).limit(1).all()
                second_latest_post = Blogs.query.order_by(desc(Blogs.article_id)).offset(1).limit(1).all()
                opening_message = form.specific_message_one.data
                closing_message = form.specific_message_two.data
                for fella in mailing_list.query.order_by(desc(mailing_list.recipient_id)).all():
                    recp = fella.email.split()
                    msg = Message(sender=ADMINS[0], recipients=recp)
                    msg.subject = "Latest | In Wait of Tomorrow"
                    msg.html = render_template("email.html", latest_post=latest_post, fella=fella,
                                               second_latest_post=second_latest_post, opening_message=opening_message,
                                               closing_message=closing_message)
                    app.mail.send(msg)
                flash('Your email has been sent, please logout by at https://inwaitoftomorrow.appspot.com/logout')
                return redirect(url_for('main.index'), code=303)
            else:
                return redirect(url_for('blogs.send_newsletter'), code=302)
        else:
            return render_template('submit_newsletter.html', form=form)


@bp_blogs.route('/test-email', methods=['GET', 'POST'])
@login_required
def test_send_newsletter():
    form = SubmitNewsletter(request.form)
    if request.method == 'POST':
        if form.authenticate.data != "theshowgoeson":
            flash("Incorrect admin password")
            return redirect(url_for('blogs.test_send_newsletter'))
        latest_post = Blogs.query.order_by(desc(Blogs.article_id)).limit(1).all()
        second_latest_post = Blogs.query.order_by(desc(Blogs.article_id)).offset(1).limit(1).all()
        opening_message = form.specific_message_one.data
        closing_message = form.specific_message_two.data
        for fella in NEWSLETTER_TEST:
            recp = fella.split()
            msg = Message(sender=ADMINS[0], recipients=recp)
            msg.subject = "Latest | In Wait of Tomorrow"
            msg.html = render_template("email.html", latest_post=latest_post, fella=fella, second_latest_post=second_latest_post, opening_message=opening_message, closing_message=closing_message)
            app.mail.send(msg)
        flash('Your email has been sent, please logout by at https://inwaitoftomorrow.appspot.com/logout')
        return redirect(url_for('main.index'), code=303)
    else:
        if form.is_submitted():
            form.method = 'POST'
            if len(form.specific_message_one.data) > 0 and len(form.specific_message_two.data) > 0:
                latest_post = Blogs.query.order_by(desc(Blogs.article_id)).limit(1).all()
                second_latest_post = Blogs.query.order_by(desc(Blogs.article_id)).offset(1).limit(1).all()
                opening_message = form.specific_message_one.data
                closing_message = form.specific_message_two.data
                for fella in NEWSLETTER_TEST:
                    recp = fella.split()
                    msg = Message(sender=ADMINS[0], recipients=recp)
                    msg.subject = "Latest | In Wait of Tomorrow"
                    msg.html = render_template("email.html", latest_post=latest_post, fella=fella,
                                               second_latest_post=second_latest_post, opening_message=opening_message,
                                               closing_message=closing_message)
                    app.mail.send(msg)
                flash('Your email has been sent')
                return redirect(url_for('main.index'), code=303)
            else:
                return redirect(url_for('blogs.test_send_newsletter'), code=302)
        else:
            return render_template('submit_newsletter.html', form=form)

