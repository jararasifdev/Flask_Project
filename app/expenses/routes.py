from flask import Blueprint
from flask_login import login_required
from app.utils.decorators import role_required
from app.controllers.expenses_controller import (
    list_company_expenses_action,
    list_expenses_action,
    submit_expense_action,
    review_expense_action,
    manage_categories_action
)

expenses_bp = Blueprint('expenses_bp', __name__, url_prefix='/expenses')

@expenses_bp.route('/company', methods=['GET'])
@login_required
@role_required('Admin', 'Accountant')
def list_company_expenses():
    return list_company_expenses_action()

@expenses_bp.route('/', methods=['GET'])
@login_required
def list_expenses():
    return list_expenses_action()

@expenses_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_expense():
    return submit_expense_action()

@expenses_bp.route('/<expense_id>/review', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Project Manager', 'Accountant')
def review_expense(expense_id):
    return review_expense_action(expense_id)

@expenses_bp.route('/categories', methods=['GET', 'POST'])
@login_required
def manage_categories():
    return manage_categories_action()
