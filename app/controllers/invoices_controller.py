from flask import current_app, render_template, redirect, url_for, flash, request
from flask_login import current_user
from app import db
from app.models import Invoice, InvoiceItem, Payment, Client, Project, Expense
from app.forms import InvoiceForm, InvoiceItemForm, PaymentForm, InvoiceStatusForm
from datetime import datetime
from sqlalchemy import func

def list_invoices_action():
    status_filter = request.args.get('status')
    client_filter = request.args.get('client_id')

    query = Invoice.query.filter_by(company_id=current_user.company_id)
    clients = Client.query.filter_by(company_id=current_user.company_id).all()

    if status_filter:
        if status_filter == 'Unpaid':
            query = query.filter(Invoice.status != 'Paid')
        else:
            query = query.filter(Invoice.status == status_filter)
    if client_filter:
        query = query.filter(Invoice.client_id == client_filter)

    page = request.args.get('page', 1, type=int)
    pagination = query.order_by(Invoice.issue_date.desc()).paginate(page=page, per_page=10, error_out=False)
    invoices = pagination.items
    return render_template('invoices/index.html', invoices=invoices, pagination=pagination, clients=clients, current_status=status_filter, current_client=client_filter, title='Invoices')

def create_invoice_action():
    form = InvoiceForm()
    
    clients = Client.query.filter_by(company_id=current_user.company_id).all()
    form.client_id.choices = [(c.id, c.client_name) for c in clients]
    
    projects = Project.query.filter_by(company_id=current_user.company_id).all()
    form.project_id.choices = [('', 'Select Project (Optional)')] + [(p.id, p.name) for p in projects]
    
    if form.validate_on_submit():
        existing_invoice = Invoice.query.filter_by(
            company_id=current_user.company_id,
            invoice_number=form.invoice_number.data
        ).first()

        if existing_invoice:
            flash(f"Invoice number '{form.invoice_number.data}' already exists. Please enter a different invoice number.", 'danger')
            return render_template('invoices/create.html', form=form, title='Create Invoice')

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
        
        try:
            db.session.commit()
            flash('Invoice created successfully.', 'success')
            return redirect(url_for('invoices_bp.view_invoice', invoice_id=invoice.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error creating invoice: {str(e)}')
            flash('Error creating invoice. Please try again.', 'danger')
        
    return render_template('invoices/create.html', form=form, title='Create Invoice')

def view_invoice_action(invoice_id):
    invoice = Invoice.query.filter_by(id=invoice_id, company_id=current_user.company_id).first_or_404()
    item_form = InvoiceItemForm()
    payment_form = PaymentForm()
    status_form = InvoiceStatusForm(status=invoice.status)
    return render_template('invoices/view.html', invoice=invoice, item_form=item_form, payment_form=payment_form, status_form=status_form, title=f'Invoice {invoice.invoice_number}')

def update_invoice_status_action(invoice_id):
    invoice = Invoice.query.filter_by(id=invoice_id, company_id=current_user.company_id).first_or_404()
    form = InvoiceStatusForm()
    if form.validate_on_submit():
        invoice.status = form.status.data
        try:
            db.session.commit()
            flash('Invoice status updated successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating invoice status: {str(e)}')
            flash('Error updating invoice status. Please try again.', 'danger')
    return redirect(url_for('invoices_bp.view_invoice', invoice_id=invoice.id))

def add_item_action(invoice_id):
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
        try:
            db.session.commit()
            flash('Item added successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error adding invoice item: {str(e)}')
            flash('Error adding item. Please try again.', 'danger')
    return redirect(url_for('invoices_bp.view_invoice', invoice_id=invoice.id))

def add_payment_action(invoice_id):
    invoice = Invoice.query.filter_by(id=invoice_id, company_id=current_user.company_id).first_or_404()
    form = PaymentForm()
    if form.validate_on_submit():
        existing_payment = Payment.query.filter_by(
            invoice_id=invoice.id,
            reference_number=form.reference_number.data
        ).first()

        if existing_payment:
            flash(f"Reference number '{form.reference_number.data}' already exists. Please enter a different reference number.", 'danger')
            return redirect(url_for('invoices_bp.view_invoice', invoice_id=invoice.id))
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
            
        try:
            db.session.commit()
            flash('Payment recorded successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error recording payment: {str(e)}')
            flash('Error recording payment. Please try again.', 'danger')
    return redirect(url_for('invoices_bp.view_invoice', invoice_id=invoice.id))

def delete_invoice_action(invoice_id):
    invoice = Invoice.query.filter_by(id=invoice_id, company_id=current_user.company_id,status='Draft').first_or_404()
    try:
        expenses = Expense.query.filter_by(invoice_id=invoice.id).all()
        for expense in expenses:
            expense.is_invoiced = False
            expense.invoice_id = None
            
        db.session.delete(invoice)
        db.session.commit()
        flash('Invoice deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting invoice: {str(e)}')
        flash('Error deleting invoice. Please try again.', 'danger')
    return redirect(url_for('invoices_bp.list_invoices'))
