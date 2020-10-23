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

from app.models import Posts_two, Blogs, Profile, Categories, Series, Authors, Comments_dg_tmp, \
    mailing_list, shop_items

bp_main = Blueprint('main', __name__)
ext = Sitemap()


def pass_through():
    pass


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


@bp_main.route('/products-sitemap.xml', methods=['GET'])
def products_sitemap():
    products = shop_items.query.all()
    return render_template('sitemap_products.xml', products=products)


@bp_main.route('/e2signi7jnwn91lzisnqiix5uvmc3v.html', methods=['GET'])
def facebook_verify():
    return render_template('e2signi7jnwn91lzisnqiix5uvmc3v.html')


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
            homepage = "yes"
            categories = Categories.query.all()
            series = Series.query.all()
            posts = Blogs.query.order_by(desc(Blogs.article_id)).limit(5).all()
            latest_article = Blogs.query.order_by(desc(Blogs.article_id)).limit(1).all()
            navigation_page = render_template('navigation.html', categories=categories)
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
                return render_template('homepage.html', latest_article=latest_article, posts=posts, form=form, categories=categories, series=series, homepage=homepage, navigation_page=navigation_page)
            else:
                if form.is_submitted():
                    form.method = 'POST'
                    search = form.Search.data
                    if len(search) == 0:
                        posts = Blogs.query.order_by(desc(Blogs.article_id)).limit(5).all()
                    else:
                        posts = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.Title.contains(search)).all()
                        posts_two = Blogs.query.order_by(desc(Blogs.article_id)).filter(
                            Blogs.Content.contains(search)).all()
                        for post in posts_two:
                            if post not in posts:
                                posts.append(post)
                    return render_template('homepage.html', latest_article=latest_article, posts=posts, form=form,
                                           categories=categories, series=series, homepage=homepage, navigation_page=navigation_page)
            return render_template('homepage.html', latest_article=latest_article, posts=posts, form=form, categories=categories, series=series, homepage=homepage, navigation_page=navigation_page)


@bp_main.route('/linkinbio', methods=['GET'])
def linkinbio():
    host = request.host
    if request.url.startswith('http://') and '127' not in host:
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)
    else:
        categories = Categories.query.all()
        navigation_page = render_template('navigation.html', categories=categories)
        return render_template('linkinbio.html', categories=categories, navigation_page=navigation_page)


@bp_main.route('/linkinbio/articles', methods=['POST', 'GET'])
def show_blog_linkinbio():
    host = request.host
    if request.url.startswith('http://') and '127' not in host:
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)
    else:
        form = SearchForm(request.form)
        categories = Categories.query.all()
        page = request.args.get('page',1,type=int)
        posts = Blogs.query.order_by(desc(Blogs.article_id)).paginate(page,5,False)
        navigation_page = render_template('navigation.html', categories=categories)
        next_url = url_for('main.show_blog_linkinbio', page=posts.next_num) \
            if posts.has_next else None
        prev_url = url_for('main.show_blog_linkinbio', page=posts.prev_num) \
            if posts.has_prev else None
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
            return render_template("mobile/blog_results.html", article_category=search, posts=posts, categories=categories,
                                   form=form, navigation_page=navigation_page)
        else:
            if form.is_submitted():
                form.method = 'POST'
                search = form.Search.data
                if len(search) == 0:
                    posts = Blogs.query.order_by(desc(Blogs.article_id)).limit(5).all()
                else:
                    posts = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.Title.contains(search)).all()
                    posts_two = Blogs.query.order_by(desc(Blogs.article_id)).filter(
                        Blogs.Content.contains(search)).all()
                    for post in posts_two:
                        if post not in posts:
                            posts.append(post)
                return render_template("mobile/blog_results.html", article_category=search, posts=posts,
                                       categories=categories, form=form, navigation_page=navigation_page)
        return render_template("mobile/blog_results.html", posts=posts.items, categories=categories, form=form,
                               next_url=next_url, prev_url=prev_url, navigation_page=navigation_page)


@bp_main.route('/articles', methods=['POST', 'GET'])
def show_blog():
    form = SearchForm(request.form)
    categories = Categories.query.all()
    posts = Blogs.query.order_by(desc(Blogs.article_id)).all()
    navigation_page = render_template('navigation.html', categories=categories)
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
        return render_template("mobile/blog_results.html", posts=posts, categories=categories, form=form, navigation_page=navigation_page)
    else:
        if form.is_submitted():
            form.method = 'POST'
            search = form.Search.data
            if len(search) == 0:
                posts = Blogs.query.order_by(desc(Blogs.article_id)).limit(5).all()
            else:
                posts = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.Title.contains(search)).all()
                posts_two = Blogs.query.order_by(desc(Blogs.article_id)).filter(
                    Blogs.Content.contains(search)).all()
                for post in posts_two:
                    if post not in posts:
                        posts.append(post)
            return render_template("mobile/blog_results.html", posts=posts, categories=categories, form=form)
    return render_template("mobile/blog_results.html", posts=posts, categories=categories, form=form, navigation_page=navigation_page)


@bp_main.route('/<category>', methods=['POST', 'GET'])
def show_blog_category(category):
        form = SearchForm(request.form)
        categories = Categories.query.all()
        navigation_page = render_template('navigation.html', categories=categories)
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
                                       article_category=article_category, form=form, navigation_page=navigation_page)
            article_category = category
            return render_template("mobile/blog_results.html", posts=posts, categories=categories,
                                   article_category=article_category, form=form, navigation_page=navigation_page)


@bp_main.route('/<series_key>', methods=['POST', 'GET'])
def show_blog_series(series_key):
    form = SearchForm(request.form)
    form.Search.data = series_key
    request.method = 'POST'
    categories = Categories.query.all()
    navigation_page = render_template('navigation.html', categories=categories)
    posts = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.Title.contains(form.Search.data)).all()
    posts_two = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.Content.contains(form.Search.data)).all()
    for post in posts_two:
        if post not in posts:
            posts.append(post)
    return render_template("mobile/blog_results.html", posts=posts, categories=categories, form=form, navigation_page=navigation_page)



@bp_main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('You are logged in')
        return redirect(url_for('main.index'))
    form = LoginForm()
    homepage = "no"
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
            return render_template('login.html', form=form, homepage=homepage)


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
        homepage = "no"
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
        return render_template('register.html', form=form, homepage=homepage)


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
    host = request.host
    if '127' not in host:
        abort(404)
    else:
        form = CreateArticle(request.form)
        authors = Authors.query.all()
        time_date = datetime.now()
        if request.method == 'POST' and form.validate():
            post_url = "https://inwaitoftomorrow.appspot.com/" + form.Post_ID.data
            post_main_image_root = "/static/img/"+form.Image_root.data
            post_jpg_image = post_main_image_root.replace(".webp",".jpg")
            post = Blogs(Title=form.Title.data, Post_ID=form.Post_ID.data, Description=form.Description.data, Image_root=post_main_image_root, url_=post_url, Content=form.Content.data, Time="{}:{}:{}".format(time_date.strftime("%H"), time_date.strftime("%M"), time_date.strftime("%S")), Date="{}-{}-{}".format(time_date.strftime("%Y"), time_date.strftime("%m"), time_date.strftime("%d")), category=form.category.data, author=form.author.data, keywords=form.keywords.data, Image_iphone=post_jpg_image)
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


@bp_main.route('/author/<author_id>', methods=['POST','GET'])
def authors(author_id):
    host = request.host
    if request.url.startswith('http://') and '127' not in host:
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)
    else:
        if Authors.query.filter(Authors.author_id.contains(author_id)).all():
            categories = Categories.query.all()
            navigation_page = render_template('navigation.html', categories=categories)
            person_name = []
            person = Authors.query.filter_by(author_id=author_id).all()
            for geeza in person:
                person_name.append(geeza.author_name)
            posts = Blogs.query.filter(Blogs.author.contains(person_name[0])).order_by(desc(Blogs.article_id)).all()
            return render_template('author.html', categories=categories, person=person, posts=posts, navigation_page=navigation_page)


@bp_main.errorhandler(404)
def pnf_404(error):
    return render_template("404.html"), 404


@bp_main.errorhandler(500)
def pnf_500(error):
    return render_template("500.html"), 500