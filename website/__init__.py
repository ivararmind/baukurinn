import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()

def create_app():
    app = Flask(__name__)

    # Secret key for session security
    app.config['SECRET_KEY'] = 'hjshjhdjah kjshkjdhjs'

    # Use Heroku's DATABASE_URL if available, otherwise fallback to SQLite for local development
    database_url = os.getenv('DATABASE_URL', 'sqlite:///database.db')

    # Fix Heroku's "postgres://" URL format to "postgresql://"
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    # Database Configuration

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///database.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize database and migrations
    db.init_app(app)
    migrate.init_app(app, db)

    # Email Configuration
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_USERNAME'] = 'ivararmind@gmail.com'
    app.config['MAIL_PASSWORD'] = 'sbzc hfuy glqy xdvw'
    mail.init_app(app)

    # Custom Jinja filter for formatting numbers
    @app.template_filter('format_thousands')
    def format_thousands(value):
        try:
            value = float(value)
            formatted_value = '{:,.2f}'.format(value).replace(",", "X").replace(".", ",").replace("X", ".")
            return formatted_value[:-3] if formatted_value.endswith(",00") else formatted_value
        except (ValueError, TypeError):
            return value

    # Import and register blueprints (routes)
    from .views import views
    from .auth import auth
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    # Import models
    from .models import User, Log

    # Ensure tables are created
    with app.app_context():
        db.create_all()

    # User authentication setup
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app
