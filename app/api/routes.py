import json
import os
from flask import Blueprint, render_template, jsonify, request, abort, session
from sqlalchemy import desc
import app
from app.HelloAnalytics import initialize_analyticsreporting, get_report_most_popular, print_response, \
    get_report_events, get_report_pageviews
from app.blogs.routes import newsletter_signup
from app.main.forms import EmailToMeForm
from app.models import Blogs, main_stock_list
from flask_mail import Mail, Message
import requests
from app.AuthenticationModule import apiAuth
from app import mail_sender

abbreviations = [{"abbrev": "tech", "full": "technology"}, {"abbrev": "ai", "full": "artificial intelligence"}]

ADMINS = ['inwaitoftomorrow@gmail.com']
bp_api = Blueprint('api', __name__, url_prefix='/api')


# Query Google Analytics API to get the most popular articles in the last 14 days
@bp_api.route('/most-popular', methods=['POST', 'GET'])
def get_most_popular():
    #analytics = initialize_analyticsreporting()
    #response = get_report_most_popular(analytics)
    #analytics_reports = print_response(response)
    #sorted_dict = sorted(analytics_reports, key=lambda k: k['views'], reverse=True)
    #most_popular = []
    posts = Blogs.query.order_by(desc(Blogs.article_id)).all()

    return jsonify(status=render_template('most_popular.html', posts=posts[0:5], title="Most popular"))

@bp_api.route('/respond-comments/', methods=['POST', 'GET'])
def approve_comments():
    jsonBody = request.get_json()
    print(jsonBody)
    #res = requests.get("https://lowdhampharmacy.pythonanywhere.com/respond-comment", json=jsonBody, auth=apiAuth)
    return jsonify(status="Complete")

# Get the most similar articles to the one currently open and also gets the number of views for current article
@bp_api.route('/similar/<post_id>', methods=['POST', 'GET'])
def get_similar_blogs(post_id):
    import datetime
    jsonBody = {"postId": post_id}
    #res = requests.get("https://69uet54rv1.execute-api.eu-west-2.amazonaws.com/dev/view-comment", json=jsonBody, auth=apiAuth)
    #print(res.text)
    #requestResults = res.json()
    formattedComments = []
    #print(requestResults)  
    _comments = []

    for comment in _comments:
        print(comment)
        formattedComment = {}
        formattedComment["ID"] = comment[0]
        formattedComment["Name"] = comment[1]
        formattedComment["Comment"] = comment[2]
        formattedComment["Date"] = datetime.datetime.strptime(comment[3], '%a, %d %b %Y %H:%M:%S %Z').strftime('%d/%m/%y') if comment[3] else ""
        formattedComments.append(formattedComment)
    commentsHtml = render_template('comments.html', comments=formattedComments, forApproval=False)
    post = Blogs.query.filter_by(Post_ID=post_id).all()[0]

    category_list = []
    category_list = post.category.split(', ') if ',' in post.category else [post.category]

    print(category_list)
    posts = Blogs.query.order_by(desc(Blogs.article_id)).all()
    similar_posts = []

    for post in posts:
        post_categories = post.category.split(', ') if ',' in post.category else [post.category]
        similarity_index = len([category for category in post_categories if category in category_list])
        if similarity_index > 0:
            similar_post = {}
            similar_post['index'] = similarity_index
            similar_post['post'] = post
            similar_posts.append(similar_post)

    sorted_dict = sorted(similar_posts, key=lambda k: k['index'], reverse=True)
    result = [dict['post'] for dict in sorted_dict if dict['post'].Post_ID!=post_id]
    #analytics = initialize_analyticsreporting()
    #response = get_report_pageviews(analytics)
    #analytics_reports = print_response(response)
    #sorted_dict = sorted(analytics_reports, key=lambda k: k['views'], reverse=True)
    #views = next((dict['views'] for dict in sorted_dict if post_id in dict['page']),0)
    #print(views)
    return jsonify(status=render_template('most_similar.html', posts=[result[0], result[1], result[2]], 
                                            title="More like this"), views=100, commentsHtml=commentsHtml)


@bp_api.route('/prepare-reading/<search_terms>', methods=['GET', 'POST'])
def prepare_reading(search_terms):
    terms = search_terms.lower()
    search_list = terms.split(',')
    print(search_list)
    matching_posts = []
    posts = Blogs.query.order_by(desc(Blogs.article_id)).all()
    for post in posts:
        similar_post = {}
        similarity_index = 0
        categories = post.category.lower()
        keywords = post.keywords.lower()
        post_categories = categories.split(', ') if ',' in categories else [categories]
        post_keywords = keywords.split(', ') if ',' in keywords else [keywords]
        for term in search_list:

            if "-" in term:
                term = term.replace("-", " ")

            abbrev = next((dict_["abbrev"] for dict_ in abbreviations if dict_["full"] == term), None)
            full = next((dict_["full"] for dict_ in abbreviations if dict_["abbrev"] == term), None)

            if term in post_categories or (abbrev and abbrev in post_categories) or (full and full in post_categories):
                similarity_index += 1

            if term in post_keywords or (abbrev and abbrev in post_keywords) or (full and full in post_keywords):
                similarity_index += 1

            if term in post.Title.lower() or (abbrev and abbrev in post.Title.lower()) or (full and full in post.Title.lower()):
                similarity_index += 1

            if term in post.Description.lower() or (abbrev and abbrev in post.Description.lower()) or (full and full in post.Description.lower()):
                similarity_index += 1

        if similarity_index > 0:
            similar_post['index'] = similarity_index
            similar_post['post'] = post
            matching_posts.append(similar_post)

    sorted_dict = sorted(matching_posts, key=lambda k: k['index'], reverse=True)
    results = []
    posts_ids = []

    results = [dict_['post'] for dict_ in sorted_dict]
    posts_ids = [dict_['post'].Post_ID for dict_ in sorted_dict]

    form = EmailToMeForm(request.form)
    template = render_template('prepared_reading.html', posts=results, form=form)
    return jsonify(status=template, type=posts_ids)


@bp_api.route('/send-articles/', methods=['POST', 'GET'])
def send_articles():

    if not request.get_json():
        return abort(404)

    email_address = request.get_json()['emailAddress']
    article_ids = request.get_json()['articleIds'].split(",")

    if email_address == "" or '@' not in email_address or '.' not in email_address:
        return jsonify(status="Please enter a valid email address")

    if request.get_json()['signUp']:
        newsletter_signup(email_address)
    posts = []

    blogs = Blogs.query.all()

    for blog in blogs:
        if blog.Post_ID in article_ids:
            posts.append(blog)

    msg = Message(sender=mail_sender, recipients=email_address.split())
    msg.html = render_template('prepared_reading_to_email.html', posts=posts)
    msg.subject = "Here's what we found for you"
    app.mail.send(msg)
    return jsonify(status="Check your emails!")


@bp_api.route('/userinterests/', methods=['POST', 'GET'])
def api_get_user_interests():
    words = ["Technology", "Environment", "Science", "Film", "Healthcare", "AI", "FinTech", "BioTech", "Computing"]
    user_interests = render_template("user_interests.html", words=words)
    return jsonify(status=user_interests)

@bp_api.route('/shop/add-item-to-cart/')
def add_item_to_cart():

    item_details = request.get_json()

    if not item_details:
        return abort(404)

    item_session_details = ["size", "quantity", "colour", "item_number", "itemprice"]
    for detail in item_session_details:
        session[detail] = [] if detail not in session else session[detail]
        session[detail].append(item_details[detail])

@bp_api.route('/subscribe', methods=['POST', 'GET'])
def subscribe():
    #res = requests.post("https://lowdhampharmacy.pythonanywhere.com/subscribe", json=request.get_json(), auth=apiAuth)
    return jsonify(status="success")


@bp_api.route('/stock-check/', methods=['GET', 'POST'])
def get_stock_list():
    stock_list = [{"stock_id": item_stock.stock_id, "Size": item_stock.Size, "Colour": item_stock.Colour, "item_number": item_stock.item_number, "stock": item_stock.stock} for item_stock in main_stock_list.query.all()]
    return jsonify(status=stock_list)

@bp_api.errorhandler(404)
def pnf_404(error):
    return render_template("404.html"), 404


@bp_api.errorhandler(500)
def pnf_500(error):
    return render_template("500.html"), 500