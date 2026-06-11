from flask import Blueprint
from flask_login import login_required
from app.utils.decorators import role_required
from app.controllers.time_tracking_controller import (
    list_timesheets_action,
    log_time_action,
    review_timesheet_action,
    view_timesheet_action,
    approve_all_action
)

time_tracking_bp = Blueprint('time_tracking_bp', __name__)

@time_tracking_bp.route('/timesheets')
@login_required
def list_timesheets():
    return list_timesheets_action()

@time_tracking_bp.route('/timesheets/log', methods=['GET', 'POST'])
@login_required
def log_time():
    return log_time_action()

@time_tracking_bp.route('/timesheets/<timesheet_id>/review', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Project Manager')
def review_timesheet(timesheet_id):
    return review_timesheet_action(timesheet_id)

@time_tracking_bp.route('/timesheets/<timesheet_id>/view', methods=['GET'])
@login_required
def view_timesheet(timesheet_id):
    return view_timesheet_action(timesheet_id)

@time_tracking_bp.route('/timesheets/approve_all', methods=['POST'])
@login_required
@role_required('Admin', 'Project Manager')
def approve_all():
    return approve_all_action()
