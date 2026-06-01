from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.client import Client
from app.forms.client_forms import ClientForm
from app.utils.decorators import role_required
clients_bp = Blueprint('clients_bp', __name__, url_prefix='/clients')

@clients_bp.route('/', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def add_client():
    form = ClientForm()
    if form.validate_on_submit():
        client = Client(
            company_id=current_user.company_id,
            client_name=form.client_name.data,
            company_name=form.company_name.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data
        )
        db.session.add(client)
        db.session.commit()
        flash('Client added successfully!', 'success')
        return redirect(url_for('clients_bp.add_client'))

    clients = Client.query.filter_by(company_id=current_user.company_id).all()
    return render_template('clients/index.html', clients=clients, form=form)

@clients_bp.route('/<client_id>/delete', methods=['POST'])
@login_required
@role_required('Admin')
def delete_client(client_id):
    client = Client.query.filter_by(id=client_id, company_id=current_user.company_id).first_or_404()
    db.session.delete(client)
    db.session.commit()
    flash('Client deleted successfully!', 'success')
    return redirect(url_for('clients_bp.add_client'))
