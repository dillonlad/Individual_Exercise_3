from datetime import timedelta, datetime
from urllib.parse import urlparse, urljoin

from flask import render_template, Blueprint, request, flash, redirect, url_for, Flask, make_response, abort, \
    render_template_string, session, jsonify
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
from app.HelloAnalytics import initialize_analyticsreporting, print_response, get_report, get_report_most_popular
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


@bp_main.route('/sitemap-news.xml', methods=['GET'])
def news_sitemap():
    articles = Blogs.query.all()
    list_of_articles = []
    for article in articles:
        article_dict = {}
        article_url = article.url_
        if '_' in article_url:
            article_url = article_url.replace("_","-")
        if 'http://' in article_url:
            article_url = article_url.replace("http://","https://")

        article_dict['url'] = article_url
        article_dict['Date'] = article.Date
        article_dict['Title'] = article.Title
        article_dict['last_mod'] = article.date_mod
        list_of_articles.append(article_dict)
    return render_template('news_sitemap.xml', articles=list_of_articles)


@bp_main.route('/products-sitemap.xml', methods=['GET'])
def products_sitemap():
    products = shop_items.query.all()
    return render_template('sitemap_products.xml', products=products)


@bp_main.route('/e2signi7jnwn91lzisnqiix5uvmc3v.html', methods=['GET'])
def facebook_verify():
    return render_template('e2signi7jnwn91lzisnqiix5uvmc3v.html')


def cookies_accept():
    if 'cookies_accept' not in session:
        flash(render_template_string("<p>By using our website, you agree to our use of cookies. <a href='{{ url_for('main.privacy_policies') }}'>Click here to find out more and turn off cookies.</a></p>"))
        session['cookies_accept'] = "True"


def third_party_cookies():
    if 'third_party_cookies_none' in session:
        return "False"
    else:
        return "True"


@bp_main.route('/cookies/disallow', methods=['POST', 'GET'])
def no_cookies():
    session['third_party_cookies_none'] = "None"
    session['cookies_accept'] = "False"
    flash(render_template_string("<p>Third party cookies have successfully been blocked</p>"
                                 "<a class='border border-dark text-dark rounded-0 w-100 pt-1 pb-1 pl-5 pr-5' href='{{ url_for('main.privacy_policies') }}'>OK</a>"))
    return redirect(url_for('main.privacy_policies'))


@bp_main.route('/policy/privacy', methods=['POST', 'GET'])
def privacy_policies():
    allow_third_party_cookies = third_party_cookies()
    privacy_statement = render_template('privacy_statement.html')
    categories = Categories.query.all()
    navigation_page = render_template('navigation.html', categories=categories)
    return render_template('legal.html', allow_third_party_cookies=allow_third_party_cookies, privacy_statement=privacy_statement, categories=categories, navigation_page=navigation_page)


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
            posts = Blogs.query.order_by(desc(Blogs.article_id)).limit(6).all()
            latest_article = Blogs.query.order_by(desc(Blogs.article_id)).limit(1).all()
            navigation_page = render_template('navigation.html', categories=categories)
            cookies_accept()
            allow_third_party_cookies = third_party_cookies()
            footer = render_template('footer.html', categories=categories)
            if request.method == 'POST':
                search = form.Search.data
                return redirect(url_for('main.article_search', search_query=search))
            elif form.is_submitted():
                form.method = 'POST'
                search = form.Search.data
                return redirect(url_for('main.article_search', search_query=search))
            return render_template('homepage.html', allow_third_party_cookies=allow_third_party_cookies, latest_article=latest_article, posts=posts, form=form, categories=categories, series=series, homepage=homepage, navigation_page=navigation_page, footer=footer)


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
        cookies_accept()
        allow_third_party_cookies = third_party_cookies()
        return render_template('linkinbio.html', allow_third_party_cookies=allow_third_party_cookies, categories=categories, navigation_page=navigation_page)


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
        page = request.args.get('page', 1, type=int)
        posts = Blogs.query.order_by(desc(Blogs.article_id)).paginate(page, 6, False)
        navigation_page = render_template('navigation.html', categories=categories)
        cookies_accept()
        footer = render_template('footer.html', categories=categories)
        allow_third_party_cookies = third_party_cookies()
        next_url = url_for('main.show_blog_linkinbio', page=posts.next_num) \
            if posts.has_next else None
        prev_url = url_for('main.show_blog_linkinbio', page=posts.prev_num) \
            if posts.has_prev else None
        if request.method == 'POST':
            search = form.Search.data
            return redirect(url_for('main.article_search', search_query=search))
        elif form.is_submitted():
            form.method = 'POST'
            search = form.Search.data
            return redirect(url_for('main.article_search', search_query=search))
        return render_template("mobile/linkinbio_results.html", allow_third_party_cookies=allow_third_party_cookies, posts=posts.items, categories=categories, form=form,
                               next_url=next_url, prev_url=prev_url, navigation_page=navigation_page, footer=footer)


@bp_main.route('/articles', methods=['POST', 'GET'])
def show_blog():
    form = SearchForm(request.form)
    categories = Categories.query.all()
    posts = Blogs.query.order_by(desc(Blogs.article_id)).all()
    navigation_page = render_template('navigation.html', categories=categories)
    cookies_accept()
    allow_third_party_cookies = third_party_cookies()
    footer = render_template('footer.html', categories=categories)
    if request.method == 'POST':
        search = form.Search.data
        return redirect(url_for('main.article_search', search_query=search))
    elif form.is_submitted():
        form.method = 'POST'
        search = form.Search.data
        return redirect(url_for('main.article_search', search_query=search))
    return render_template("mobile/blog_results.html", allow_third_party_cookies=allow_third_party_cookies, posts=posts, categories=categories, form=form, navigation_page=navigation_page, footer=footer)


@bp_main.route('/<category>', methods=['POST', 'GET'])
def show_blog_category(category):
        form = SearchForm(request.form)
        categories = Categories.query.all()
        navigation_page = render_template('navigation.html', categories=categories)
        cookies_accept()
        allow_third_party_cookies = third_party_cookies()
        footer = render_template('footer.html', categories=categories)
        if Categories.query.filter(Categories.category_name.contains(category)).all():
            posts = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.category.contains(category)).all()
            if request.method == 'POST':
                search = form.Search.data
                return redirect(url_for('main.article_search', search_query=search))
            elif form.is_submitted():
                form.method = 'POST'
                search = form.Search.data
                return redirect(url_for('main.article_search', search_query=search))
            article_category = category
            return render_template("mobile/blog_results.html", allow_third_party_cookies=allow_third_party_cookies, posts=posts, categories=categories,
                                   article_category=article_category, form=form, navigation_page=navigation_page, footer=footer)


@bp_main.route('/search/<search_query>', methods=['POST', 'GET'])
def article_search(search_query):
    form = SearchForm(request.form)
    categories = Categories.query.all()
    navigation_page = render_template('navigation.html', categories=categories)
    posts = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.Title.contains(search_query)).all()
    posts_two = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.Content.contains(search_query)).all()
    allow_third_party_cookies = third_party_cookies()
    footer = render_template('footer.html', categories=categories)
    for post in posts_two:
        if post not in posts:
            posts.append(post)
    if request.method == 'POST':
        search = form.Search.data
        return redirect(url_for('main.article_search', search_query=search))
    elif form.is_submitted():
        form.method = 'POST'
        search = form.Search.data
        return redirect(url_for('main.article_search', search_query=search))
    return render_template("mobile/blog_results.html", allow_third_party_cookies = allow_third_party_cookies, posts=posts, categories=categories, form=form, article_category=search_query,
                       navigation_page=navigation_page, footer=footer)


@bp_main.route('/series/<series_key>', methods=['POST', 'GET'])
def show_blog_series(series_key):
    form = SearchForm(request.form)
    form.Search.data = series_key
    request.method = 'POST'
    categories = Categories.query.all()
    allow_third_party_cookies = third_party_cookies()
    navigation_page = render_template('navigation.html', categories=categories)
    posts = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.Title.contains(form.Search.data)).all()
    posts_two = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.Content.contains(form.Search.data)).all()
    for post in posts_two:
        if post not in posts:
            posts.append(post)
    return render_template("mobile/blog_results.html", allow_third_party_cookies=allow_third_party_cookies, posts=posts, categories=categories, form=form, navigation_page=navigation_page)



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
            post_url = "https://inwaitoftomorrow.appspot.com/blogs/" + form.Post_ID.data
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
            cookies_accept()
            allow_third_party_cookies = third_party_cookies()
            for geeza in person:
                person_name.append(geeza.author_name)
            posts = Blogs.query.filter(Blogs.author.contains(person_name[0])).order_by(desc(Blogs.article_id)).all()
            return render_template('author.html', allow_third_party_cookies=allow_third_party_cookies, categories=categories, person=person, posts=posts, navigation_page=navigation_page)


@bp_main.route('/api/most-popular', methods=['POST', 'GET'])
def get_most_popular():
    analytics = initialize_analyticsreporting()
    response = get_report_most_popular(analytics)
    analytics_reports = print_response(response)
    sorted_dict = sorted(analytics_reports, key=lambda k: k['views'], reverse=True)
    most_popular = []
    posts = Blogs.query.order_by(desc(Blogs.article_id)).all()
    for dict in sorted_dict:
        for post in posts:
            if post.Post_ID in dict['page']:
                if len(most_popular) < 5:
                    most_popular.append(post)
                else:
                    break

    return jsonify(status=render_template('most_popular.html', posts=most_popular, title="Most popular"))


@bp_main.route('/api/similar/<post_id>', methods=['POST', 'GET'])
def get_similar_blogs(post_id):

    post = Blogs.query.filter_by(Post_ID=post_id).all()
    category_list = []
    for match_post in post:
        category = match_post.category

        if ',' in category:
            category_list = category.split(', ')
        else:
            category_list = [category]
    print(category_list)
    posts = Blogs.query.order_by(desc(Blogs.article_id)).all()
    similar_posts = []

    for post in posts:
        if ',' in post.category:
            post_categories = post.category.split(', ')
        else:
            post_categories = [post.category]
        similarity_index = 0

        for category in post_categories:
            if category in category_list:
                similarity_index += 1

        if similarity_index > 0:
            similar_post = {}
            similar_post['index'] = similarity_index
            similar_post['post'] = post
            similar_posts.append(similar_post)

    sorted_dict = sorted(similar_posts, key=lambda k: k['index'], reverse=True)
    result = []
    for dict in sorted_dict:
        if (len(result) < 3) and (dict['post'].Post_ID != post_id):
            result.append(dict['post'])

    return jsonify(status=render_template('most_similar.html', posts=result, title="More like this"))


@bp_main.route('/admin/analytics', methods=['POST', 'GET'])
@login_required
def show_analytics():

    categories = Categories.query.all()
    navigation_page = render_template('navigation.html', categories=categories)

    analytics = initialize_analyticsreporting()
    response = get_report(analytics)
    analytics_reports = print_response(response)

    total_website_views = 0
    for web_report in analytics_reports:
        total_website_views += web_report['views']

    blog_views = []
    blog_titles = []

    posts = Blogs.query.order_by(desc(Blogs.article_id)).all()
    for post in posts:
        blog_titles.append(post.Title)
        total_views = 0
        for report in analytics_reports:
            if post.Post_ID in report['page']:
                total_views += report['views']
        blog_views.append(total_views)

    total = sum(blog_views)
    blog_list = []

    for i in range(len(blog_titles)):
        blog_dict = {'Blog_title': blog_titles[i], 'article_views': blog_views[i]}
        blog_list.append(blog_dict)

    product_names = []
    product_views = []

    products = shop_items.query.all()
    for product in products:
        product_names.append(product.item_name)
        total_views = 0
        for new_report in analytics_reports:
            if product.item_id in new_report['page']:
                total_views += new_report['views']
        product_views.append(total_views)

    product_list = []

    for i in range(len(product_names)):
        product_dict = {'product_name': product_names[i], 'product_views': product_views[i]}
        product_list.append(product_dict)

    return render_template('analytics.html', analytics_reports=analytics_reports, blog_views=blog_views, posts=posts, total=total, blog_list=blog_list, categories=categories, navigation_page=navigation_page, product_list=product_list, total_website_views=total_website_views)


@bp_main.errorhandler(404)
def pnf_404(error):
    return render_template("404.html"), 404


@bp_main.errorhandler(500)
def pnf_500(error):
    return render_template("500.html"), 500