from datetime import datetime, timezone
from app import db
from app.models.base import generate_uuid

class Company(db.Model):
    __tablename__ = 'company'
    id = db.Column(db.String(32), primary_key=True, default=generate_uuid)
    company_name = db.Column(db.String(255), nullable=False)
    registration_no = db.Column(db.String(100), nullable=True)
    tax_id = db.Column(db.String(100), nullable=True)
    address = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    users = db.relationship('User', backref='company', lazy=True)
    departments = db.relationship('Department', backref='company', lazy=True)
    employees = db.relationship('Employee', backref='company', lazy=True)
    clients = db.relationship('Client', backref='company', lazy=True)
    projects = db.relationship('Project', backref='company', lazy=True)
    expense_categories = db.relationship('ExpenseCategory', backref='company', lazy=True)
    expenses = db.relationship('Expense', backref='company', lazy=True)
    budget_alerts = db.relationship('BudgetAlert', backref='company', lazy=True)
