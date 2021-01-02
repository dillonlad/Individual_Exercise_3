import json
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
from app.blogs.forms import CommentForm, SubmitNewsletter, Newsletter
from app.main.routes import third_party_cookies, cookies_accept

from app.models import Posts_two, Blogs, Profile, Categories, Series, Authors, Comments_dg_tmp, \
    mailing_list, shop_items

bp_blogs = Blueprint('blogs', __name__, url_prefix='/blogs')
ADMINS = ['inwaitoftomorrow@gmail.com']
NEWSLETTER_TEST = ['dlad82434@gmail.com']


def structured_data(item_on_page, average_rating, review_count, reviews):

    for var in item_on_page:
        item_name = var.Title
        item_no = var.article_id
        item_image = "https://inwaitoftomorrow.appspot.com{}".format(var.Image_iphone)
        item_desc = var.Description
        item_date = var.Date
        item_category = var.category
        item_url = var.url_
        item_author = var.author
        item_body = var.Content
        item_date_mod = var.date_mod

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

    return html_insert


def form_send(form, Post_ID):

    form_name = form.name.data
    form_email = form.email.data
    form_comment = form.comment.data
    form_post_on_page = form.post_on_page.data
    form_newsletter = form.newsletter.data
    form_rating = form.rating.data

    with app.mail.connect() as conn:
        time_date = datetime.now()
        msg = Message('{} - comment'.format(form_name), sender=ADMINS[0], recipients=ADMINS)
        msg.body = '{}'.format(form_comment)
        user_email = form_email
        if user_email == "":
            user_email = "not provided"
        msg.html = '<b>{}</b> says {} about {} at this time {}:{}:{} on this date {}-{}-{}. User said {} to posting on the page and {} to newsletter, with the email {}. An overall rating of {}'.format(
            form_name, form_comment, Post_ID, time_date.strftime("%H"), time_date.strftime("%M"),
            time_date.strftime("%S"), time_date.strftime("%Y"), time_date.strftime("%m"),
            time_date.strftime("%d"),
            form_post_on_page, form_newsletter, user_email, form_rating)
        conn.send(msg)

    flash('Thanks for the reply!')


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
            latest_product = shop_items.query.limit(1).all()
            for variable in latest_product:
                product_image = variable.meta_image.replace("http://inwaitoftomorrow.appspot.com", "..")
            navigation_page = render_template('navigation.html', categories=categories)
            post = Blogs.query.filter_by(Post_ID=Post_ID).all()
            for var in post:
                p_author = var.author
                p_date = var.Date
            post_author = Authors.query.filter(Authors.author_name.contains(p_author)).all()
            for var_new in post_author:
                post_authorid = var_new.author_id
            date_object = datetime.strptime(p_date, '%Y-%m-%d')
            new_date = date_object.strftime("%d %b %Y")
            quiz_of_the_week = render_template('blogs/quiz.html')
            latest_articles = Blogs.query.order_by(desc(Blogs.article_id)).filter(Blogs.Post_ID!=Post_ID).limit(5).all()
            cookies_accept()
            allow_third_party_cookies = third_party_cookies()
            if len(post) == 0:
                return redirect(url_for('main.show_blog'))
            comments = Comments_dg_tmp.query.order_by(desc(Comments_dg_tmp.comment_id)).filter(Comments_dg_tmp.blog_name.contains(Post_ID)).all()
            number_of_comments = len(comments)
            if number_of_comments > 0 :
                total_rating = 0
                for i in comments:
                    total_rating += int(i.stars)
                aggregate_rating = total_rating/number_of_comments
            else:
                aggregate_rating = 0
            structured_info = structured_data(post, aggregate_rating, number_of_comments, comments)
            app.track_event(category="Blog read: {}".format(Post_ID), action='{}'.format(Post_ID))
            form = CommentForm(request.form)
            if request.method == 'POST' and form.validate():
                form_send(form, Post_ID)
                return redirect(url_for('blogs.post', Post_ID=Post_ID), code=303)
            else:
                if form.is_submitted():
                    form.method ='POST'
                    if (len(form.name.data) > 0 and len(form.comment.data) > 0) or (len(form.name.data) > 0 and len(form.email.data) > 0):
                        form_send(form, Post_ID)
                        return redirect(url_for('blogs.post', Post_ID=Post_ID), code=303)
                    else:
                        flash('Thanks for the reply')
                        return redirect(url_for('blogs.post', Post_ID=Post_ID), code=302)
                else:
                    return render_template("blogs/post.html", post=post, categories=categories, comments=comments, number_of_comments=number_of_comments, latest_articles=latest_articles, quiz_of_the_week=quiz_of_the_week, form=form, post_authorid=post_authorid, new_date=new_date, navigation_page=navigation_page, structured_info=structured_info, latest_product=latest_product, product_image=product_image, allow_third_party_cookies=allow_third_party_cookies)
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


@bp_blogs.errorhandler(404)
def pnf_404(error):
    return render_template("404.html"), 404


@bp_blogs.errorhandler(500)
def pnf_500(error):
    return render_template("500.html"), 500