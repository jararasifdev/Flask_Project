from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Invoice, InvoiceItem, Payment, Client, Project
from app.forms import InvoiceForm, InvoiceItemForm, PaymentForm, InvoiceStatusForm
from app.utils.decorators import role_required
from datetime import datetime
from sqlalchemy import func

invoices_bp = Blueprint('invoices_bp', __name__)

@invoices_bp.route('/invoices')
@login_required
@role_required('Admin', 'Accountant', 'Project Manager')
def list_invoices():
    status_filter = request.args.get('status')
    client_filter = request.args.get('client_id')

    query = Invoice.query.filter_by(company_id=current_user.company_id)
    clients = Client.query.filter_by(company_id=current_user.company_id).all()

    if status_filter:
        query = query.filter(Invoice.status == status_filter)
    if client_filter:
        query = query.filter(Invoice.client_id == client_filter)

    invoices = query.order_by(Invoice.issue_date.desc()).all()
    return render_template('invoices/index.html', invoices=invoices, clients=clients, current_status=status_filter, current_client=client_filter, title='Invoices')

@invoices_bp.route('/invoices/create', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Accountant', 'Project Manager')
def create_invoice():
    form = InvoiceForm()
    
    clients = Client.query.filter_by(company_id=current_user.company_id).all()
    form.client_id.choices = [(c.id, c.client_name) for c in clients]
    
    projects = Project.query.filter_by(company_id=current_user.company_id).all()
    form.project_id.choices = [('', 'Select Project (Optional)')] + [(p.id, p.name) for p in projects]
    
    if form.validate_on_submit():
        invoice = Invoice(
            company_id=current_user.company_id,
            client_id=form.client_id.data,
            project_id=form.project_id.data or None,
            invoice_number=form.invoice_number.data,
            issue_date=form.issue_date.data,
            due_date=form.due_date.data,
            status=form.status.data,
            notes=form.notes.data
        )
        db.session.add(invoice)
        db.session.flush()
        
        descriptions = request.form.getlist('item_description[]')
        quantities = request.form.getlist('item_quantity[]')
        rates = request.form.getlist('item_rate[]')
        
        subtotal = 0
        for i in range(len(descriptions)):
            desc = descriptions[i].strip()
            if not desc:
                continue
            try:
                qty = float(quantities[i])
                rate = float(rates[i])
                amount = qty * rate
                subtotal += amount
                
                item = InvoiceItem(
                    invoice_id=invoice.id,
                    description=desc,
                    quantity=qty,
                    rate=rate,
                    amount=amount
                )
                db.session.add(item)
            except (ValueError, IndexError):
                pass
                
        invoice.subtotal = subtotal
        invoice.total_amount = subtotal + invoice.tax_amount
        
        db.session.commit()
        flash('Invoice created successfully.', 'success')
        return redirect(url_for('invoices_bp.view_invoice', invoice_id=invoice.id))
        
    return render_template('invoices/create.html', form=form, title='Create Invoice')

@invoices_bp.route('/invoices/<invoice_id>', methods=['GET'])
@login_required
@role_required('Admin', 'Accountant', 'Project Manager')
def view_invoice(invoice_id):
    invoice = Invoice.query.filter_by(id=invoice_id, company_id=current_user.company_id).first_or_404()
    item_form = InvoiceItemForm()
    payment_form = PaymentForm()
    status_form = InvoiceStatusForm(status=invoice.status)
    return render_template('invoices/view.html', invoice=invoice, item_form=item_form, payment_form=payment_form, status_form=status_form, title=f'Invoice {invoice.invoice_number}')

@invoices_bp.route('/invoices/<invoice_id>/update_status', methods=['POST'])
@login_required
@role_required('Admin', 'Accountant', 'Project Manager')
def update_invoice_status(invoice_id):
    invoice = Invoice.query.filter_by(id=invoice_id, company_id=current_user.company_id).first_or_404()
    form = InvoiceStatusForm()
    if form.validate_on_submit():
        invoice.status = form.status.data
        db.session.commit()
        flash('Invoice status updated successfully.', 'success')
    return redirect(url_for('invoices_bp.view_invoice', invoice_id=invoice.id))

@invoices_bp.route('/invoices/<invoice_id>/add_item', methods=['POST'])
@login_required
@role_required('Admin', 'Accountant', 'Project Manager')
def add_item(invoice_id):
    invoice = Invoice.query.filter_by(id=invoice_id, company_id=current_user.company_id).first_or_404()
    form = InvoiceItemForm()
    if form.validate_on_submit():
        amount = form.quantity.data * form.rate.data
        item = InvoiceItem(
            invoice_id=invoice.id,
            description=form.description.data,
            quantity=form.quantity.data,
            rate=form.rate.data,
            amount=amount
        )
        db.session.add(item)

        invoice.subtotal += amount
        invoice.total_amount = invoice.subtotal + invoice.tax_amount
        db.session.commit()
        
        flash('Item added successfully.', 'success')
    return redirect(url_for('invoices_bp.view_invoice', invoice_id=invoice.id))

@invoices_bp.route('/invoices/<invoice_id>/add_payment', methods=['POST'])
@login_required
@role_required('Admin', 'Accountant', 'Project Manager')
def add_payment(invoice_id):
    invoice = Invoice.query.filter_by(id=invoice_id, company_id=current_user.company_id).first_or_404()
    form = PaymentForm()
    if form.validate_on_submit():
        payment = Payment(
            invoice_id=invoice.id,
            payment_date=form.payment_date.data,
            amount_paid=form.amount_paid.data,
            payment_method=form.payment_method.data,
            reference_number=form.reference_number.data
        )
        db.session.add(payment)
        db.session.flush()

        total_paid = db.session.query(func.sum(Payment.amount_paid)).filter_by(invoice_id=invoice.id).scalar() or 0
        
        if total_paid >= invoice.total_amount and invoice.total_amount > 0:
            invoice.status = 'Paid'
        else:
            if invoice.due_date and invoice.due_date < datetime.utcnow().date():
                invoice.status = 'Overdue'
            else:
                invoice.status = 'Partial'
            
        db.session.commit()
        flash('Payment recorded successfully.', 'success')
    return redirect(url_for('invoices_bp.view_invoice', invoice_id=invoice.id))
