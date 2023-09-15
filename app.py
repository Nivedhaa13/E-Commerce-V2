from flask import Flask
from application.database import db 
from application.api import UserResource,ProductAPI,CategoryAPI,CartAPI,ExportAPI
from flask_cors import CORS
from flask_restful import Api
from flask_migrate import Migrate
from flask_security import Security
from application.models import User, Role
from application.cac import cache
from application.api import *
from application.tasks import *
from application.workers import *





config = {
    "DEBUG": True,  
    "CACHE_TYPE": "SimpleCache", 
    "CACHE_DEFAULT_TIMEOUT": 300
}

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'
app.config['SECURITY_PASSWORD_SALT'] = 'thisisasecretsalt'
app.config['WTF_CSRF_ENABLED'] = False
app.config.from_mapping(config)

security = Security(app, user_datastore)
migrate = Migrate(app, db)

CORS(app)


api = Api(app)
db.init_app(app)
#cache.init_app(app)

api.add_resource(UserResource, '/user')
api.add_resource(LoginResource, '/managerlogin')
api.add_resource(UserLoginResource, '/userlogin')
api.add_resource(StoreManagerRegistrationResource, '/store_manager_register')
api.add_resource(UnapprovedManagersResource, '/get_unapproved_managers')
api.add_resource(ApproveManagerResource, '/approve_manager/<int:manager_id>')
api.add_resource(ProductAPI, '/products', '/products/<int:product_id>')
api.add_resource(CategoryAPI, '/categories', '/categories/<int:category_id>')
api.add_resource(CartAPI, '/carts', '/carts/<int:cart_id>')
api.add_resource(OrdersAPI, '/order','/order/<int:user_id>')
api.add_resource(CategoryRequestResource, '/edit_requests')
api.add_resource(ApproveEditRequestResource, '/approve_edit_request/<int:request_id>')
api.add_resource(AddCategoryRequestResource, '/add_new_category_request')
api.add_resource(ExportAPI, '/export')

import time
@app.route("/")
@cache.cached(timeout=5)
def index():
    #time.sleep(10)
    return "hello"

@app.route('/api/approve_store_manager/<int:user_id>', methods=['POST'])
@admin_required
def approve_store_manager(user_id):
    user = User.query.get(user_id)
    if user and user.has_role('store manager'):
        user.is_approved = True
        db.session.commit()
        return {"message": "Store manager approved"}, 200
    return {"message": "User not found or not a store manager"}, 404

app.config.update(CELERY_CONFIG={
    'broker_url': 'redis://localhost:6379/2',
    'result_backend': 'redis://localhost:6379/2',
    'enable_utc': False
})

#celery = make_celery(app)

with app.app_context():
    db.create_all()

    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        admin_role = Role(name='admin', description='Administrator Role')
        db.session.add(admin_role)

    manager_role = Role.query.filter_by(name='store manager').first()
    if not manager_role:
        manager_role = Role(name='store manager', description='Store Manager Role')
        db.session.add(manager_role)

    user_role = Role.query.filter_by(name='user').first()
    if not user_role:
        user_role = Role(name='user', description='Regular User Role')
        db.session.add(user_role)

    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        hashed_password = generate_password_hash('admin')
        admin_user = User(username='admin', email='admin@gmail.com', address="random", password=hashed_password ,fs_uniquifier='admin', active=True,is_approved=True)
        admin_user.roles.append(admin_role)
        db.session.add(admin_user)

    db.session.commit()
if __name__ == "__main__":
    app.run(debug=True)


