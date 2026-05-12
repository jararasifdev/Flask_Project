from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, current_user, logout_user, login_required
from app import db, bcrypt
from app.models import User, Company, Employee, Role, UserSession
from app.forms import RegistrationForm, LoginForm, UpdateProfileForm
import datetime
import uuid
from sqlalchemy.exc import IntegrityError,SQLAlchemyError

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_bp.dashboard'))

    if request.args.get('secret') != 'admin_setup':
        return redirect(url_for('auth_bp.login'))

    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            existing_user = User.query.filter_by(email=form.email.data).first()
            if existing_user:
                flash('Email already registered.', 'danger')
                return render_template('auth/register.html', title='Register', form=form)
            admin_role = Role.query.filter_by(name='Admin').first()
            if not admin_role:
                admin_role = Role(name='Admin', description='Full system management')
                db.session.add(admin_role)
                db.session.commit()

            company = Company(company_name=form.company_name.data)
            db.session.add(company)
            db.session.flush()

            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

            user = User(
                company_id=company.id,
                role_id=admin_role.id,
                email=form.email.data,
                password_hash=hashed_password
            )
            db.session.add(user)
            db.session.flush()

            employee = Employee(
                user_id=user.id,
                company_id=company.id,
                full_name=form.full_name.data
            )
            db.session.add(employee)
            db.session.commit()

            flash('Your account has been created! You can now log in.', 'success')
            return redirect(url_for('auth_bp.login'))
        except IntegrityError:
            db.session.rollback()
            flash('A database integrity error occurred.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash('Something went wrong. Please try again.', 'danger')
    return render_template('auth/register.html', title='Register', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_bp.dashboard'))

    form = LoginForm()
    try:
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
                login_user(user, remember=form.remember.data)
                user.last_login_at = datetime.datetime.now(datetime.timezone.utc)
                
                session_token = uuid.uuid4().hex
                user_session = UserSession(
                    user_id=user.id,
                    session_token=session_token,
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
                db.session.add(user_session)
                db.session.commit()
                
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('dashboard_bp.dashboard'))
            else:
                flash('Login Unsuccessful. Please check email and password', 'danger')

    except SQLAlchemyError as e:
        db.session.rollback()
        flash('A database error occurred. Please try again.','danger')
    except Exception as e:
        db.session.rollback()
        flash('An unexpected error occurred during login.','danger')

    return render_template('auth/login.html', title='Login', form=form)

@auth_bp.route('/logout')
def logout():
    session_record = UserSession.query.filter_by(user_id=current_user.id,is_active=True).first()

    if session_record:
        session_record.is_active = False
        db.session.commit()

    logout_user()
    return redirect(url_for('auth_bp.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateProfileForm()
    try:
        employee = current_user.employee
        if form.validate_on_submit():
            if not employee:
                flash('Employee profile not found.', 'danger')
                return redirect(url_for('dashboard_bp.dashboard'))
            employee.full_name = form.full_name.data
            employee.phone = form.phone.data
            
            if form.password.data:
                hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
                current_user.password_hash = hashed_password
                
            db.session.commit()
            flash('Your profile has been updated!', 'success')
            return redirect(url_for('auth_bp.profile'))
        elif request.method == 'GET':
            if employee:
                form.full_name.data = employee.full_name
                form.phone.data = employee.phone

    except SQLAlchemyError as e:
        db.session.rollback()
        flash('A database error occurred while updating your profile.','danger')
    except Exception as e:
        db.session.rollback()
        flash('An unexpected error occurred.','danger')

    return render_template('main/profile.html', title='Profile', form=form)
