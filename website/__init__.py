from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from dotenv import load_dotenv



mail = Mail() 

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()  
DB_NAME = "database.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'hjshjhdjah kjshkjdhjs'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    db.init_app(app)
    migrate.init_app(app, db)  


    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_USERNAME'] = 'ivararmind@gmail.com'
    app.config['MAIL_PASSWORD'] = 'sbzc hfuy glqy xdvw'
    mail.init_app(app)  # Initialize Mail with app here



    @app.template_filter('format_thousands')
    def format_thousands(value):
        try:
            value = float(value)
            formatted_value = '{:,.2f}'.format(value).replace(",", "X").replace(".", ",").replace("X", ".")

            if formatted_value.endswith(",00"):
                formatted_value = formatted_value[:-3] 

            return formatted_value
        except (ValueError, TypeError):
            return value


    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, Log
    
    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    

    return app