from flask import jsonify, render_template
from flask_login import current_user
from app import db
from app.models import Notification

def get_unread_action():
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

def mark_read_action(notif_id):
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

def list_notifications_action():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template('notifications/index.html', notifications=notifications, title='All Notifications')
