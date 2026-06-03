from datetime import datetime, timezone
from app import db
from app.models.base import generate_uuid

class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.String(32), primary_key=True, default=generate_uuid)
    company_id = db.Column(db.String(32), db.ForeignKey('company.id'), nullable=False)
    project_id = db.Column(db.String(32), db.ForeignKey('projects.id'), nullable=True)
    client_id = db.Column(db.String(32), db.ForeignKey('clients.id'), nullable=False)
    status = db.Column(db.String(50), default='Draft')
    invoice_number = db.Column(db.String(100), nullable=False)
    issue_date = db.Column(db.Date, nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    subtotal = db.Column(db.Numeric(12, 2), default=0.00)
    tax_amount = db.Column(db.Numeric(12, 2), default=0.00)
    total_amount = db.Column(db.Numeric(12, 2), default=0.00)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    project = db.relationship('Project', backref='invoices')
    client = db.relationship('Client', backref='invoices')
    items = db.relationship('InvoiceItem', backref='invoice', lazy=True, cascade="all, delete-orphan")
    payments = db.relationship('Payment', backref='invoice', lazy=True, cascade="all, delete-orphan")

class InvoiceItem(db.Model):
    __tablename__ = 'invoice_items'
    id = db.Column(db.String(32), primary_key=True, default=generate_uuid)
    invoice_id = db.Column(db.String(32), db.ForeignKey('invoices.id'), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), default=1.00)
    rate = db.Column(db.Numeric(12, 2), default=0.00)
    amount = db.Column(db.Numeric(12, 2), default=0.00)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.String(32), primary_key=True, default=generate_uuid)
    invoice_id = db.Column(db.String(32), db.ForeignKey('invoices.id'), nullable=False)
    payment_date = db.Column(db.Date, nullable=True)
    amount_paid = db.Column(db.Numeric(12, 2), nullable=False)
    payment_method = db.Column(db.String(100), nullable=True)
    reference_number = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
