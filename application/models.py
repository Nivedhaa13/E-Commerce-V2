from application.database import *
from flask_security import UserMixin, RoleMixin
from datetime import datetime 
from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField, IntegerField,HiddenField,SelectField,FieldList
from wtforms.validators import InputRequired, Length, DataRequired,Email
from datetime import datetime
from application.database import db
from flask import make_response
from werkzeug.exceptions import HTTPException
import json

roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))) 

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    address = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    orders = db.relationship('Order', backref='user', lazy=True)
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))
    fs_uniquifier = db.Column(db.String(255), unique=True, nullable=False) 
    active = db.Column(db.Boolean())
    is_approved = db.Column(db.Boolean, default=False)

class Role(db.Model, RoleMixin):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40))
    description = db.Column(db.String(255))

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    products = db.relationship('Product', backref='category')

class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)

class Cart(db.Model):
    __tablename__ = 'cart'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    product = db.relationship('Product', backref='carts', primaryjoin='Cart.product_id == Product.id')
    user = db.relationship('User', backref='carts', primaryjoin='Cart.user_id == User.id')

class Order(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)

class NotFoundError(HTTPException):
    def __init__(self, status_code):
        self.response = make_response('', status_code)


class BusinessValidationError(HTTPException):
    def __init__(self, status_code, error_code, error_message):
        message = {'error_code': error_code, 'error_message': error_message}
        self.response = make_response(json.dumps(message), status_code)





  