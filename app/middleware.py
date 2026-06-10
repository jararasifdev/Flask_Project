import time
from flask import request, g, flash, redirect, url_for
from flask_login import current_user, logout_user

def setup_middleware(app):
    @app.before_request
    def before_request():
        g.start = time.time()
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        print(f"[{time.strftime('%H:%M:%S')}] ---> START {request.method} {request.path} (IP: {ip})")
        
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
