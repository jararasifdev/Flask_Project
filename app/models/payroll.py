from datetime import datetime, timezone
from app import db
from app.models.base import generate_uuid

class PayrollRun(db.Model):
    __tablename__ = 'payroll_runs'
    id = db.Column(db.String(32), primary_key=True, default=generate_uuid)
    company_id = db.Column(db.String(32), db.ForeignKey('company.id'), nullable=False)
    status = db.Column(db.String(50), default='Draft')
    payroll_month = db.Column(db.Date, nullable=False)
    generated_by_employee_id = db.Column(db.String(32), db.ForeignKey('employees.id'), nullable=True)
    generated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    generated_by = db.relationship('Employee', foreign_keys=[generated_by_employee_id])
    payroll_items = db.relationship('PayrollItem', backref='payroll_run', lazy=True, cascade="all, delete-orphan")

class PayrollItem(db.Model):
    __tablename__ = 'payroll_items'
    id = db.Column(db.String(32), primary_key=True, default=generate_uuid)
    payroll_run_id = db.Column(db.String(32), db.ForeignKey('payroll_runs.id'), nullable=False)
    employee_id = db.Column(db.String(32), db.ForeignKey('employees.id'), nullable=False)
    status = db.Column(db.String(50), default='Pending')
    base_salary = db.Column(db.Numeric(12, 2), default=0.00)
    overtime_amount = db.Column(db.Numeric(12, 2), default=0.00)
    bonus_amount = db.Column(db.Numeric(12, 2), default=0.00)
    deductions = db.Column(db.Numeric(12, 2), default=0.00)
    net_salary = db.Column(db.Numeric(12, 2), default=0.00)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    employee = db.relationship('Employee', backref='payroll_items')
