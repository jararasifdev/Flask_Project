from flask import current_app, render_template, redirect, url_for, flash, request
from flask_login import current_user
from app import db
from app.models.client import Client
from app.forms.client_forms import ClientForm

def list_clients_action():
    form = ClientForm()
    search_query = request.args.get('search', '').strip()
    query = Client.query.filter_by(company_id=current_user.company_id, is_active=True)
    if search_query:
        query = query.filter(db.or_(Client.client_name.ilike(f'%{search_query}%'),
                                    Client.company_name.ilike(f'%{search_query}%'),
                                    Client.email.ilike(f'%{search_query}%'),
                                    ))
    page = request.args.get('page', 1, type=int)
    pagination = query.order_by(Client.client_name.asc()).paginate(page=page, per_page=10, error_out=False)
    clients = pagination.items
    return render_template('clients/index.html', clients=clients, pagination=pagination, form=form, search_query=search_query)

def add_client_action():
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
        try:
            db.session.add(client)
            db.session.commit()
            flash('Client added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error adding client: {str(e)}')
            flash('Error adding client. Please try again.', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
    return redirect(url_for('clients_bp.list_clients'))

def delete_client_action(client_id):
    client = Client.query.filter_by(id=client_id, company_id=current_user.company_id).first_or_404()
    try:
        client.is_active = False
        db.session.commit()
        flash('Client deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting client: {str(e)}')
        flash('Error deleting client. Please try again.', 'danger')
    return redirect(url_for('clients_bp.list_clients'))
