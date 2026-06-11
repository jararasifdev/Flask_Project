from flask import Blueprint
from flask_login import login_required
from app.controllers.notifications_controller import (
    get_unread_action,
    mark_read_action,
    list_notifications_action
)

notifications_bp = Blueprint('notifications_bp', __name__)

@notifications_bp.route('/api/notifications/unread', methods=['GET'])
@login_required
def get_unread():
    return get_unread_action()

@notifications_bp.route('/api/notifications/<notif_id>/read', methods=['POST'])
@login_required
def mark_read(notif_id):
    return mark_read_action(notif_id)

@notifications_bp.route('/notifications', methods=['GET'])
@login_required
def list_notifications():
    return list_notifications_action()
