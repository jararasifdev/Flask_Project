from flask import Blueprint
from flask_login import login_required
from app.utils.decorators import role_required
from app.controllers.employees_controller import (
    list_employees_action,
    create_employee_action,
    edit_employee_action,
    delete_employee_action
)

employees_bp = Blueprint('employees_bp', __name__)

@employees_bp.route('/employees')
@login_required
@role_required('Admin')
def list_employees():
    return list_employees_action()

@employees_bp.route('/employees/create', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def create_employee():
    return create_employee_action()

@employees_bp.route('/employees/<employee_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def edit_employee(employee_id):
    return edit_employee_action(employee_id)

@employees_bp.route('/employees/<employee_id>/delete', methods=['POST'])
@login_required
@role_required('Admin')
def delete_employee(employee_id):
    return delete_employee_action(employee_id)
