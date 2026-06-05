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
    from app.clients.routes import clients_bp
    from app.projects.routes import projects_bp
    from app.expenses.routes import expenses_bp
    from app.invoices.routes import invoices_bp
    from app.reports.routes import reports_bp
    from app.time_tracking.routes import time_tracking_bp
    from app.notifications.routes import notifications_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(departments_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(time_tracking_bp)
    app.register_blueprint(notifications_bp)

    return app
