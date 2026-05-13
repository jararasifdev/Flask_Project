from datetime import datetime, timezone
from app import db
from app.models.base import generate_uuid

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.String(32), primary_key=True, default=generate_uuid)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    users = db.relationship('User', backref='role', lazy=True)
