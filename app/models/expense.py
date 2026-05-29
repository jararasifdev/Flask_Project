from datetime import datetime, timezone
from app import db
from app.models.base import generate_uuid

class ExpenseCategory(db.Model):
    __tablename__ = 'expense_categories'
    id = db.Column(db.String(32), primary_key=True, default=generate_uuid)
    company_id = db.Column(db.String(32), db.ForeignKey('company.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.String(32), primary_key=True, default=generate_uuid)
    company_id = db.Column(db.String(32), db.ForeignKey('company.id'), nullable=False)
    project_id = db.Column(db.String(32), db.ForeignKey('projects.id'), nullable=False)
    employee_id = db.Column(db.String(32), db.ForeignKey('employees.id'), nullable=False)
    category_id = db.Column(db.String(32), db.ForeignKey('expense_categories.id'), nullable=False)
    approved_by_employee_id = db.Column(db.String(32), db.ForeignKey('employees.id'), nullable=True)
    status = db.Column(db.String(50), default='Pending')
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.Text, nullable=True)
    receipt_file = db.Column(db.String(255), nullable=True)
    submitted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    approved_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    project = db.relationship('Project', backref='expenses', lazy=True)
    employee = db.relationship('Employee', backref='submitted_expenses', lazy=True, foreign_keys=[employee_id])
    category = db.relationship('ExpenseCategory', backref='expenses', lazy=True)
    approved_by = db.relationship('Employee', backref='approved_expenses', lazy=True, foreign_keys=[approved_by_employee_id])

class BudgetAlert(db.Model):
    __tablename__ = 'budget_alerts'
    id = db.Column(db.String(32), primary_key=True, default=generate_uuid)
    company_id = db.Column(db.String(32), db.ForeignKey('company.id'), nullable=False)
    project_id = db.Column(db.String(32), db.ForeignKey('projects.id'), nullable=False)
    alert_type = db.Column(db.String(100), nullable=True)
    message = db.Column(db.Text, nullable=True)
    triggered_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    project = db.relationship('Project', backref='budget_alerts', lazy=True)
