from flask import Blueprint
from flask_login import login_required
from app.utils.decorators import role_required
from app.controllers.invoices_controller import (
    list_invoices_action,
    create_invoice_action,
    view_invoice_action,
    update_invoice_status_action,
    add_item_action,
    add_payment_action,
    delete_invoice_action
)

invoices_bp = Blueprint('invoices_bp', __name__)

@invoices_bp.route('/invoices')
@login_required
@role_required('Admin', 'Accountant')
def list_invoices():
    return list_invoices_action()

@invoices_bp.route('/invoices/create', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Accountant')
def create_invoice():
    return create_invoice_action()

@invoices_bp.route('/invoices/<invoice_id>', methods=['GET'])
@login_required
@role_required('Admin', 'Accountant')
def view_invoice(invoice_id):
    return view_invoice_action(invoice_id)

@invoices_bp.route('/invoices/<invoice_id>/update_status', methods=['POST'])
@login_required
@role_required('Admin', 'Accountant')
def update_invoice_status(invoice_id):
    return update_invoice_status_action(invoice_id)

@invoices_bp.route('/invoices/<invoice_id>/add_item', methods=['POST'])
@login_required
@role_required('Admin', 'Accountant')
def add_item(invoice_id):
    return add_item_action(invoice_id)

@invoices_bp.route('/invoices/<invoice_id>/add_payment', methods=['POST'])
@login_required
@role_required('Admin', 'Accountant')
def add_payment(invoice_id):
    return add_payment_action(invoice_id)

@invoices_bp.route('/invoices/<invoice_id>/delete', methods=['POST'])
@login_required
@role_required('Admin', 'Accountant')
def delete_invoice(invoice_id):
    return delete_invoice_action(invoice_id)
