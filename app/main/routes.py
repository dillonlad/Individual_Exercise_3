import io
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
from werkzeug.security import generate_password_hash, safe_str_cmp

import app
from app import db
from app.AuthenticationModule import otp_required, otp_verified, is_admin, url_https, url_homepage, local_only
from app.HelloAnalytics import initialize_analyticsreporting, print_response, get_report, get_report_most_popular
from app.LoadingModule import load_templates

from app.main.forms import SignupForm, LoginForm, PostForm, BlogEditor, CreateArticle, SearchForm, OTPForm, ImageUpload, \
    ContactForm

from app.models import Posts_two, Blogs, Profile, Categories, Series, Authors, Comments_dg_tmp, \
    mailing_list, shop_items
from PIL import Image

bp_main = Blueprint('main', __name__)
ext = Sitemap()
ADMINS = ['inwaitoftomorrow@gmail.com']
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'heic'}
FILE_UPLOAD_MIMETYPES = [
    {"Extension": ".docx", "Mimetype": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    {"Extension": ".doc", "Mimetype": "application/msword"},
    {"Extension": ".txt", "Mimetype": "text/plain"},
    {"Extension": ".pdf", "Mimetype": "application/pdf"}
]


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
@url_https
def privacy_policies():
    allow_third_party_cookies = third_party_cookies()
    privacy_statement = render_template('privacy_statement.html')
    categories = Categories.query.all()
    navigation_page = render_template('navigation.html', categories=categories)
    return render_template('legal.html', allow_third_party_cookies=allow_third_party_cookies, privacy_statement=privacy_statement, categories=categories, navigation_page=navigation_page)


@bp_main.route('/', methods=['POST', 'GET'])
@url_https
@url_homepage
def index():
    if current_user.is_authenticated:
        profile = Profile.query.filter(Profile.username==current_user.username).all()
        return render_template('landing.html', profile=profile)
    else:
        app.track_event(category='Homepage', action='Homepage visit')
        categories, navigation_page, allow_third_party_cookies, footer = load_templates()
        form = SearchForm(request.form)
        homepage = "yes"
        series = Series.query.all()
        posts = Blogs.query.order_by(desc(Blogs.article_id)).limit(6).all()
        latest_article = Blogs.query.order_by(desc(Blogs.article_id)).limit(1).all()
        if request.method == 'POST':
            search = form.Search.data
            return redirect(url_for('main.article_search', search_query=search))
        elif form.is_submitted():
            form.method = 'POST'
            search = form.Search.data
            return redirect(url_for('main.article_search', search_query=search))
        return render_template('homepage.html', allow_third_party_cookies=allow_third_party_cookies, latest_article=latest_article, posts=posts, form=form, categories=categories, series=series, homepage=homepage, navigation_page=navigation_page, footer=footer)


@bp_main.route('/linkinbio', methods=['GET'])
@url_https
def linkinbio():
    categories, navigation_page, allow_third_party_cookies, footer = load_templates()
    words = ["Technology", "Environment", "Science", "Film", "Healthcare", "AI", "FinTech", "BioTech", "Computing"]
    return render_template('linkinbio.html', allow_third_party_cookies=allow_third_party_cookies, categories=categories, navigation_page=navigation_page, words=words)


@bp_main.route('/linkinbio/articles', methods=['POST', 'GET'])
@url_https
def show_blog_linkinbio():
    form = SearchForm(request.form)
    categories, navigation_page, allow_third_party_cookies, footer = load_templates()
    page = request.args.get('page', 1, type=int)
    posts = Blogs.query.order_by(desc(Blogs.article_id)).paginate(page, 6, False)
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
@url_https
def show_blog():
    form = SearchForm(request.form)
    categories, navigation_page, allow_third_party_cookies, footer = load_templates()
    posts = Blogs.query.order_by(desc(Blogs.article_id)).all()
    if request.method == 'POST':
        search = form.Search.data
        return redirect(url_for('main.article_search', search_query=search))
    elif form.is_submitted():
        form.method = 'POST'
        search = form.Search.data
        return redirect(url_for('main.article_search', search_query=search))
    return render_template("mobile/blog_results.html", allow_third_party_cookies=allow_third_party_cookies, posts=posts, categories=categories, form=form, navigation_page=navigation_page, footer=footer)


@bp_main.route('/<category>', methods=['POST', 'GET'])
@url_https
def show_blog_category(category):
    form = SearchForm(request.form)
    categories, navigation_page, allow_third_party_cookies, footer = load_templates()
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
@url_https
def article_search(search_query):
    form = SearchForm(request.form)
    categories, navigation_page, allow_third_party_cookies, footer = load_templates()
    posts = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.Title.contains(search_query)).all()
    posts_two = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.Content.contains(search_query)).all()
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


@bp_main.route('/write-for-us', methods=['POST', 'GET'])
@url_https
def write_for_us():
    categories, navigation_page, allow_third_party_cookies, footer = load_templates()
    latest_articles = Blogs.query.order_by(desc(Blogs.article_id)).limit(5).all()
    form = ContactForm(request.form)
    if request.method == "POST":

        if not form.name.data or not form.email.data:
            flash("Please enter a valid name and email")
            return redirect(url_for('main.write_for_us'))

        if '@' not in form.email.data or '.' not in form.email.data:
            flash("Please enter a valid email address")
            return redirect(url_for('main.write_for_us'))

        uploaded_file = request.files.get('file')
        file_allowed = False
        if uploaded_file:
            file_allowed = any(file_type["Extension"] in uploaded_file.filename for file_type in FILE_UPLOAD_MIMETYPES)
            print(file_allowed)

            if not file_allowed:
                flash(render_template_string("""<p>File type not supported, please upload file in: </p> 
                    <ul><li>.docx</li> <li>.doc</li> <li>.pdf</li> <li>.txt</li></ul>"""))
                return redirect(url_for('main.write_for_us'))

        with app.mail.connect() as conn:

            msg = Message('Contact - Write For Us', sender=ADMINS[0], recipients=ADMINS)
            msg.html = """
                <p>Name: {}</p>
                <p>Email: {}</p>
                <p>Message: {}</p>
            """.format(form.name.data, form.email.data, form.message.data)
            if file_allowed:
                attachment_bytes = io.BytesIO(uploaded_file.read())
                attachment_buffer = attachment_bytes.getvalue()
                mime_type = next((file_type["Mimetype"] for file_type in FILE_UPLOAD_MIMETYPES if file_type["Extension"]
                                 in uploaded_file.filename), None)
                msg.attach(uploaded_file.filename, mime_type, attachment_buffer)
            conn.send(msg)

            flash(render_template_string("<p>Thanks for your message, we'll be in contact!</p>"))

            return redirect(url_for('main.write_for_us'))

    return render_template('writeforus.html', categories=categories, navigation_page=navigation_page,
                           allow_third_party_cookies=allow_third_party_cookies, footer=footer,
                           latest_articles=latest_articles, form=form)


@bp_main.route('/series/<series_key>', methods=['POST', 'GET'])
@url_https
def show_blog_series(series_key):
    form = SearchForm(request.form)
    form.Search.data = series_key
    request.method = 'POST'
    categories, navigation_page, allow_third_party_cookies, footer = load_templates()
    posts = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.Title.contains(form.Search.data)).all()
    posts_two = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.Content.contains(form.Search.data)).all()
    for post in posts_two:
        if post not in posts:
            posts.append(post)
    return render_template("mobile/blog_results.html", allow_third_party_cookies=allow_third_party_cookies, posts=posts, categories=categories, form=form, navigation_page=navigation_page)


@bp_main.route('/login', methods=['GET', 'POST'])
@url_https
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
        return redirect(url_for('main.generate_otp'), code=303)
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
                return redirect(url_for('main.generate_otp'), code=303)
            else:
                return redirect(url_for('main.generate_otp'), code=302)
        else:
            return render_template('login.html', form=form, homepage=homepage)


@bp_main.route('/otp-generate', methods=['GET', 'POST'])
@login_required
def generate_otp():
    ADMINS = ['inwaitoftomorrow@gmail.com']
    import random
    import string
    import hmac
    from hashlib import sha512

    if current_user.is_authenticated:
        profile = Profile.query.filter(Profile.username == current_user.username).all()
        letters = string.ascii_uppercase
        auth_code = ''.join(random.choice(letters) for i in range(6))
        print(auth_code)
        key = b'RZdUEoXajGZjbdwDxJun1w'
        session['auth_code'] = u'{0}|{1}'.format(auth_code, hmac.new(key, auth_code.encode('utf-8'), sha512).hexdigest())
        email = profile[0].email.split()
        msg = Message(sender=ADMINS[0], recipients=email)
        msg.subject = "OTP"
        msg.body = '{}'.format(auth_code)
        app.mail.send(msg)

        return redirect(url_for('main.authenticate_user'))


@bp_main.route('/authenticate-user', methods=['GET', 'POST'])
@login_required
def authenticate_user():
    form = OTPForm()

    if request.method == 'POST':
        cookie = session['auth_code']
        print(cookie)
        key = b'RZdUEoXajGZjbdwDxJun1w'
        import hmac
        from hashlib import sha512

        payload, digest = cookie.rsplit(u'|', 1)
        if hasattr(digest, 'decode'):
            digest = digest.decode('ascii')  # pragma: no cover
            print(digest)

        if safe_str_cmp(hmac.new(key, payload.encode('utf-8'), sha512).hexdigest(), digest):
            if form.otp_code.data == payload:
                print(payload)
                print(form.otp_code.data)
                otp_verified()
                return redirect(url_for('main.index'))
            else:
                flash("Incorrect OTP")
                return redirect(url_for('main.authenticate_user'))

    return render_template('otp.html', form=form, homepage="no")


@bp_main.route('/logout/')
@login_required
def logout():
    logout_user()
    session['otp'] = 'logged off'
    flash('You have successfully logged off')
    return redirect(url_for('main.index'))


@bp_main.route('/register/', methods=['POST', 'GET'])
@local_only
def register():
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
@otp_required
@is_admin
@local_only
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
@otp_required
@is_admin
@local_only
def new_post():
    form = CreateArticle(request.form)
    author_choices =[('0', '')]
    authors = Authors.query.all()
    for author in authors:
        author_choices.append((author.author_name, author.author_name))
    form.author.choices = author_choices
    time_date = datetime.now()
    if request.method == 'POST' and form.validate():

        image_filename = form.Image_root.data
        uploaded_file = request.files.get('file')

        validate_filename = uploaded_file.filename.split(".")
        img_extension = validate_filename[1]

        if not uploaded_file:
            return 'No file uploaded.', 400

        if img_extension not in ALLOWED_EXTENSIONS:
            flash('{} is an unsupported type of image. Please upload images of the following file types: {}'.format(
                uploaded_file.filename, ALLOWED_EXTENSIONS))
            return redirect(url_for('main.upload_image'), code=303)

        image = Image.open(uploaded_file)
        w, h = image.size
        aspect_ratio = w / h
        max_image_height = 600 / aspect_ratio
        image.thumbnail((600, max_image_height))

        jpeg_filetype = '/static/img/{}-small.jpg'.format(image_filename)
        webp_filetype = '/static/img/{}-small.webp'.format(image_filename)

        image.save('app' + jpeg_filetype)
        image.save('app' + webp_filetype)

        post_url = "https://inwaitoftomorrow.appspot.com/blogs/" + form.Post_ID.data
        post_main_image_root = webp_filetype
        post_jpg_image = jpeg_filetype
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


@bp_main.route('/upload-image/', methods=['POST', 'GET'])
@login_required
@otp_required
@is_admin
@local_only
def upload_image():
    form = ImageUpload(request.form)
    if request.method == "POST":
        image_filename = form.filename.data
        uploaded_file = request.files.get('file')

        validate_filename = uploaded_file.filename.split(".")
        img_extension = validate_filename[1]
        print(img_extension)

        if not uploaded_file:
            return 'No file uploaded.', 400

        if img_extension not in ALLOWED_EXTENSIONS:
            flash('{} is an unsupported type of image. Please upload images of the following file types: {}'.format(
                uploaded_file.filename, ALLOWED_EXTENSIONS))
            return redirect(url_for('main.upload_image'), code=303)

        image = Image.open(uploaded_file)
        w, h = image.size
        aspect_ratio = w/h
        max_image_height = 600/aspect_ratio
        image.thumbnail((600, max_image_height))
        image.save('app/static/img/{}-small.jpg'.format(image_filename))
        image.save('app/static/img/{}-small.webp'.format(image_filename))

        flash("Image successfully uploaded")
    return render_template("image_upload.html", form=form, homepage="no")


@bp_main.route('/author/<author_id>', methods=['POST','GET'])
@url_https
def authors(author_id):
    categories, navigation_page, allow_third_party_cookies, footer = load_templates()
    if Authors.query.filter(Authors.author_id.contains(author_id)).all():
        person = Authors.query.filter_by(author_id=author_id).all()[0]
        posts = Blogs.query.filter(Blogs.author.contains(person.author_name)).order_by(desc(Blogs.article_id)).all()
        return render_template('author.html', allow_third_party_cookies=allow_third_party_cookies,
                               categories=categories, person=person, posts=posts, navigation_page=navigation_page,
                               footer=footer)
    else:
        return abort(404)


@bp_main.route('/admin/analytics', methods=['POST', 'GET'])
@login_required
@otp_required
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