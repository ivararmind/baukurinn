from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from flask_migrate import Migrate
import os



db = SQLAlchemy()
migrate = Migrate()  
DB_NAME = "database.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'hjshjhdjah kjshkjdhjs'
    DATABASE_URL = os.getenv("DATABASE_URL")

    # Fix Heroku's old-style `postgres://` URL format
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL   
    db.init_app(app)
    migrate.init_app(app, db)  




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
