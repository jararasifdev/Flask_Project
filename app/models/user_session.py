from datetime import datetime, timezone
from app import db
from app.models.base import generate_uuid

class UserSession(db.Model):
    __tablename__ = 'user_sessions'
    id = db.Column(db.String(32), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(32), db.ForeignKey('users.id'), nullable=False)
    session_token = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(100), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_activity = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = db.relationship('User', backref='sessions', lazy=True)
