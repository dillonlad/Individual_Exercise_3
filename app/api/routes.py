from flask import Blueprint, render_template, jsonify
from sqlalchemy import desc

from app.HelloAnalytics import initialize_analyticsreporting, get_report_most_popular, print_response, \
    get_report_events, get_report_pageviews
from app.models import Blogs

abbreviations = [{"abbrev": "tech", "full": "technology"}, {"abbrev": "ai", "full": "artificial intelligence"}]

bp_api = Blueprint('api', __name__, url_prefix='/api')


@bp_api.route('/most-popular', methods=['POST', 'GET'])
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


@bp_api.route('/similar/<post_id>', methods=['POST', 'GET'])
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

    analytics = initialize_analyticsreporting()
    response = get_report_pageviews(analytics)
    analytics_reports = print_response(response)
    sorted_dict = sorted(analytics_reports, key=lambda k: k['views'], reverse=True)
    views = 0
    for dict in sorted_dict:
        if post_id in dict['page']:
            views = dict['views']
            break
    print(views)

    return jsonify(status=render_template('most_similar.html', posts=result, title="More like this"), views=views)

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

        if ',' in categories:
            post_categories = categories.split(', ')
        else:
            post_categories = [categories]

        if ',' in keywords:
            post_keywords = keywords.split(',')
        else:
            post_keywords = [keywords]

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

    while len(results) <= 5:
        for dict_ in sorted_dict:
            results.append(dict_['post'])
        break

    for result in results:
        print(result.Title)
    return jsonify(status="hi")
