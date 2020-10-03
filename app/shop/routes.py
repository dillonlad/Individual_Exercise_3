from datetime import timedelta, datetime
from urllib.parse import urlparse, urljoin

import flask
from flask import render_template, Blueprint, request, flash, redirect, url_for, Flask, make_response, abort, \
    render_template_string, jsonify, session, json
from flask_login import login_required, current_user, logout_user, login_user
from flask_mail import Mail, Message
from flask_mobility import Mobility
from flask_mobility.decorators import mobile_template, mobilized
from markupsafe import Markup
from paypalhttp import HttpError
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
    mailing_list, shop_items, main_stock_list
import paypalrestsdk

from app.paypal_api_call import CreateOrder
from app.shop.forms import testShop, CreditCardPayment, EnquiryForm
from app.new_paypal import PayPalClient
from paypalcheckoutsdk.orders import OrdersCreateRequest, OrdersCaptureRequest
from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment, LiveEnvironment



bp_shop = Blueprint('shop', __name__, url_prefix="/shop")
ADMINS = ['inwaitoftomorrow@gmail.com']


paypalrestsdk.configure({
  "mode": "live", # sandbox or live
  "client_id": "AX1xZ5LS2EKdjzXGX5s9pqscRnp_HXF_DYoUarP40589iY4891E4bGL0OwllD8JSBwEQ6AWgkBDPvs5A",
  "client_secret": "EDdiEGaGzpXfTXIt5zgmDr1VW_-y7K5NzOedZSQ6uEqjjAhyEgEeWSDLpqiJNVt9LagWRB66GobPOwCt" })


client_id = "AX1xZ5LS2EKdjzXGX5s9pqscRnp_HXF_DYoUarP40589iY4891E4bGL0OwllD8JSBwEQ6AWgkBDPvs5A"
client_secret = "EDdiEGaGzpXfTXIt5zgmDr1VW_-y7K5NzOedZSQ6uEqjjAhyEgEeWSDLpqiJNVt9LagWRB66GobPOwCt"
# Creating an environment
environment = LiveEnvironment(client_id=client_id, client_secret=client_secret)
client = PayPalHttpClient(environment)


@bp_shop.route('/', methods=['GET'])
def shop():
    host = request.host
    if "www" in host:
        return redirect('https://inwaitoftomorrow.appspot.com/shop/', code=301)
    elif "inwaitoftomorrow.com" in host:
        return redirect('https://inwaitoftomorrow.appspot.com/shop/', code=301)
    elif request.url.startswith('http://') and '127' not in host:
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)
    else:
        categories = Categories.query.all()
        navigation_page = render_template('navigation.html', categories=categories)
        items = shop_items.query.all()
        return render_template('shop.html', items=items, categories=categories, navigation_page=navigation_page)


@bp_shop.route('/<id>', methods=['GET', 'POST'])
def shop_item(id):
    host = request.host
    if request.url.startswith('http://') and '127' not in host:
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)
    else:
        if shop_items.query.filter(shop_items.item_id.contains(id)).all():
            categories = Categories.query.all()
            navigation_page = render_template('navigation.html', categories=categories)
            item_on_page = shop_items.query.filter_by(item_id=id).all()
            privacy_policy = render_template('privacy_statement.html')
            for var in item_on_page:
                item_name = var.item_name
                item_no = var.item_number
                item_price = float(var.price)
            testshopform = testShop(request.form)
            if request.method == 'POST':
                if testshopform.colour.data == "Please select":
                    flash('Invalid colour request')
                    return redirect(url_for('shop.shop_item', id=id))
                elif testshopform.size.data == "Please select":
                    flash('Invalid size request')
                    return redirect(url_for('shop.shop_item', id=id))
                else:
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
                    if testshopform.colour.data == "Please select":
                        flash('Invalid colour request')
                        return redirect(url_for('shop.shop_item', id=id))
                    elif testshopform.size.data == "Please select":
                        flash('Invalid size request')
                        return redirect(url_for('shop.shop_item', id=id))
                    else:
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
            return render_template("item_shop.html", testshopform=testshopform, categories=categories, item_on_page=item_on_page, privacy_policy=privacy_policy, navigation_page=navigation_page)


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
    navigation_page = render_template('navigation.html', categories=categories)
    privacy_policy = render_template('privacy_statement.html')
    if 'cart' in session:
        items_in_cart = session['cart']
        colours_in_cart = session['colour']
        quantities_in_cart = session['quantity']
        prices_in_cart = session['itemprice']
        sizes_in_cart = session['size']
        counter = len(items_in_cart)
        cost_list = []
        new_quantities = []
        for i in range(counter):
            cost = quantities_in_cart[i]*prices_in_cart[i]
            cost_list.append(cost)
            new_quantity = int(quantities_in_cart[i])
            new_quantities.append(new_quantity)
        final_cost = round(sum(cost_list), 2)
        if 'abroad_delivery' in session:
            shipping_cost = 9.85
            shipping_msg = "Intl"
        else:
            shipping_cost = 4.10
            shipping_msg = "UK"
        final_with_shipping = round(final_cost + shipping_cost, 2)
        return render_template('cart-live.html', categories=categories, final_cost=final_cost, counter=counter, items=items_in_cart, colours=colours_in_cart, quantities=new_quantities, sizes=sizes_in_cart, prices=prices_in_cart, cost_list=cost_list, final_with_shipping=final_with_shipping, privacy_policy=privacy_policy, shipping_cost=shipping_cost, navigation_page=navigation_page, shipping_msg=shipping_msg)
    else:
        flash('You have no items in your cart')
        return redirect(url_for('shop.shop'))


@bp_shop.route('/card-payment', methods=['GET', 'POST'])
def card_payment():
    if 'cart' in session:
        items_in_cart = session.get('cart', [])
        counter = len(items_in_cart)
        items_to_buy = []
        price_amount_list = []
        if 'abroad_delivery' in session:
            shipping_cost = 9.85
        else:
            shipping_cost = 4.10
        for it in range(counter):
            item_details = {
                "name": "{}, size: {}, colour: {}".format(session['cart'][it], session['size'][it],
                                                          session['colour'][it]),
                "sku": "{}".format(session['item_number'][it]),
                "unit_amount": {
                    "currency_code": "GBP",
                    "value": "{}".format(session['itemprice'][it])},
                "quantity": int(session['quantity'][it])}
            items_to_buy.append(item_details)
            price_amount = session['itemprice'][it] * session['quantity'][it]
            price_amount_list.append(price_amount)
        price_total_amount = round(sum(price_amount_list), 2)
        inc_shipping = round(price_total_amount + shipping_cost, 2)
        request = OrdersCreateRequest()

        request.prefer('return=representation')

        pay_body = \
            {
                "intent": "CAPTURE",
                "purchase_units": [{
                    "amount": {
                        "currency_code": "GBP",
                        "value": "{}".format(inc_shipping),
                        "breakdown": {
                            "item_total": {
                                "currency_code": "GBP",
                                 "value": "{}".format(price_total_amount)},
                            "shipping": {
                                "currency_code": "GBP",
                                "value": "{}".format(shipping_cost)}
                        }
                    },
                    "items": items_to_buy}]
            }
        order_creation = create_order(pay_body, debug=True)
        print(order_creation)
        return order_creation
    else:
        flash('You have no items in your cart')
        return redirect(url_for('shop.shop'))


@bp_shop.route('/card-execute', methods=['GET', 'POST'])
def card_execute():
    if 'cart' in session:
        order_id = session['order_id']
        return capture_order(order_id, debug=True)
    else:
        flash('You have no items in your cart')
        return redirect(url_for('shop.shop'))


@bp_shop.route('/empty', methods=['GET', 'POST'])
def empty_basket():
    session.clear()
    return redirect(url_for('shop.shop'))


@bp_shop.route('/enquiry', methods=['GET', 'POST'])
def enquiry():
    form = EnquiryForm(request.form)
    if request.method == 'POST' and form.validate():
        with app.mail.connect() as conn:
            msg = Message('{} - comment'.format(form.name.data), sender=ADMINS[0], recipients=ADMINS)
            msg.body = '{}'.format(form.message.data)
            user_email = form.email.data
            if user_email == "":
                user_email = "not provided"
            msg.html = '<b>{}</b> says {}. Email: {}'.format(
                form.name.data, form.message.data, user_email)
            conn.send(msg)
        flash('Thanks for the reply! We will get back to you as soon as possible!')
        return redirect(url_for('shop.shop'), code=303)
    else:
        if form.is_submitted():
            form.method = 'POST'
            if (len(form.name.data) > 0 and len(form.comment.data) > 0) or (
                    len(form.name.data) > 0 and len(form.email.data) > 0):
                with app.mail.connect() as conn:
                    msg = Message('{} - comment'.format(form.name.data), sender=ADMINS[0], recipients=ADMINS)
                    msg.body = '{}'.format(form.message.data)
                    user_email = form.email.data
                    if user_email == "":
                        user_email = "not provided"
                    msg.html = '<b>{}</b> says {}. Email: {}'.format(
                        form.name.data, form.message.data, user_email)
                    conn.send(msg)
                flash('Thanks for the reply! We will get back to you as soon as possible!')
                return redirect(url_for('shop.shop'), code=303)
            else:
                flash('Thanks for the reply! We will get back to you as soon as possible!')
                return redirect(url_for('shop.shop'), code=303)
        else:
            return render_template('enquiry_page.html', form=form)


@bp_shop.route('/abroad-delivery')
def abroad_delivery():
    session['abroad_delivery'] = "Yes"
    return redirect(url_for('shop.shop_cart'))


@bp_shop.route('/stock/<id>/<item_number>/<Colour>/<Size>', methods=['GET', 'POST'])
def stock_checker(id, item_number, Colour, Size):
    if main_stock_list.query.filter(main_stock_list.item_number.contains(item_number)).filter(main_stock_list.Size.contains(Size)).filter(main_stock_list.Colour.contains(Colour)).all():
        stock_item = main_stock_list.query.filter_by(item_number=item_number).filter_by(Size=Size).filter_by(Colour=Colour).all()
        for var in stock_item:
            stock_number = var.stock
        if stock_number == 0:
            status = "Unfortunately, this item is OUT OF STOCK in this size, please enquire below if you'd like one so that we know"
        else:
            status = "In stock"
        return jsonify(stock_status=status)


@bp_shop.errorhandler(404)
def pnf_404(error):
    return render_template("404.html"), 404


@bp_shop.errorhandler(500)
def pnf_500(error):
    return render_template("500.html"), 500


def create_order(payment_body, debug=False):
    request_order = OrdersCreateRequest()
    request_order.prefer('return=representation')
    #3. Call PayPal to set up a transaction
    request_order.request_body(payment_body)
    response = client.execute(request_order)
    if debug:
        print('Order With Complete Payload:')
        print('Status Code:', response.status_code)
        print('Status:', response.result.status)
        print('Order ID:', response.result.id)
        session['order_id'] = response.result.id
        print('Intent:', response.result.intent)
        print('Links:')
        for link in response.result.links:
            print('\t{}: {}\tCall Type: {}'.format(link.rel, link.href, link.method))
            print('Total Amount: {} {}'.format(response.result.purchase_units[0].amount.currency_code,
                                               response.result.purchase_units[0].amount.value))
            # If call returns body in response, you can get the deserialized version from the result attribute of the response
    return jsonify(status_code=response.status_code,
                   status=response.result.status,
                   orderID=response.result.id,
                   intent=response.result.intent)


def capture_order(order_id, debug=False):
    """Method to capture order using order_id"""
    request = OrdersCaptureRequest(order_id)
    # 3. Call PayPal to capture an order
    response = client.execute(request)
    # 4. Save the capture ID to your database. Implement logic to save capture to your database for future reference.
    if debug:
        print('Status Code: ', response.status_code)
        print('Status: ', response.result.status)
        print('Order ID: ', response.result.id)
        print('Links: ')
        for link in response.result.links:
            print('\t{}: {}\tCall Type: {}'.format(link.rel, link.href, link.method))
        print('Capture Ids: ')
        for purchase_unit in response.result.purchase_units:
            for capture in purchase_unit.payments.captures:
              print('\t', capture.id)
        print("Buyer:")
        print("\tEmail Address: {}\n\tName: {}\n\t".format(response.result.payer.email_address,
                response.result.payer.name.given_name + " " + response.result.payer.name.surname))
        flash('Transaction completed!')
    return jsonify(status_code=response.status_code,
                   status=response.result.status,
                   orderID=response.result.id)