from flask_restful import Resource, fields, marshal_with, reqparse
from flask_security import SQLAlchemyUserDatastore
from application.database import db
from application.models import User, Role,Product, Order, EditRequest, BusinessValidationError, NotFoundError, Category, Cart
#from .tasks import send_email
from application.models import User, User_Order, roles_users, Role,Product, Order, BusinessValidationError, NotFoundError, Category, Cart
from flask_bcrypt import Bcrypt
from werkzeug.exceptions import Conflict
from sqlalchemy.exc import IntegrityError
from flask_security import roles_required
from werkzeug.security import check_password_hash,generate_password_hash
from functools import wraps
from flask import jsonify
import datetime
from .cac import cache
from flask import jsonify, Response
from flask_restful import Resource
from io import StringIO
from .export_csv import export_orders_to_csv, export_products_to_csv,export_user_order_to_csv
# from .cac import cache
import json

import time

bcrypt = Bcrypt()

user_datastore = SQLAlchemyUserDatastore(db, User, Role)

def admin_required(fn):
    @wraps(fn)
    @roles_required('admin')
    def decorated_view(*args, **kwargs):
        return fn(*args, **kwargs)
    return decorated_view

def store_manager_required(fn):
    @wraps(fn)
    @roles_required('store manager')
    def decorated_view(*args, **kwargs):
        return fn(*args, **kwargs)
    return decorated_view



class UserResource(Resource):
    def post(self):
        user_req_parser = reqparse.RequestParser()
        user_req_parser.add_argument('username', required=True, help="Username is required")
        user_req_parser.add_argument('email', required=True, help="Email is required")
        user_req_parser.add_argument('address', required=True, help="Address is required")
        user_req_parser.add_argument('password', required=True, help="Password is required")
        args = user_req_parser.parse_args()
        username = args.get('username')
        email = args.get('email')
        address = args.get('address')
        password = args.get('password')

        if user_datastore.find_user(email=email) or user_datastore.find_user(username=username):
            raise Conflict

        try:
            hashed_password = generate_password_hash(password)
            user = user_datastore.create_user(username=username, email=email, address=address, password=hashed_password)
            db.session.commit()
            user_datastore.add_role_to_user(user, 'user')
            db.session.commit()

            return {"username": user.username}
        except IntegrityError:
            return {"signup": "failed"}, 406
        
class UserLoginResource(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', required=True) 
        parser.add_argument('password', required=True)
        args = parser.parse_args()

        user = User.query.filter_by(email=args['email']).first()  

        if user and check_password_hash(user.password, args['password']):
            user_roles = db.session.query(Role.name).join(roles_users).filter(roles_users.c.user_id == user.id).all()

            roles = [role[0] for role in user_roles]
                
            return {
                    "fs_uniquifier": user.fs_uniquifier,
                    "user_id": user.id,
                    "message": "Login successful",
                    "is_approved": user.is_approved,
                    "roles": roles 
                }, 200
        else:
            return {"message": "Invalid email or password"}, 401

class LoginResource(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', required=True) 
        parser.add_argument('password', required=True)
        args = parser.parse_args()

        user = User.query.filter_by(email=args['email']).first()  

        if user and check_password_hash(user.password, args['password']):
            if user.is_approved:
                user_roles = db.session.query(Role.name).join(roles_users).filter(roles_users.c.user_id == user.id).all()
                roles = [role[0] for role in user_roles]
                return {
                    "fs_uniquifier": user.fs_uniquifier,
                    "user_id": user.id,
                    "message": "Login successful",
                    "is_approved": user.is_approved,
                    "roles": roles
                }, 200
            else:
                return {"message": "Account not yet approved. Please wait for approval."}, 401
        else:
            return {"message": "Invalid email or password"}, 401





class StoreManagerRegistrationResource(Resource):
    def post(self):
        manager_req_parser = reqparse.RequestParser()
        manager_req_parser.add_argument('username', required=True, help="Username is required")
        manager_req_parser.add_argument('email', required=True, help="Email is required")
        manager_req_parser.add_argument('address', required=True, help="Address is required")
        manager_req_parser.add_argument('password', required=True, help="Password is required")
        args = manager_req_parser.parse_args()
        username = args.get('username')
        email = args.get('email')
        address = args.get('address')
        password = args.get('password')

        if user_datastore.find_user(email=email) or user_datastore.find_user(username=username):
            raise Conflict
        try:
            hashed_password = generate_password_hash(password)
            user = user_datastore.create_user(username=username, email=email, password=hashed_password,address=address)
            db.session.commit()
            is_approved = db.Column(db.Boolean, default=False)
            db.session.commit()
            user_datastore.add_role_to_user(user, 'store manager')
            db.session.commit()
            
            return {"message": "Store manager registered successfully"}, 201
        except IntegrityError:
            return {"signup": "failed"}, 406
        
class UnapprovedManagersResource(Resource):
    #@cache.memoize(50)
    def get(self):
        unapproved_managers = User.query.filter(User.is_approved == False, User.roles.any(Role.name == 'store manager')).all()
        unapproved_managers_data = [
            {
                "id": manager.id,
                "username": manager.username,
                "email": manager.email,
            }
            for manager in unapproved_managers
        ]
        return unapproved_managers_data, 200
class ApproveManagerResource(Resource):
    def post(self, manager_id):
        manager = User.query.get(manager_id)
        if manager:
            manager.is_approved = True
            db.session.commit()
            return {"message": "Manager approved successfully"}, 200
        else:
            return {"message": "Manager not found"}, 404


class CategoryRequestResource(Resource):
    #@cache.memoize(50)
    def get(self):
        edit_requests = EditRequest.query.all()
        result = [
            {
                'id': request.id,
                'store_manager_id': request.store_manager_id,
                'category_id': request.category_id,
                'request_message': request.request_message,
                'is_approved': request.is_approved,
            }
            for request in edit_requests
        ]
        return result, 200
    
    
    def post(self):
        request_parser = reqparse.RequestParser()
        request_parser.add_argument('store_manager_id', type=int, required=True)
        request_parser.add_argument('category_id', type=int, required=True)
        request_parser.add_argument('request_message', type=str, required=True)
        args = request_parser.parse_args()

        store_manager_id = args['store_manager_id']
        category_id = args['category_id']
        request_message = args['request_message']

        new_request = EditRequest(store_manager_id=store_manager_id, category_id=category_id, request_message=request_message)
        db.session.add(new_request)
        db.session.commit()

        return {"message": "Edit request submitted successfully"}, 201
    
class AddCategoryRequestResource(Resource):
    def post(self):
        request_parser = reqparse.RequestParser()
        request_parser.add_argument('store_manager_id', type=int, required=True)
        request_parser.add_argument('request_message', type=str, required=True)
        args = request_parser.parse_args()

        store_manager_id = args['store_manager_id']
        request_message = args['request_message']
        new_category_request = EditRequest(
            store_manager_id=store_manager_id,
            category_id=None, 
            request_message=request_message,
        )
        db.session.add(new_category_request)
        db.session.commit()

    
class ApproveEditRequestResource(Resource):
    def post(self, request_id):
        try:
            edit_request = EditRequest.query.get(request_id)
            if edit_request:
                edit_request.is_approved = True
                db.session.commit()
                return {"message": "Edit request approved successfully"}, 200
            else:
                return {"message": "Edit request not found"}, 404
        except Exception as e:
            return {"message": str(e)}, 500


product_parser = reqparse.RequestParser()
product_parser.add_argument('name')
product_parser.add_argument('price', type=float)
product_parser.add_argument('stock', type=int)
product_parser.add_argument('description')
product_parser.add_argument('category_id', type=int)

product_response_fields = {
    "id": fields.Integer(attribute="id"),  
    "name": fields.String(attribute="name"),  
    "price": fields.Float(attribute="price"),  
    "stock": fields.Integer(attribute="stock"),  
    "description": fields.String(attribute="description"),  
    "category_id": fields.Integer(attribute="category_id")  
}


class ProductAPI(Resource):
    @marshal_with(product_response_fields)
    #@cache.cached(timeout=5)
    def get(self, product_id=None):
        if product_id is None:
            all_products = Product.query.all()
            return all_products
        else:
            product = Product.query.get(product_id)
            if product:
                return product
            else:
                raise NotFoundError(status_code=404)
    
    def delete(self, product_id):
        product_exist = db.session.query(
            Product).filter(Product.id == product_id).first()

        if product_exist:
            db.session.delete(product_exist)
            db.session.commit()
            return '', 200

        if product_exist is None:
            raise NotFoundError(status_code=404)
    @marshal_with(product_response_fields)
    def put(self, product_id):
        args = product_parser.parse_args()
        product_name = args.get('name', None)  
        product_price = args.get('price', None) 
        product_stock = args.get('stock', None) 
        product_description = args.get('description', None)
        product_category_id = args.get('category_id', None)


        if product_name is None:
            raise BusinessValidationError(
                status_code=400, error_code='MISSING_PRODUCT_NAME', error_message='Product name is required and should be a string')

        if product_price is None:
            raise BusinessValidationError(
                status_code=400, error_code='MISSING_PRODUCT_PRICE', error_message='Product price is required and should be a number')

        if product_stock is None:
            raise BusinessValidationError(
                status_code=400, error_code='MISSING_PRODUCT_STOCK', error_message='Product stock is required and should be an integer')

        if product_description is None:
            raise BusinessValidationError(
                status_code=400, error_code='MISSING_PRODUCT_DESCRIPTION', error_message='Product description is required and should be a string')

        if product_category_id is None:
            raise BusinessValidationError(
                status_code=400, error_code='MISSING_PRODUCT_CATEGORY', error_message='Product category ID is required and should be an integer')

        product = db.session.query(Product).filter(Product.id == product_id).first()

        if product is None:
            raise NotFoundError(status_code=404)

        product.name = product_name
        product.price = product_price
        product.stock = product_stock
        product.description = product_description
        product.category_id = product_category_id

        db.session.commit()

        return product


    @marshal_with(product_response_fields)
    def post(self):
        args = product_parser.parse_args()
        product_name = args.get('name', None)  
        product_price = args.get('price', None) 
        product_stock = args.get('stock', None) 
        product_description = args.get('description', None)
        product_category_id = args.get('category_id', None)

        if product_name is None:
            raise BusinessValidationError(
                status_code=400, error_code='MISSING_PRODUCT_NAME', error_message='Product name is required and should be a string')

        if product_price is None:
            raise BusinessValidationError(
                status_code=400, error_code='MISSING_PRODUCT_PRICE', error_message='Product price is required and should be a number')

        if product_stock is None:
            raise BusinessValidationError(
                status_code=400, error_code='MISSING_PRODUCT_STOCK', error_message='Product stock is required and should be an integer')

        if product_description is None:
            raise BusinessValidationError(
                status_code=400, error_code='MISSING_PRODUCT_DESCRIPTION', error_message='Product description is required and should be a string')

        if product_category_id is None:
            raise BusinessValidationError(
                status_code=400, error_code='MISSING_PRODUCT_CATEGORY', error_message='Product category ID is required and should be an integer')

        product = db.session.query(Product).filter(Product.name == product_name).first()

        if product:
            raise BusinessValidationError(status_code=409, error_code='PRODUCT_ALREADY_EXISTS', error_message='Product with this name already exists')

        new_product = Product(
            name=product_name,
            price=product_price,
            stock=product_stock,
            description=product_description,
            category_id=product_category_id
        )

        db.session.add(new_product)
        db.session.commit()

        return new_product, 201
    
category_parser = reqparse.RequestParser()
category_parser.add_argument('name', required=True)

category_response_fields = {
    "id": fields.Integer(attribute="id"),
    "name": fields.String(attribute="name")
}

class CategoryAPI(Resource):
    @marshal_with(category_response_fields)
    #@cache.cached(timeout=5)
    def get(self, category_id=None):
        if category_id is None:
            all_categories = Category.query.all()
            return all_categories
        else:
            category = Category.query.get(category_id)
            if category:
                return category
            else:
                raise NotFoundError(status_code=404)

    def delete(self, category_id):
        category_exist = db.session.query(
            Category).filter(Category.id == category_id).first()

        if category_exist:
            db.session.delete(category_exist)
            db.session.commit()
            return '', 200

        if category_exist is None:
            raise NotFoundError(status_code=404)

    @marshal_with(category_response_fields)
    def put(self, category_id):
        args = category_parser.parse_args()
        category_name = args.get('name', None)

        if category_name is None:
            raise BusinessValidationError(
                status_code=400, error_code='MISSING_CATEGORY_NAME', error_message='Category name is required and should be a string')

        category = db.session.query(Category).filter(
            Category.id == category_id).first()

        if category is None:
            raise NotFoundError(status_code=404)

        category.name = category_name
        db.session.commit()

        return category

    @marshal_with(category_response_fields)
    def post(self):
        args = category_parser.parse_args()
        category_name = args.get('name', None)

        if category_name is None:
            raise BusinessValidationError(
                status_code=400, error_code='MISSING_CATEGORY_NAME', error_message='Category name is required and should be a string')

        category = db.session.query(Category).filter(
            Category.name == category_name).first()

        if category:
            raise BusinessValidationError(status_code=409, error_code='CATEGORY_ALREADY_EXISTS', error_message='Category with this name already exists')

        new_category = Category(name=category_name)

        db.session.add(new_category)
        db.session.commit()

        return new_category, 201
cart_parser = reqparse.RequestParser()
cart_parser.add_argument('user_id', type=int, required=True)
cart_parser.add_argument('product_id', type=int, required=True)
cart_parser.add_argument('quantity', type=int, required=True)

cart_response_fields = {
    "id": fields.Integer(attribute="id"),
    "user_id": fields.Integer(attribute="user_id"),
    "product_id": fields.Integer(attribute="product_id"),
    "quantity": fields.Integer(attribute="quantity")
}

class CartAPI(Resource):
    @marshal_with(cart_response_fields)
    #@cache.cached(timeout=5)
    def get(self, cart_id=None):
        total_amount=0
        if cart_id is None:
            all_cart_items = Cart.query.all()
            return all_cart_items
        else:
            cart_item = Cart.query.get(cart_id)
            if cart_item:
                return cart_item
            for cart_item in cart_item:
                product = Product.query.get(cart_item.product_id)
                total_amount += product.price * cart_item.quantity
                return {"total_amount": total_amount}

    
    def delete(self, cart_id):
        cart_item_exist = db.session.query(
            Cart).filter(Cart.id == cart_id).first()

        if cart_item_exist:
            db.session.delete(cart_item_exist)
            db.session.commit()
            return '', 200

        if cart_item_exist is None:
            raise NotFoundError(status_code=404)

    @marshal_with(cart_response_fields)
    def put(self, cart_id):
        args = cart_parser.parse_args()
        user_id = args.get('user_id')
        product_id = args.get('product_id')
        quantity = args.get('quantity')

        cart_item = db.session.query(Cart).filter(Cart.id == cart_id).first()

        if cart_item is None:
            raise NotFoundError(status_code=404)

        cart_item.user_id = user_id
        cart_item.product_id = product_id
        cart_item.quantity = quantity

        db.session.commit()

        return cart_item

    @marshal_with(cart_response_fields)
    def post(self):
        args = cart_parser.parse_args()
        user_id = args.get('user_id')
        product_id = args.get('product_id')
        quantity = args.get('quantity')

        new_cart_item = Cart(user_id=user_id, product_id=product_id, quantity=quantity)

        db.session.add(new_cart_item)
        db.session.commit()

        return new_cart_item, 201

order_parser = reqparse.RequestParser()
order_parser.add_argument('user_id', type=int, required=True)

order_response_fields = {
    # "id": fields.Integer(attribute="id"),
    "user_id": fields.Integer(attribute="user_id"),
    "order_date": fields.DateTime(attribute="order_date"),
    "total_amount": fields.Float(attribute="total_amount")
}
orderproduct_response_fields = {
    "total_amount": fields.Float(attribute="total_amount")
}



class OrdersAPI(Resource):
    #@cache.cached(timeout=5)
    def get(self,user_id):
        #time.sleep(5)
        cart_items = Cart.query.filter_by(user_id=user_id).all()
        total_amount = 0
        
        for cart_item in cart_items:
            product = Product.query.get(cart_item.product_id)
            total_amount += product.price * cart_item.quantity
        # for order in order
        return jsonify({"total_amount": total_amount})


    @marshal_with(order_response_fields)
    def post(self):
        args = order_parser.parse_args()
        user_id = args.get('user_id')
        cart_items = Cart.query.filter_by(user_id=user_id).all()
        total_amount = 0

        for cart_item in cart_items:
            product = Product.query.get(cart_item.product_id)
            total_amount += product.price * cart_item.quantity

        new_order = Order(
            user_id=user_id,
            order_date=datetime.datetime.utcnow(),
            total_amount=total_amount
        )
        db.session.add(new_order)
        db.session.commit()

        for cart_item in cart_items:
            product = Product.query.get(cart_item.product_id)

            new_order_item = User_Order(
                order_id=new_order.id,  
                product_id=product.id,
                quantity=cart_item.quantity,
                product_price=product.price
            )
            db.session.add(new_order_item)
            product.stock -= cart_item.quantity
            db.session.delete(cart_item)

        db.session.commit()

        return new_order, 201


class ExportAPI(Resource):
    def get(self):
        try:
            products = Product.query.all()
            orders = Order.query.all()
            user_orders = User_Order.query.all()

            export_products_to_csv(products)
            export_orders_to_csv(orders)
            export_user_order_to_csv(user_orders)

            response_data = {"message": "CSV export completed."}
            return Response(json.dumps(response_data), status=200, content_type="application/json")

        except Exception as e:
            response_data = {"message": f"Error: {str(e)}"}
            return Response(json.dumps(response_data), status=500, content_type="application/json")
    def post(self):
        try:
            products = Product.query.all()
            orders = Order.query.all()
            user_orders = User_Order.query.all()

            export_products_to_csv(products)
            export_orders_to_csv(orders)
            export_user_order_to_csv(user_orders)

            return jsonify({"message": "CSV export completed."}), 200
        except Exception as e:
            return jsonify({"message": f"Error: {str(e)}"}), 500

    





