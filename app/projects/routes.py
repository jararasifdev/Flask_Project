from flask import Blueprint
from flask_login import login_required
from app.controllers.projects_controller import (
    create_project_action,
    view_project_action,
    assign_project_action,
    remove_project_employee_action,
    change_project_status_action
)

projects_bp = Blueprint('projects_bp', __name__, url_prefix='/projects')

@projects_bp.route('/', methods=['GET', 'POST'])
@login_required
def create_project():
    return create_project_action()

@projects_bp.route('/<project_id>', methods=['GET'])
@login_required
def view_project(project_id):
    return view_project_action(project_id)

@projects_bp.route('/<project_id>/assign', methods=['POST'])
@login_required
def assign_project(project_id):
    return assign_project_action(project_id)

@projects_bp.route('/<project_id>/remove/<employee_id>', methods=['POST'])
@login_required
def remove_project_employee(project_id, employee_id):
    return remove_project_employee_action(project_id, employee_id)

@projects_bp.route('/<project_id>/status', methods=['POST'])
@login_required
def change_project_status(project_id):
    return change_project_status_action(project_id)
