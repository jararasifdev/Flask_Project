from flask import Blueprint
from flask_login import login_required
from app.utils.decorators import role_required
from app.controllers.payroll_controller import (
    list_runs_action,
    generate_payroll_action,
    view_run_action,
    edit_item_action,
    approve_run_action
)

payroll_bp = Blueprint('payroll_bp', __name__)

@payroll_bp.route('/payroll', methods=['GET'])
@login_required
@role_required('Admin', 'Accountant')
def list_runs():
    return list_runs_action()

@payroll_bp.route('/payroll/generate', methods=['POST'])
@login_required
@role_required('Admin', 'Accountant')
def generate_payroll():
    return generate_payroll_action()

@payroll_bp.route('/payroll/<run_id>', methods=['GET'])
@login_required
@role_required('Admin', 'Accountant')
def view_run(run_id):
    return view_run_action(run_id)

@payroll_bp.route('/payroll/item/<item_id>', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Accountant')
def edit_item(item_id):
    return edit_item_action(item_id)

@payroll_bp.route('/payroll/<run_id>/approve', methods=['POST'])
@login_required
@role_required('Admin', 'Accountant')
def approve_run(run_id):
    return approve_run_action(run_id)
