from werkzeug.security import generate_password_hash, check_password_hash

from app import db


class Comments(db.Model):
    name = db.Column(db.Text, nullable=False, primary_key=True)
    comment = db.Column(db.Text, nullable=False)
    blog_name = db.Column(db.Text)
    date = db.Column(db.Text)


class Posts(db.Model):
    post_name = db.Column(db.Text, nullable=False, primary_key=True)
    post_description = db.Column(db.Text, nullable=False)
    post_image = db.Column(db.BLOB, nullable=False)
    post_hyperlink = db.Column(db.Text, nullable=False)
    

class Posts_two(db.Model):
    post_name = db.Column(db.Text, nullable=False, primary_key=True)
    post_description = db.Column(db.Text, nullable=False)
    post_image = db.Column(db.Text, nullable=False)
    post_hyperlink = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, nullable=True)
    category_name = db.Column(db.Text, nullable=True)
    article_id = db.Column(db.Integer, nullable=True)