from flask import render_template, Blueprint, request, flash, redirect, url_for
from app.forms import SignupForm

bp_main = Blueprint('main', __name__)


@bp_main.route('/')
def index():
    return render_template('homepage.html')


@bp_main.route('/templates', methods=['POST', 'GET'])
def signup():
    form = SignupForm(request.form)
    if request.method == 'POST' and form.validate():
        flash('Signup requested for {}'.format(form.name.data))
        return redirect(url_for("templates.homepage"))
    return render_template('signup.html', form=form)