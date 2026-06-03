from datetime import datetime, timezone
from app import db
from app.models.base import generate_uuid

class Timesheet(db.Model):
    __tablename__ = 'timesheets'
    id = db.Column(db.String(32), primary_key=True, default=generate_uuid)
    company_id = db.Column(db.String(32), db.ForeignKey('company.id'), nullable=False)
    employee_id = db.Column(db.String(32), db.ForeignKey('employees.id'), nullable=False)
    project_id = db.Column(db.String(32), db.ForeignKey('projects.id'), nullable=False)
    approved_by_employee_id = db.Column(db.String(32), db.ForeignKey('employees.id'), nullable=True)
    status = db.Column(db.String(50), default='Pending')
    work_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    total_hours = db.Column(db.Numeric(5, 2), nullable=False)
    is_billable = db.Column(db.Boolean, default=True)
    task_description = db.Column(db.Text, nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    employee = db.relationship('Employee', foreign_keys=[employee_id], backref='timesheets')
    project = db.relationship('Project', backref='timesheets')
    approved_by = db.relationship('Employee', foreign_keys=[approved_by_employee_id])
