from flask import render_template, render_template_string, flash, session, request

from app.main.forms import SearchForm
from app.models import Categories


def cookies_accept():
    if 'cookies_accept' not in session:
        flash(render_template_string("<p class='m-auto'>By using our website, you agree to our use of cookies. <a href='{{ url_for('main.privacy_policies') }}'>Click here to find out more and turn off cookies.</a></p>"))
        session['cookies_accept'] = "True"


def third_party_cookies():
    if 'third_party_cookies_none' in session:
        return "False"
    else:
        return "True"


def load_templates():
    categories = Categories.query.all()
    search_form = SearchForm(request.form)
    navigation_page = render_template('navigation.html', categories=categories, search_form=search_form)
    cookies_accept()
    allow_third_party_cookies = third_party_cookies()
    footer = render_template('footer.html', categories=categories)
    return categories, navigation_page, allow_third_party_cookies, footer
