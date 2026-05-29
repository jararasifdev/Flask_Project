from datetime import datetime, timezone
from app import db
from app.models.base import generate_uuid

class EmployeeProject(db.Model):
    __tablename__ = 'employee_projects'
    id = db.Column(db.String(32), primary_key=True, default=generate_uuid)
    employee_id = db.Column(db.String(32), db.ForeignKey('employees.id'), nullable=False)
    project_id = db.Column(db.String(32), db.ForeignKey('projects.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    removed_at = db.Column(db.DateTime, nullable=True)

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.String(32), primary_key=True, default=generate_uuid)
    company_id = db.Column(db.String(32), db.ForeignKey('company.id'), nullable=False)
    client_id = db.Column(db.String(32), db.ForeignKey('clients.id'), nullable=False)
    project_manager_id = db.Column(db.String(32), db.ForeignKey('employees.id'), nullable=True)
    status = db.Column(db.String(50), default='In Progress')
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    budget = db.Column(db.Numeric(15, 2), nullable=False, default=0)
    start_date = db.Column(db.Date, nullable=True)
    estimated_end_date = db.Column(db.Date, nullable=True)
    actual_end_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    client = db.relationship('Client', backref='projects', lazy=True)
    project_manager = db.relationship('Employee', backref='managed_projects', lazy=True, foreign_keys=[project_manager_id])
    employees = db.relationship('Employee', secondary='employee_projects', backref='projects', lazy='dynamic')
