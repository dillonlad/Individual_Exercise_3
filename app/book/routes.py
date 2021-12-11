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
from app.LoadingModule import load_templates


bp_book = Blueprint('book', __name__, url_prefix='/book')

@bp_book.route('/book', methods=['GET', 'POST'])
def read_book():
    categories, navigation_page, allow_third_party_cookies, footer = load_templates()
    return render_template('books/book.html', categories=categories, navigation_page=navigation_page,
                            allow_third_party_cookies=allow_third_party_cookies, footer=footer)
