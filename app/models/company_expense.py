from datetime import datetime, timezone
from app import db
from app.models.base import generate_uuid

class CompanyExpense(db.Model):
    __tablename__ = 'company_expenses'
    id = db.Column(db.String(32), primary_key=True, default=generate_uuid)
    company_id = db.Column(db.String(32), db.ForeignKey('company.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    expense_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
