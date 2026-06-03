from datetime import datetime, timezone
from app import db
from app.models.base import generate_uuid

class FinancialReport(db.Model):
    __tablename__ = 'financial_reports'
    id = db.Column(db.String(32), primary_key=True, default=generate_uuid)
    company_id = db.Column(db.String(32), db.ForeignKey('company.id'), nullable=False)
    report_type = db.Column(db.String(100), nullable=True)
    generated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    file_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
