from flask import Blueprint
from flask_login import login_required
from app.controllers.auth_controller import (
    register_action,
    login_action,
    logout_action,
    profile_action
)

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    return register_action()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    return login_action()

@auth_bp.route('/logout')
@login_required
def logout():
    return logout_action()

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    return profile_action()
