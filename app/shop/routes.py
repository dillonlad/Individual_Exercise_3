from datetime import timedelta, datetime
from urllib.parse import urlparse, urljoin

from flask import render_template, Blueprint, request, flash, redirect, url_for, Flask, make_response, abort, \
    render_template_string, jsonify, session
from flask_login import login_required, current_user, logout_user, login_user
from flask_mail import Mail, Message
from flask_mobility import Mobility
from flask_mobility.decorators import mobile_template, mobilized
from markupsafe import Markup
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
    mailing_list, shop_items
import paypalrestsdk

from app.shop.forms import testShop

bp_shop = Blueprint('shop', __name__, url_prefix="/shop")

paypalrestsdk.configure({
  "mode": "live", # sandbox or live
  "client_id": "AX1xZ5LS2EKdjzXGX5s9pqscRnp_HXF_DYoUarP40589iY4891E4bGL0OwllD8JSBwEQ6AWgkBDPvs5A",
  "client_secret": "EDdiEGaGzpXfTXIt5zgmDr1VW_-y7K5NzOedZSQ6uEqjjAhyEgEeWSDLpqiJNVt9LagWRB66GobPOwCt" })


@bp_shop.route('/', methods=['GET'])
def shop():
    categories = Categories.query.all()
    items = shop_items.query.all()
    return render_template('shop.html', items=items, categories=categories)


@bp_shop.route('/<id>', methods=['GET', 'POST'])
def shop_item(id):
    if shop_items.query.filter(shop_items.item_id.contains(id)).all():
        categories = Categories.query.all()
        item_on_page = shop_items.query.filter_by(item_id=id).all()
        for var in item_on_page:
            item_name = var.item_name
            item_no = var.item_number
            item_price = float(var.price)
        testshopform = testShop(request.form)
        if request.method == 'POST':
            if 'size' not in session:
                session['size'] = []
            if 'quantity' not in session:
                session['quantity'] = []
            if 'colour' not in session:
                session['colour'] = []
            if 'item_number' not in session:
                session['item_number'] = []
            if 'itemprice' not in session:
                session['itemprice'] = []
            session['size'].append(testshopform.size.data)
            session['colour'].append(testshopform.colour.data)
            session['quantity'].append(float(testshopform.quantity.data))
            session['item_number'].append(item_no)
            session['itemprice'].append(float(item_price))
            items_in_cart = session.get('itemprice', [])
            counter = len(items_in_cart)
            message = Markup(render_template_string(
                "<!DOCTYPE html><html lang='en'><span>You have added an item to your cart</span><br><span><a href='add-to-cart/{}'>Please click to confirm</a></span></html>".format(
                    id)))
            flash(message)
            return redirect(url_for('shop.shop_item', id=id), code=303)
        else:
            if testshopform.is_submitted():
                testshopform.method = 'POST'
                if 'size' not in session:
                    session['size'] = []
                if 'quantity' not in session:
                    session['quantity'] = []
                if 'colour' not in session:
                    session['colour'] = []
                if 'item_number' not in session:
                    session['item_number'] = []
                if 'itemprice' not in session:
                    session['itemprice'] = []
                session['size'].append(testshopform.size.data)
                session['colour'].append(testshopform.colour.data)
                session['quantity'].append(float(testshopform.quantity.data))
                session['item_number'].append(item_no)
                session['itemprice'].append(item_price)
                items_in_cart = session.get('itemprice', [])
                counter = len(items_in_cart)
                message = Markup(render_template_string(
                    "<!DOCTYPE html><html lang='en'><span>You have added an item to your cart</span><br><span><a href='add-to-cart/{}'>Please click to confirm</a></span></html>".format(
                        id)))
                flash(message)
                return redirect(url_for('shop.shop_item', id=id), code=303)
        return render_template("item_shop.html", testshopform=testshopform, categories=categories, item_on_page=item_on_page)


@bp_shop.route('/add-to-cart/<id>', methods=['GET', 'POST'])
def add_to_cart(id):
    if 'cart' not in session:
        session['cart'] = []
    if 'price' not in session:
        session['price'] = 0

    session['cart'].append(id)
    session['price'] += 25
    print(session)

    return redirect(url_for('shop.shop_cart'))


@bp_shop.route('/cart', methods=['GET', 'POST'])
def shop_cart():
    categories = Categories.query.all()
    if 'cart' in session:
        items_in_cart = session['cart']
        colours_in_cart = session['colour']
        quantities_in_cart = session['quantity']
        prices_in_cart = session['itemprice']
        sizes_in_cart = session['size']
        counter = len(items_in_cart)
        cost_list = []
        for i in range(counter):
            cost = quantities_in_cart[i]*prices_in_cart[i]
            cost_list.append(cost)
        final_cost = round(sum(cost_list), 2)
        return render_template('cart-live.html', categories=categories, final_cost=final_cost, counter=counter, items=items_in_cart, colours=colours_in_cart, quantities=quantities_in_cart, sizes=sizes_in_cart, prices=prices_in_cart)
    else:
        return render_template('cart-live.html', categories=categories, final_cost="0.00", counter=0, items=[], colours=[], quantities=[], sizes=[], prices=[])


@bp_shop.route('/payment', methods=['POST'])
def payment():
    items_in_cart = session.get('cart', [])
    counter = len(items_in_cart)
    items_to_buy = []
    price_amount_list = []
    shipping_cost = 4.10
    for it in range(counter):
        item_details = {
            "name": "{}, size: {}, colour: {}".format(session['cart'][it], session['size'][it],
                                                      session['colour'][it]),
            "sku": "{}".format(session['item_number'][it]),
            "price": "{}".format(session['itemprice'][it]),
            "currency": "GBP",
            "quantity": session['quantity'][it]}
        items_to_buy.append(item_details)
        price_amount = session['itemprice'][it]*session['quantity'][it]
        price_amount_list.append(price_amount)
    price_total_amount = round(sum(price_amount_list), 2)
    inc_shipping = round(price_total_amount + shipping_cost, 2)
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"},
        "redirect_urls": {
            "return_url": "https://inwaitoftomorrow.appspot.com/execute",
            "cancel_url": "https://inwaitoftomorrow.appspot.com/"},
        "transactions": [{
            "item_list": {
                "items": items_to_buy},
            "amount": {
                "total": "{}".format(inc_shipping),
                "currency": "GBP",
                "details": {
                    "subtotal": "{}".format(price_total_amount),
                    "shipping": "{}".format(shipping_cost)
                }
            },
            "description": "Size: {}, Colour: {}".format(session.get('size', []), session.get('colour', []))}]})
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


@bp_shop.route('/empty', methods=['GET', 'POST'])
def empty_basket():
    session.clear()
    return redirect(url_for('shop.shop'))


@bp_shop.errorhandler(404)
def pnf_404(error):
    return render_template("404.html"), 404


@bp_shop.errorhandler(500)
def pnf_500(error):
    return render_template("500.html"), 500