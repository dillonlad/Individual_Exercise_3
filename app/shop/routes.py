import re
from app.AuthenticationModule import url_homepage, url_https
from datetime import timedelta, datetime
from urllib.parse import urlparse, urljoin
from app.LoadingModule import load_templates

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
from app import db, mail_sender
from app.main.forms import SignupForm, LoginForm, PostForm, BlogEditor, CreateArticle, SearchForm
from app.main.routes import bp_main, cookies_accept, third_party_cookies

from app.models import Posts_two, Blogs, Profile, Categories, Series, Authors, Comments_dg_tmp, \
    mailing_list, shop_items, main_stock_list, item_reviews
import paypalrestsdk

from app.paypal_api_call import CreateOrder
from app.shop.forms import testShop, CreditCardPayment, EnquiryForm, RatingForm
from app.new_paypal import PayPalClient
from paypalcheckoutsdk.orders import OrdersCreateRequest, OrdersCaptureRequest
from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment, LiveEnvironment


bp_shop = Blueprint('shop', __name__, url_prefix="/shop")
ADMINS = ['inwaitoftomorrow@gmail.com']


paypalrestsdk.configure({
  "mode": "sandbox", # sandbox or live
  "client_id": "AY4ffGjZA7NXzbriohRQzXUhQQ2bB-FHw3G4WD-az18s7JkKvLdHUoitBeG4oPwsUm20EI7FzKxWJySF",
  "client_secret": "EJseVVNIHj6VaU9cRz6vICNnWlgmK4l_aH51iRvOzru99WEF3u2Mujy4r98LWw79aD-PgKC6xNxZgLfj" })


# sandbox credentials
# client id: AY4ffGjZA7NXzbriohRQzXUhQQ2bB-FHw3G4WD-az18s7JkKvLdHUoitBeG4oPwsUm20EI7FzKxWJySF
# client secret: EJseVVNIHj6VaU9cRz6vICNnWlgmK4l_aH51iRvOzru99WEF3u2Mujy4r98LWw79aD-PgKC6xNxZgLfj

# live credentials
# client id: AX1xZ5LS2EKdjzXGX5s9pqscRnp_HXF_DYoUarP40589iY4891E4bGL0OwllD8JSBwEQ6AWgkBDPvs5A
# client secret: EDdiEGaGzpXfTXIt5zgmDr1VW_-y7K5NzOedZSQ6uEqjjAhyEgEeWSDLpqiJNVt9LagWRB66GobPOwCt


client_id = "AX1xZ5LS2EKdjzXGX5s9pqscRnp_HXF_DYoUarP40589iY4891E4bGL0OwllD8JSBwEQ6AWgkBDPvs5A"
client_secret = "EDdiEGaGzpXfTXIt5zgmDr1VW_-y7K5NzOedZSQ6uEqjjAhyEgEeWSDLpqiJNVt9LagWRB66GobPOwCt"
# Creating an environment
environment = LiveEnvironment(client_id=client_id, client_secret=client_secret)
client = PayPalHttpClient(environment)


def structured_data(item_on_page, average_rating, review_count, reviews):

    item_name = item_on_page.item_name
    item_no = item_on_page.item_number
    item_price = float(item_on_page.price)
    item_image = item_on_page.meta_image
    item_desc = item_on_page.meta_description

    reviews_data = []

    for var_review in reviews:
        structured_review = {
            "@type": "Review",
            "author": "{}".format(var_review.name),
            "datePublished": "{}".format(var_review.date),
            "reviewBody": "{}".format(var_review.review),
            "name": "{} stars".format(var_review.stars),
            "reviewRating": {
                "@type": "Rating",
                "bestRating": "5",
                "ratingValue": "{}".format(var_review.stars),
                "worstRating": "1"
            }
        }
        reviews_data.append(structured_review)

    aggregate_rating = {
        "@type": "AggregateRating",
        "ratingValue": "{}".format(average_rating),
        "reviewCount": "{}".format(review_count)
    }

    structured_data_dict = {
        "@context": "https://schema.org",
        "@type": "Product",
        "aggregateRating": aggregate_rating,
        "description": "{}".format(item_desc),
        "name": "{}".format(item_name),
        "image": "{}".format(item_image),
        "availability": "https://schema.org/InStock",
        "price": "{}".format(item_price),
        "priceCurrency": "GBP",
        "brand": "What Next Bro?",
        "sku": "{}".format(item_no),
        "review": reviews_data
    }

    json_structured_data = json.dumps(structured_data_dict)
    html_insert = render_template_string('<script type="application/ld+json">{}</script>'.format(json_structured_data))

    return html_insert


@bp_shop.route('/', methods=['GET'])
@url_https
@url_homepage
def shop():
    categories, navigation_page, allow_third_party_cookies, footer = load_templates()
    items = shop_items.query.all()
    return render_template('shop.html', items=items, allow_third_party_cookies=allow_third_party_cookies, 
                            categories=categories, navigation_page=navigation_page, footer=footer)


@bp_shop.route('/<id>', methods=['GET', 'POST'])
@url_https
def shop_item(id):
    
    if shop_items.query.filter(shop_items.item_id.contains(id)).all():
        categories, navigation_page, allow_third_party_cookies, footer = load_templates()
        privacy_policy = render_template('privacy_statement.html')

        item_on_page = shop_items.query.filter_by(item_id=id).all()[0]
        item_name = item_on_page.item_name
        item_no = item_on_page.item_number
        item_price = float(item_on_page.price)
        json_insert = json.dumps({"item_id":id, "item_name": item_name, "item_no":item_no, "item_price":item_price})
        reviews = item_reviews.query.order_by(desc(item_reviews.review_id)).filter(item_reviews.item_id==item_no).all()
        
        stars_total = sum(var_review.stars for var_review in reviews)
        stars_total = 0
        number_of_reviews = len(reviews)
        for var_review in reviews:
            item_stars = var_review.stars
            stars_total += item_stars
        avg_rating = stars_total/number_of_reviews
        int_avg_rating = int(avg_rating)
        data_structure = structured_data(item_on_page, int_avg_rating, number_of_reviews, reviews)
        
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
        return render_template("item_shop.html", allow_third_party_cookies=allow_third_party_cookies, 
                            testshopform=testshopform, categories=categories, item_on_page=[item_on_page], 
                            privacy_policy=privacy_policy, navigation_page=navigation_page, reviews=reviews, 
                            number_of_reviews=number_of_reviews, average_rating=int_avg_rating, 
                            data_structure=data_structure, json_insert=json_insert)


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
@url_https
def shop_cart():
    privacy_policy = render_template('privacy_statement.html')
    categories, navigation_page, allow_third_party_cookies, footer = load_templates()
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
            shipping_cost = 32.91
            shipping_msg = "Intl"
        else:
            shipping_cost = 0.00
            shipping_msg = "Free Delivery, UK ONLY"
        final_with_shipping = round(final_cost + shipping_cost, 2)
        return render_template('cart-live.html', allow_third_party_cookies=allow_third_party_cookies, 
                            categories=categories, final_cost=final_cost, counter=counter, items=items_in_cart,
                            colours=colours_in_cart, quantities=new_quantities, sizes=sizes_in_cart, 
                            prices=prices_in_cart, cost_list=cost_list, final_with_shipping=final_with_shipping, 
                            privacy_policy=privacy_policy, shipping_cost=shipping_cost, navigation_page=navigation_page, 
                            shipping_msg=shipping_msg)
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
        shipping_cost = 32.91 if 'abroad_delivery' in session else 0.00
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
    cookies_accept()
    allow_third_party_cookies = third_party_cookies()
    if request.method == 'POST' and form.validate():
        with app.mail.connect() as conn:
            msg = Message('{} - comment'.format(form.name.data), sender=mail_sender, recipients=ADMINS)
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
            if (len(form.name.data) > 0 and len(form.message.data) > 0) or (
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
            return render_template('enquiry_page.html', form=form, allow_third_party_cookies=allow_third_party_cookies)


@bp_shop.route('/review/<id>', methods=['GET', 'POST'])
def item_review(id):
    form = RatingForm(request.form)
    categories = Categories.query.all()
    navigation_page = render_template('navigation.html', categories=categories)
    cookies_accept()
    allow_third_party_cookies = third_party_cookies()
    if request.method == 'POST' and form.validate():
        with app.mail.connect() as conn:
            msg = Message('{} - comment'.format(form.name.data), sender=mail_sender, recipients=ADMINS)
            msg.body = '{}'.format(form.comment.data)
            msg.html = '<b>{}</b> says {}. Stars: {}. Item: {}'.format(
                form.name.data, form.comment.data, form.stars.data, id)
            conn.send(msg)
        flash('Thanks for the reply! We will get back to you as soon as possible!')
        return redirect(url_for('shop.shop'), code=303)
    else:
        if form.is_submitted():
            form.method = 'POST'
            if (len(form.name.data) > 0 and len(form.comment.data) > 0) or (
                    len(form.name.data) > 0):
                with app.mail.connect() as conn:
                    msg = Message('{} - comment'.format(form.name.data), sender=mail_sender, recipients=ADMINS)
                    msg.body = '{}'.format(form.comment.data)
                    msg.html = '<b>{}</b> says {}. Stars: {}. Item; {}'.format(
                        form.name.data, form.comment.data, form.stars.data, id)
                    conn.send(msg)
                flash('Thanks for the reply! We will get back to you as soon as possible!')
                return redirect(url_for('shop.shop'), code=303)
            else:
                flash('Thanks for the reply! We will get back to you as soon as possible!')
                return redirect(url_for('shop.shop'), code=303)
        else:
            return render_template('review_page.html', allow_third_party_cookies=allow_third_party_cookies, form=form, navigation_page=navigation_page)


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
        elif stock_number == 1:
            status = "Only 1 left in stock"
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