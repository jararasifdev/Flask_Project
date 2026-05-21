from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from app.config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth_bp.login'
login_manager.login_message_category = 'info'
bcrypt = Bcrypt()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)

    from app.auth.routes import auth_bp
    from app.dashboard.routes import dashboard_bp
    from app.employees.routes import employees_bp
    from app.departments.routes import departments_bp


    app.register_blueprint(dashboard_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(departments_bp)
    app.register_blueprint(auth_bp)

    return app
