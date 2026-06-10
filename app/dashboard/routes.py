from flask import Blueprint
from flask_login import login_required
from app.controllers.dashboard_controller import dashboard_action

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    return dashboard_action()
