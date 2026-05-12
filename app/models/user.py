from datetime import datetime, timezone
from flask_login import UserMixin
from app import db, login_manager
from app.models.base import generate_uuid

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.String(32), primary_key=True, default=generate_uuid)
    company_id = db.Column(db.String(32), db.ForeignKey('company.id'), nullable=False)
    role_id = db.Column(db.String(32), db.ForeignKey('roles.id'), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    last_login_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    employee = db.relationship('Employee', backref='user', uselist=False, lazy=True)
