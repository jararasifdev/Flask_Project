from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Notification

notifications_bp = Blueprint('notifications_bp', __name__)

@notifications_bp.route('/api/notifications/unread', methods=['GET'])
@login_required
def get_unread():
    notifications = Notification.query.filter_by(
        user_id=current_user.id, 
        is_read=False
    ).order_by(Notification.created_at.desc()).all()
    
    data = []
    for notif in notifications:
        data.append({
            'id': notif.id,
            'title': notif.title,
            'message': notif.message,
            'type': notif.type.name if notif.type else 'Notification',
            'created_at': notif.created_at.strftime("%Y-%m-%d %H:%M")
        })
    return jsonify({'notifications': data, 'count': len(data)})

@notifications_bp.route('/api/notifications/<notif_id>/read', methods=['POST'])
@login_required
def mark_read(notif_id):
    if notif_id == 'all':
        notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
        for notif in notifications:
            notif.is_read = True
    else:
        notif = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first()
        if notif:
            notif.is_read = True
            
    db.session.commit()
    return jsonify({'success': True})
