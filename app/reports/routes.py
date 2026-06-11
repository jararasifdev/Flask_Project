from flask import Blueprint
from flask_login import login_required
from app.utils.decorators import role_required
from app.controllers.reports_controller import dashboard_action

reports_bp = Blueprint('reports_bp', __name__)

@reports_bp.route('/reports')
@login_required
@role_required('Admin', 'Accountant', 'Project Manager')
def dashboard():
    return dashboard_action()
