from flask import Blueprint
from flask_login import login_required
from app.utils.decorators import superadmin_required
from app.controllers.superadmin_controller import (
    login_action,
    dashboard_action,
    list_companies_action,
    toggle_company_status_action,
    delete_company_action,
    create_company_action,
    list_users_action
)

superadmin_bp = Blueprint('superadmin_bp', __name__)

@superadmin_bp.route('/superadmin/login', methods=['GET', 'POST'])
def login():
    return login_action()

@superadmin_bp.route('/superadmin')
@login_required
@superadmin_required
def dashboard():
    return dashboard_action()

@superadmin_bp.route('/superadmin/companies')
@login_required
@superadmin_required
def list_companies():
    return list_companies_action()

@superadmin_bp.route('/superadmin/companies/<company_id>/toggle_status', methods=['POST'])
@login_required
@superadmin_required
def toggle_company_status(company_id):
    return toggle_company_status_action(company_id)

@superadmin_bp.route('/superadmin/companies/<company_id>/delete', methods=['POST'])
@login_required
@superadmin_required
def delete_company(company_id):
    return delete_company_action(company_id)

@superadmin_bp.route('/superadmin/companies/create', methods=['GET', 'POST'])
@login_required
@superadmin_required
def create_company():
    return create_company_action()

@superadmin_bp.route('/superadmin/users')
@login_required
@superadmin_required
def list_users():
    return list_users_action()
