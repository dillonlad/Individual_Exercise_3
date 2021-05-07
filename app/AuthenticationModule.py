from functools import wraps

from flask import flash, url_for, redirect, session, request
from flask_login import current_user, logout_user

from app.models import Profile, Categories


def is_admin(func):

    @wraps(func)
    def decorated_view(*args, **kwargs):

        if current_user.is_authenticated:
            profiles = Profile.query.filter(Profile.username==current_user.username).all()
            role = '*'
            for profile in profiles:
                role = profile.role

            if role == "Admin":
                return func(*args, **kwargs)
            else:
                flash("You are not an admin")
                return redirect(url_for('main.index'))

    return decorated_view



def otp_verified():
    session['otp'] = 'pass'


def otp_required(func):

    @wraps(func)
    def decorated_view(*args, **kwargs):
        print(session['otp'])
        if session['otp'] != 'pass':
            if current_user.is_authenticated:
                flash("Please check your email for the OTP code")
                return redirect(url_for('main.authenticate_user'))
        else:
            return func(*args, **kwargs)

    return decorated_view


def url_https(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):

        host = request.host
        print(host)
        if request.url.startswith('http://') and '127' not in host:
            url = request.url.replace('http://', 'https://', 1)
            code = 301
            return redirect(url, code=code)
        else:
            return func(*args, **kwargs)

    return decorated_view


def url_homepage(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        host = request.host
        if "www" in host:
            return redirect('https://inwaitoftomorrow.appspot.com', code=301)
        elif "inwaitoftomorrow.com" in host:
            return redirect('https://inwaitoftomorrow.appspot.com', code=301)
        else:
            return func(*args, **kwargs)

    return decorated_view


def url_blogs(Post_ID):

    if "_" in Post_ID:
        return redirect(url_for('blogs.post', Post_ID=Post_ID.replace("_", "-")), 301)