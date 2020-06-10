from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db


class Authors(db.Model):
    author_id = db.Column(db.Integer, nullable=False, primary_key=True)
    author_name = db.Column(db.Text, nullable=False)


class Comments_dg_tmp(db.Model):
    name = db.Column(db.Text, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    blog_name = db.Column(db.Text)
    date = db.Column(db.Text)
    comment_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    stars = db.Column(db.Integer, nullable=True)


class mailing_list(db.Model):
    recipient_id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False)


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


class Blogs(db.Model):
    __tablename__ = 'Blogs'
    Title = db.Column(db.Text, nullable=False, primary_key=True)
    Post_ID = db.Column(db.Text, nullable=True)
    Description = db.Column(db.Text, nullable=True)
    Image_root = db.Column(db.Text, nullable=True)
    url_ = db.Column(db.Text, nullable=True)
    Content = db.Column(db.Text, nullable=False)
    Time = db.Column(db.Text, nullable=True)
    Date = db.Column(db.Text, nullable=True)
    category = db.Column(db.Text, nullable=True)
    article_id = db.Column(db.Integer, autoincrement=True, nullable=False)
    author = db.Column(db.Text, nullable=True)
    keywords = db.Column(db.Text, nullable=True)
    no_series_name = db.Column(db.Text, nullable=True)
    series = db.Column(db.Text, nullable=True)
    Image_iphone = db.Column(db.Text, nullable=True)



class Series(db.Model):
    series_id = db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False)
    series_name = db.Column(db.Text, nullable=False)
    series_key = db.Column(db.Text)
    series_image = db.Column(db.Text, nullable=False)


class Categories(db.Model):
    category_id = db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False)
    category_name = db.Column(db.Text, db.ForeignKey(Blogs.category))


class Profile(UserMixin, db.Model):
    username = db.Column(db.Text, nullable=False, primary_key=True)
    email = db.Column(db.Text, nullable=False)
    password = db.Column(db.Text, nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    # have to use primary key
    def get_id(self):
        return self.username
