from flask import Blueprint, request
from flask_login import login_required
from app.utils.decorators import role_required
from app.controllers.departments_controller import (
    list_departments_action,
    create_department_action,
    view_department_action,
    assign_employee_action,
    remove_employee_from_department_action,
    delete_department_action
)

departments_bp = Blueprint('departments_bp', __name__)

@departments_bp.route('/departments')
@login_required
@role_required('Admin')
def list_departments():
    return list_departments_action()

@departments_bp.route('/departments/create', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def create_department():
    return create_department_action()

@departments_bp.route('/departments/<department_id>/view', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def view_department(department_id):
    return view_department_action(department_id)

@departments_bp.route('/departments/<department_id>/assign', methods=['POST'])
@login_required
@role_required('Admin')
def assign_employee(department_id):
    return assign_employee_action(department_id)

@departments_bp.route('/departments/<department_id>/remove_employee/<employee_id>', methods=['POST'])
@login_required
@role_required('Admin')
def remove_employee_from_department(department_id, employee_id):
    return remove_employee_from_department_action(department_id, employee_id)

@departments_bp.route('/departments/<department_id>/delete', methods=['POST'])
@login_required
@role_required('Admin')
def delete_department(department_id):
    return delete_department_action(department_id)
