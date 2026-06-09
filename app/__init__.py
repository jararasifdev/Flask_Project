from flask import Flask, request, g
import time
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

    from app.scheduler import init_scheduler
    init_scheduler(app)
    
    from app.auth.routes import auth_bp
    from app.dashboard.routes import dashboard_bp
    from app.employees.routes import employees_bp
    from app.departments.routes import departments_bp
    from app.clients.routes import clients_bp
    from app.projects.routes import projects_bp
    from app.expenses.routes import expenses_bp
    from app.invoices.routes import invoices_bp
    from app.reports.routes import reports_bp
    from app.payroll.routes import payroll_bp
    from app.time_tracking.routes import time_tracking_bp
    from app.notifications.routes import notifications_bp

    from app.superadmin.routes import superadmin_bp
    
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
    app.register_blueprint(payroll_bp)
    app.register_blueprint(superadmin_bp)

    @app.before_request
    def before_request():
        g.start = time.time()
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        print(f"[{time.strftime('%H:%M:%S')}] ---> START {request.method} {request.path} (IP: {ip})")

        from flask_login import current_user, logout_user
        from flask import flash, redirect, url_for
        
        if current_user.is_authenticated:
            if not current_user.is_superadmin:
                if not current_user.company or not current_user.company.is_active:
                    logout_user()
                    flash('Your company account has been suspended.', 'danger')
                    return redirect(url_for('auth_bp.login'))

            if current_user.is_superadmin:
                if request.blueprint and request.blueprint not in ['superadmin_bp', 'auth_bp'] and not request.path.startswith('/static/'):
                    flash('Super Administrators are restricted to the Platform Admin portal.', 'warning')
                    return redirect(url_for('superadmin_bp.dashboard'))

        if request.args:
            print(f"  | Args: {dict(request.args)}")
        if request.form:
            safe_form = {k: ('***' if 'password' in k.lower() else v) for k, v in request.form.items()}
            print(f"  | Form: {safe_form}")
        if request.is_json:
            print(f"  | JSON: {request.get_json(silent=True)}")

    @app.after_request
    def after_request(response):
        if hasattr(g, 'start'):
            duration = time.time() - g.start
            print(f"[{time.strftime('%H:%M:%S')}] <--- END {request.method} {request.path} | Status: {response.status_code} | Time: {duration:.4f}s")
        return response

    return app
