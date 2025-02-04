from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from dotenv import load_dotenv

# Load environment variables from a .env file (if present)
load_dotenv()

mail = Mail()
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    # Set your secret key (you can also store this in the .env file)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'hjshjhdjah kjshkjdhjs')
    
    # Retrieve the DATABASE_URL from the environment.
    # This should be set in your Heroku config, or for local development,
    # you can define it in a .env file in the root of your project.
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL is not set. Please set it in your environment or in your .env file.")
    
    # If using Heroku Postgres, the URL may begin with 'postgres://'
    # SQLAlchemy expects it to begin with 'postgresql://'
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Configure Mail using environment variables (set these in your .env file or Heroku config)
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 465))
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'True') == 'True'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    mail.init_app(app)
    
    # Example custom template filter
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
    
    # Register blueprints
    from .views import views
    from .auth import auth
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    
    # Import models and create tables if they don't exist
    from .models import User, Log
    with app.app_context():
        db.create_all()
    
    # Configure Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    return app
