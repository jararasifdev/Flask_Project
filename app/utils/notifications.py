from app import db
from app.models import Notification, NotificationType

def create_notification(company_id, user_id, type_name, title, message=None):
    notification_type = NotificationType.query.filter_by(name=type_name).first()
    if not notification_type:
        notification_type = NotificationType(name=type_name)
        db.session.add(notification_type)
        db.session.flush()

    notif = Notification(
        company_id=company_id,
        user_id=user_id,
        notification_type_id=notification_type.id,
        title=title,
        message=message
    )
    db.session.add(notif)
