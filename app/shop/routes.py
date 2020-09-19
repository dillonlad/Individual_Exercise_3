from datetime import timedelta, datetime
from urllib.parse import urlparse, urljoin

from flask import render_template, Blueprint, request, flash, redirect, url_for, Flask, make_response, abort, \
    render_template_string, jsonify
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
from app.main.forms import SignupForm, LoginForm, PostForm, BlogEditor, CreateArticle, SearchForm
from app.main.routes import bp_main

from app.models import Posts_two, Blogs, Profile, Categories, Series, Authors, Comments_dg_tmp, \
    mailing_list
import paypalrestsdk

from app.shop.forms import testShop

bp_shop = Blueprint('shop', __name__, url_prefix="/shop")

paypalrestsdk.configure({
  "mode": "sandbox", # sandbox or live
  "client_id": "AY4ffGjZA7NXzbriohRQzXUhQQ2bB-FHw3G4WD-az18s7JkKvLdHUoitBeG4oPwsUm20EI7FzKxWJySF",
  "client_secret": "EJseVVNIHj6VaU9cRz6vICNnWlgmK4l_aH51iRvOzru99WEF3u2Mujy4r98LWw79aD-PgKC6xNxZgLfj" })


@bp_shop.route('/', methods=['GET'])
def shop():
    return render_template_string("<h1>Shop coming very soon!</h1> Return <a href='{{ url_for('main.index') }}'>home</a>")


@bp_shop.route('/test', methods=['GET', 'POST'])
def shop_test():
    testshopform = testShop()
    test_shop_cookie_item = make_response(render_template("shop_test.html", testshopform=testshopform))
    if request.method == 'POST':
        test_shop_cookie_item.set_cookie('item', testshopform.item.data)
        test_shop_cookie_item.set_cookie('price', testshopform.price.data)
        test_shop_cookie_item.set_cookie('quantity', int(testshopform.quantity.data))
        return render_template("shop_test.html", testshopform=testshopform)
    else:
        return test_shop_cookie_item


@bp_shop.route('/payment', methods=['POST'])
def payment():
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"},
        "redirect_urls": {
            "return_url": "http://127.0.0.1:5000/execute",
            "cancel_url": "http://127.0.0.1:5000/"},
        "transactions": [{
            "item_list": {
                "items": [{
                    "name": "{}".format(request.cookies.get("item")),
                    "sku": "12345",
                    "price": "{}".format(request.cookies.get("price")),
                    "currency": "USD",
                    "quantity": request.cookies.get("quantity")}]},
            "amount": {
                "total": "{}".format(request.cookies.get("price")),
                "currency": "USD"},
            "description": "This is the payment transaction description."}]})
    if payment.create():
        print('Payment success!')
    else:
        print(payment.error)
    return jsonify({'paymentID' : payment.id})


@bp_shop.route('/execute', methods=['POST'])
def execute():
    success = False
    payment = paypalrestsdk.Payment.find(request.form['paymentID'])
    if payment.execute({'payer_id' : request.form['payerID']}):
        print('Execute success!')
        success = True
    else:
        print(payment.error)
    return jsonify({'success' : success})


@bp_shop.errorhandler(404)
def pnf_404(error):
    return render_template("404.html"), 404


@bp_shop.errorhandler(500)
def pnf_500(error):
    return render_template("500.html"), 500