from flask import Blueprint, render_template, make_response

from app.models import Categories, Blogs, shop_items

bp_sitemaps = Blueprint('sitemaps', __name__)


@bp_sitemaps.route('/sitemap-index.xml')
def sitemap_index():
    return render_template('sitemap_index.xml')


@bp_sitemaps.route('/articles-sitemap.xml', methods=['GET'])
def articles_sitemap():
    categories = Categories.query.all()
    articles = Blogs.query.all()
    return render_template('sitemap_blogs.xml', categories=categories, articles=articles)


@bp_sitemaps.route('/sitemap-news.xml', methods=['GET'])
def news_sitemap():
    articles = Blogs.query.all()
    list_of_articles = []
    for article in articles:
        article_dict = {}
        article_url = article.url_
        if '_' in article_url:
            article_url = article_url.replace("_","-")
        if 'http://' in article_url:
            article_url = article_url.replace("http://","https://")

        article_dict['url'] = article_url
        article_dict['Date'] = article.Date
        article_dict['Title'] = article.Title
        article_dict['last_mod'] = article.date_mod
        list_of_articles.append(article_dict)
    return render_template('news_sitemap.xml', articles=list_of_articles)


@bp_sitemaps.route('/products-sitemap.xml', methods=['GET'])
def products_sitemap():
    products = shop_items.query.all()
    return render_template('sitemap_products.xml', products=products)


@bp_sitemaps.route('/robots.txt', methods=['GET'])
def robots_file():
    response = make_response(open('robots.txt').read())
    response.headers["Content-type"] = "text/plain"
    return response


@bp_sitemaps.route('/e2signi7jnwn91lzisnqiix5uvmc3v.html', methods=['GET'])
def facebook_verify():
    return render_template('e2signi7jnwn91lzisnqiix5uvmc3v.html')