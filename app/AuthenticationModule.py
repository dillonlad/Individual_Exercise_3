from functools import wraps

from flask import flash, url_for, redirect, session
from flask_login import current_user, logout_user

from app.models import Profile


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