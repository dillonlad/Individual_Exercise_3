import json
from flask import Blueprint, render_template, jsonify, request, abort, session
from sqlalchemy import desc
import app
from app.HelloAnalytics import initialize_analyticsreporting, get_report_most_popular, print_response, \
    get_report_events, get_report_pageviews
from app.blogs.routes import newsletter_signup
from app.main.forms import EmailToMeForm
from app.models import Blogs, main_stock_list
from flask_mail import Mail, Message

abbreviations = [{"abbrev": "tech", "full": "technology"}, {"abbrev": "ai", "full": "artificial intelligence"}]

ADMINS = ['inwaitoftomorrow@gmail.com']
bp_api = Blueprint('api', __name__, url_prefix='/api')


# Query Google Analytics API to get the most popular articles in the last 14 days
@bp_api.route('/most-popular', methods=['POST', 'GET'])
def get_most_popular():
    analytics = initialize_analyticsreporting()
    response = get_report_most_popular(analytics)
    analytics_reports = print_response(response)
    sorted_dict = sorted(analytics_reports, key=lambda k: k['views'], reverse=True)
    most_popular = []
    posts = Blogs.query.order_by(desc(Blogs.article_id)).all()
    for dict in sorted_dict:
        matching_post = [post for post in posts if post.Post_ID in dict['page']]
        if len(matching_post) > 0: most_popular.append(matching_post[0])
        # for post in posts:
        #     if post.Post_ID in dict['page']:
        #         if len(most_popular) < 5:
        #             most_popular.append(post)
        #         else:
        #             break

    return jsonify(status=render_template('most_popular.html', posts=[x for x in most_popular[0:5]], title="Most popular"))


# Get the most similar articles to the one currently open and also gets the number of views for current article
@bp_api.route('/similar/<post_id>', methods=['POST', 'GET'])
def get_similar_blogs(post_id):

    post = Blogs.query.filter_by(Post_ID=post_id).all()[0]

    category_list = []
    category_list = post.category.split(', ') if ',' in post.category else [post.category]
    # for match_post in post:
    #     category = match_post.category

    #     if ',' in category:
    #         category_list = category.split(', ')
    #     else:
    #         category_list = [category]

    print(category_list)
    posts = Blogs.query.order_by(desc(Blogs.article_id)).all()
    similar_posts = []

    for post in posts:
        post_categories = post.category.split(', ') if ',' in post.category else [post.category]
        # if ',' in post.category:
        #     post_categories = post.category.split(', ')
        # else:
        #     post_categories = [post.category]
        # similarity_index = 0
        similarity_index = len([category for category in post_categories if category in category_list])
        # for category in post_categories:
        #     if category in category_list:
        #         similarity_index += 1

        if similarity_index > 0:
            similar_post = {}
            similar_post['index'] = similarity_index
            similar_post['post'] = post
            similar_posts.append(similar_post)

    sorted_dict = sorted(similar_posts, key=lambda k: k['index'], reverse=True)
    #result = []
    result = [dict['post'] for dict in sorted_dict if dict['post'].Post_ID!=post_id]
    # for dict in sorted_dict:
    #     if (len(result) < 3) and (dict['post'].Post_ID != post_id):
    #         result.append(dict['post'])

    analytics = initialize_analyticsreporting()
    response = get_report_pageviews(analytics)
    analytics_reports = print_response(response)
    sorted_dict = sorted(analytics_reports, key=lambda k: k['views'], reverse=True)
    #views = 0
    views = next((dict['views'] for dict in sorted_dict if post_id in dict['page']),0)
    # for dict in sorted_dict:
    #     if post_id in dict['page']:
    #         views = dict['views']
    #         break
    print(views)

    return jsonify(status=render_template('most_similar.html', posts=[result[0], result[1], result[2]], 
                                            title="More like this"), views=views)


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
        # if ',' in categories:
        #     post_categories = categories.split(', ')
        # else:
        #     post_categories = [categories]

        # if ',' in keywords:
        #     post_keywords = keywords.split(', ')
        # else:
        #     post_keywords = [keywords]

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

    # while len(results) <= 10:
    #     for dict_ in sorted_dict:
    #         results.append(dict_['post'])
    #         posts_ids.append(dict_['post'].Post_ID)
    #     break
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

    msg = Message(sender=ADMINS[0], recipients=email_address.split())
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