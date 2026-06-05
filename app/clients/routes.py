from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.client import Client
from app.forms.client_forms import ClientForm
from app.utils.decorators import role_required
clients_bp = Blueprint('clients_bp', __name__, url_prefix='/clients')

@clients_bp.route('/', methods=['GET'])
@login_required
@role_required('Admin')
def list_clients():
    form = ClientForm()
    search_query = request.args.get('search', '').strip()
    query = Client.query.filter_by(company_id=current_user.company_id)
    if search_query:
        query = query.filter(db.or_(Client.client_name.ilike(f'%{search_query}%'),
                                    Client.company_name.ilike(f'%{search_query}%'),
                                    Client.email.ilike(f'%{search_query}%'),
                                    ))
    clients = query.order_by(Client.client_name.asc()).all()
    return render_template('clients/index.html', clients=clients, form=form, search_query=search_query)

@clients_bp.route('/add', methods=['POST'])
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
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
    return redirect(url_for('clients_bp.list_clients'))

@clients_bp.route('/<client_id>/delete', methods=['POST'])
@login_required
@role_required('Admin')
def delete_client(client_id):
    client = Client.query.filter_by(id=client_id, company_id=current_user.company_id).first_or_404()
    db.session.delete(client)
    db.session.commit()
    flash('Client deleted successfully!', 'success')
    return redirect(url_for('clients_bp.list_clients'))
