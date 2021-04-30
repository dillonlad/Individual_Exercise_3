from flask import Blueprint, render_template, jsonify
from sqlalchemy import desc

from app.HelloAnalytics import initialize_analyticsreporting, get_report_most_popular, print_response, get_report_events
from app.models import Blogs

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
    response = get_report_events(analytics, post_id)
    analytics_reports = print_response(response)
    sorted_dict = sorted(analytics_reports, key=lambda k: k['views'], reverse=True)
    views = 0
    for dict in sorted_dict:
        if post_id in dict['page']:
            views = dict['views']
            break
    print(views)

    return jsonify(status=render_template('most_similar.html', posts=result, title="More like this"), views=views)
