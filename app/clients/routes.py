from flask import Blueprint
from flask_login import login_required
from app.utils.decorators import role_required
from app.controllers.clients_controller import (
    list_clients_action,
    add_client_action,
    delete_client_action
)

clients_bp = Blueprint('clients_bp', __name__, url_prefix='/clients')

@clients_bp.route('/', methods=['GET'])
@login_required
@role_required('Admin')
def list_clients():
    return list_clients_action()

@clients_bp.route('/add', methods=['POST'])
@login_required
@role_required('Admin')
def add_client():
    return add_client_action()

@clients_bp.route('/<client_id>/delete', methods=['POST'])
@login_required
@role_required('Admin')
def delete_client(client_id):
    return delete_client_action(client_id)
