import json
from datetime import timedelta, datetime
from urllib.parse import urlparse, urljoin
from smtplib import SMTPAuthenticationError
from flask import render_template, Blueprint, request, flash, redirect, url_for, Flask, make_response, abort, \
    render_template_string, jsonify
from flask_login import login_required, current_user, logout_user, login_user
from flask_mail import Mail, Message
from flask_mobility import Mobility
from flask_mobility.decorators import mobile_template, mobilized
from sqlalchemy import null, desc
from sqlalchemy.exc import IntegrityError, OperationalError
from flask_sqlalchemy import SQLAlchemy
from os.path import abspath, join, dirname
from flask_sitemap import Sitemap, sitemap_page_needed
import requests
from requests.auth import HTTPBasicAuth
import app
from app import db
from app.AuthenticationModule import is_admin, otp_required, url_blogs, url_https, apiAuth
from app.HelloAnalytics import initialize_analyticsreporting, print_response, get_report_most_popular
from app.LoadingModule import load_templates
from app.blogs.forms import CommentForm, SubmitNewsletter, Newsletter
from app.main.forms import SearchForm
from app.main.routes import third_party_cookies, cookies_accept, bp_main

from app.models import Posts_two, Blogs, Profile, Categories, Series, Authors, Comments_dg_tmp, \
    mailing_list, shop_items

from collections import OrderedDict

bp_blogs = Blueprint('blogs', __name__, url_prefix='/blogs')
ADMINS = ['inwaitoftomorrow@gmail.com']
NEWSLETTER_TEST = [OrderedDict({"recipient_id": 6, "name": "Dillon", "email": "dlad82434@gmail.com"}),
                   OrderedDict({"recipient_id": 16, "name": "Dillon", "email": "dillonlad@live.co.uk"})]


def structured_data(item_on_page, reviews):
    item_name = item_on_page[0].Title
    item_no = item_on_page[0].article_id
    item_image = "https://inwaitoftomorrow.appspot.com{}".format(item_on_page[0].Image_iphone)
    item_desc = item_on_page[0].Description
    item_date = item_on_page[0].Date
    item_category = item_on_page[0].category
    item_url = item_on_page[0].url_
    item_author = item_on_page[0].author
    item_body = item_on_page[0].Content
    item_date_mod = item_on_page[0].date_mod

    review_count = len(reviews)
    average_rating = 0
    if review_count > 0:
        total_rating = 0
        for i in reviews:
            total_rating += int(i.stars)
        average_rating = total_rating / review_count

    aggregate_rating = {
        "@type": "AggregateRating",
        "ratingValue": "{}".format(average_rating),
        "ratingCount": "{}".format(review_count)
    }

    if len(reviews) > 0:
        structured_data_dict = {
            "@context": "https://schema.org",
            "@type": "Article",
            "description": "{}".format(item_desc),
            "name": "{}".format(item_name),
            "headline": "{}".format(item_name),
            "publisher": "In Wait of Tomorrow",
            "datePublished": "{}".format(item_date),
            "dateModified": "{}".format(item_date_mod),
            "image": "{}".format(item_image),
            "articleSection": "{}".format(item_category),
            "url": "{}".format(item_url),
            "articleBody": "{}".format(item_body),
            "author": {
                "@type": "Person",
                "name": "{}".format(item_author)
            }
        }
    else:
        structured_data_dict = {
            "@context": "https://schema.org",
            "@type": "Article",
            "description": "{}".format(item_desc),
            "name": "{}".format(item_name),
            "headline": "{}".format(item_name),
            "publisher": "In Wait of Tomorrow",
            "datePublished": "{}".format(item_date),
            "dateModified": "{}".format(item_date_mod),
            "image": "{}".format(item_image),
            "articleSection": "{}".format(item_category),
            "url": "{}".format(item_url),
            "articleBody": "{}".format(item_body),
            "author": {
                "@type": "Person",
                "name": "{}".format(item_author)
            }
        }

    json_structured_data = json.dumps(structured_data_dict)
    html_insert = render_template_string('<script type="application/ld+json">{}</script>'.format(json_structured_data))

    return html_insert, review_count


def form_send(form, Post_ID):
    name = form.name.data
    comment = form.comment.data
    rating = form.rating.data
    post_title = Post_ID

    with app.mail.connect() as conn:
        time_date = datetime.now()
        msg = Message('{} - comment'.format(name), sender=ADMINS[0], recipients=ADMINS)
        msg.body = '{}'.format(comment)
        msg.html = '<b>{}</b> says {} about {} at this time {}:{}:{} on this date {}-{}-{}. An overall rating of {}'.format(
            name, comment, post_title, time_date.strftime("%H"), time_date.strftime("%M"),
            time_date.strftime("%S"), time_date.strftime("%Y"), time_date.strftime("%m"),
            time_date.strftime("%d"),
            rating)
        conn.send(msg)

    flash('Thanks for the reply!')


@bp_blogs.route('/signup/', methods=['POST', 'GET'])
def newsletter_signup():
    jsonBody = request.get_json()
    requests.post("https://lowdhampharmacy.pythonanywhere.com/sign-up", json=jsonBody, auth=apiAuth)
    try:
        with app.mail.connect() as conn:
            msg = Message('Newsletter sign up', sender=ADMINS[0], recipients=ADMINS)
            msg.body = 'You have a new newsletter sign up'
            conn.send(msg)
    except SMTPAuthenticationError:
        print("Failed to send email")
    return jsonify(status="Thanks for signing up!")


@bp_blogs.route('/comment/<name>/<rating>/<comment>/<post_title>', methods=['POST', 'GET'])
def blog_comment(name, rating, comment, post_title):
    with app.mail.connect() as conn:
        time_date = datetime.now()
        msg = Message('{} - comment'.format(name), sender=ADMINS[0], recipients=ADMINS)
        msg.body = '{}'.format(comment)
        msg.html = '<b>{}</b> says {} about {} at this time {}:{}:{} on this date {}-{}-{}'.format(
            name, comment, post_title, time_date.strftime("%H"), time_date.strftime("%M"),
            time_date.strftime("%S"), time_date.strftime("%Y"), time_date.strftime("%m"),
            time_date.strftime("%d"))
        conn.send(msg)

    return jsonify(status="Thanks for the comment")

@bp_blogs.route('/add-comment', methods=['POST', 'GET'])
def add_new_blog_comment():
    jsonBody = request.get_json()
    post = Blogs.query.filter_by(Title=jsonBody["postName"]).first()
    jsonBody["postName"] = post.Post_ID
    res = requests.post('https://lowdhampharmacy.pythonanywhere.com/add-comment', json=jsonBody, auth=apiAuth)
    print("response from server: {}".format(res.text))
    dictFromServer = res.json()
    if dictFromServer:
        try:
            with app.mail.connect() as conn:
                msg = Message('New comments', sender=ADMINS[0], recipients=ADMINS)
                msg.body = 'You have some unread comments to respond to'
                conn.send(msg)
        except SMTPAuthenticationError:
            print("Email failed to send")
    return jsonify(status="Thanks for the comment")

@bp_blogs.route('/<Post_ID>', methods=['POST', 'GET'])
@url_https
def post(Post_ID):

    if "_" in Post_ID:
        return redirect(url_for('blogs.post', Post_ID=Post_ID.replace("_", "-")), 301)

    post = Blogs.query.filter_by(Post_ID=Post_ID).all()
    if not post:
        return redirect(abort(404))
    categories, navigation_page, allow_third_party_cookies, footer = load_templates()
    latest_product = shop_items.query.limit(1).all()
    product_image = latest_product[0].meta_image.replace("http://inwaitoftomorrow.appspot.com", "..")
    p_author = post[0].author
    p_date = post[0].Date
    post_author = Authors.query.filter(Authors.author_name.contains(p_author)).all()
    post_authorid = post_author[0].author_id
    date_object = datetime.strptime(p_date, '%Y-%m-%d')
    new_date = date_object.strftime("%d %b %Y")
    latest_articles = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.Post_ID != Post_ID).limit(
        5).all()
    comments = Comments_dg_tmp.query.order_by(desc(Comments_dg_tmp.comment_id)).filter(
        Comments_dg_tmp.blog_name.contains(Post_ID)).all()

    structured_info, number_of_comments = structured_data(post, comments)
    app.track_event(category="Blog read: {}".format(Post_ID), action='{}'.format(Post_ID))
    form = CommentForm(request.form)
    newsletter_form = Newsletter(request.form)
    return render_template("blogs/post.html", post=post, categories=categories, comments=comments,
                           number_of_comments=number_of_comments, latest_articles=latest_articles,
                           form=form, post_authorid=post_authorid,
                           new_date=new_date, navigation_page=navigation_page,
                           structured_info=structured_info, latest_product=latest_product,
                           product_image=product_image,
                           allow_third_party_cookies=allow_third_party_cookies,
                           newsletter_form=newsletter_form, footer=footer)


@bp_blogs.route('/email', methods=['GET', 'POST'])
@login_required
@otp_required
@is_admin
def send_newsletter():
    form = SubmitNewsletter(request.form)
    latest_posts = Blogs.query.order_by(desc(Blogs.article_id)).all()
    latest_post = latest_posts[0]
    second_latest_post = latest_posts[1]
    third_latest_post = latest_posts[2]
    if request.method == 'POST':
        opening_message = render_template_string(form.specific_message_one.data)
        closing_message = render_template_string(form.specific_message_two.data)
        for fella in mailing_list.query.order_by(desc(mailing_list.recipient_id)).all():
            recp = fella.email.split()
            msg = Message(sender=ADMINS[0], recipients=recp)
            msg.subject = "Latest | In Wait of Tomorrow"
            msg.html = render_template("email.html", latest_post=latest_post, fella=fella,
                                       second_latest_post=second_latest_post, third_latest_post=third_latest_post,
                                       opening_message=opening_message, closing_message=closing_message)
            app.mail.send(msg)
        flash('Your email has been sent, please logout by at https://inwaitoftomorrow.appspot.com/logout')
        return redirect(url_for('main.index'), code=303)
    else:
        if form.is_submitted():
            form.method = 'POST'
            if len(form.specific_message_one.data) > 0 and len(form.specific_message_two.data) > 0:
                opening_message = render_template_string(form.specific_message_one.data)
                closing_message = render_template_string(form.specific_message_two.data)
                for fella in mailing_list.query.order_by(desc(mailing_list.recipient_id)).all():
                    recp = fella.email.split()
                    msg = Message(sender=ADMINS[0], recipients=recp)
                    msg.subject = "Latest | In Wait of Tomorrow"
                    msg.html = render_template("email.html", latest_post=latest_post, fella=fella,
                                               second_latest_post=second_latest_post,
                                               third_latest_post=third_latest_post,
                                               opening_message=opening_message, closing_message=closing_message)
                    app.mail.send(msg)
                flash('Your email has been sent, please logout by at https://inwaitoftomorrow.appspot.com/logout')
                return redirect(url_for('main.index'), code=303)
            else:
                return redirect(url_for('blogs.send_newsletter'), code=302)
        else:
            return render_template('submit_newsletter.html', form=form, latest_post=latest_post,
                                   second_latest_post=second_latest_post, third_latest_post=third_latest_post)


@bp_blogs.route('/test-email', methods=['GET', 'POST'])
@login_required
@otp_required
@is_admin
def test_send_newsletter():
    form = SubmitNewsletter(request.form)
    latest_posts = Blogs.query.order_by(desc(Blogs.article_id)).all()
    latest_post = latest_posts[0]
    second_latest_post = latest_posts[1]
    third_latest_post = latest_posts[2]
    if request.method == 'POST':
        if form.authenticate.data != "theshowgoeson":
            flash("Incorrect admin password")
            return redirect(url_for('blogs.test_send_newsletter'))
        opening_message = render_template_string(form.specific_message_one.data)
        closing_message = render_template_string(form.specific_message_two.data)
        for fella in NEWSLETTER_TEST:
            recp = fella['email'].split()
            msg = Message(sender=ADMINS[0], recipients=recp)
            msg.subject = "Latest | In Wait of Tomorrow"
            msg.html = render_template("email.html", latest_post=latest_post, fella=fella,
                                       second_latest_post=second_latest_post, third_latest_post=third_latest_post,
                                       opening_message=opening_message, closing_message=closing_message)
            app.mail.send(msg)
        flash('Your email has been sent, please logout by at https://inwaitoftomorrow.appspot.com/logout')
        return redirect(url_for('main.index'), code=303)
    else:
        if form.is_submitted():
            form.method = 'POST'
            if len(form.specific_message_one.data) > 0 and len(form.specific_message_two.data) > 0:
                opening_message = render_template_string(form.specific_message_one.data)
                closing_message = render_template_string(form.specific_message_two.data)
                for fella in NEWSLETTER_TEST:
                    recp = fella["email"].split()
                    msg = Message(sender=ADMINS[0], recipients=recp)
                    msg.subject = "Latest | In Wait of Tomorrow"
                    msg.html = render_template("email.html", latest_post=latest_post, fella=fella,
                                               second_latest_post=second_latest_post,
                                               third_latest_post=third_latest_post, opening_message=opening_message,
                                               closing_message=closing_message)
                    app.mail.send(msg)
                flash('Your email has been sent')
                return redirect(url_for('main.index'), code=303)
            else:
                return redirect(url_for('blogs.test_send_newsletter'), code=302)
        else:
            return render_template('submit_newsletter.html', form=form, latest_post=latest_post,
                                   second_latest_post=second_latest_post, third_latest_post=third_latest_post)


@bp_blogs.errorhandler(404)
def pnf_404(error):
    return render_template("404.html"), 404


@bp_blogs.errorhandler(500)
def pnf_500(error):
    return render_template("500.html"), 500
