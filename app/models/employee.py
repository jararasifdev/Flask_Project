from datetime import datetime, timezone
from app import db
from app.models.base import generate_uuid

class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.String(32), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(32), db.ForeignKey('users.id'), unique=True, nullable=False)
    company_id = db.Column(db.String(32), db.ForeignKey('company.id'), nullable=False)
    department_id = db.Column(db.String(32), db.ForeignKey('departments.id'), nullable=True)
    employee_code = db.Column(db.String(50), nullable=True)
    full_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    employment_type = db.Column(db.String(50), nullable=True)
    joining_date = db.Column(db.Date, nullable=True)
    hourly_rate = db.Column(db.Numeric(10, 2), nullable=True)
    monthly_salary = db.Column(db.Numeric(10, 2), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
