from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, current_user
from app import db, bcrypt
from app.models import Company, User, UserSession, Employee, Role
import datetime
import uuid

def login_action():
    if current_user.is_authenticated and current_user.is_superadmin:
        return redirect(url_for('superadmin_bp.dashboard'))
        
    if request.args.get('secret') != 'master_key':
        return redirect(url_for('auth_bp.login'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            if not user.is_superadmin:
                flash('You do not have Platform Admin privileges.', 'danger')
                return render_template('superadmin/login.html', title='Platform Admin Login')
                
            login_user(user, remember=request.form.get('remember'))
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
            
            return redirect(url_for('superadmin_bp.dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
            
    return render_template('superadmin/login.html', title='Platform Admin Login')

def dashboard_action():
    total_companies = Company.query.count()
    active_companies = Company.query.filter_by(is_active=True).count()
    total_users = User.query.count()
    
    return render_template('superadmin/dashboard.html', 
                           total_companies=total_companies, 
                           active_companies=active_companies,
                           total_users=total_users,
                           title='Super Admin Dashboard')

def list_companies_action():
    companies = Company.query.order_by(Company.created_at.desc()).all()
    return render_template('superadmin/companies.html', companies=companies, title='Manage Companies')

def toggle_company_status_action(company_id):
    company = Company.query.get_or_404(company_id)
    
    if company.is_active:
        company.is_active = False
        
        users = User.query.filter_by(company_id=company.id).all()
        user_ids = [u.id for u in users]
        if user_ids:
            UserSession.query.filter(UserSession.user_id.in_(user_ids), UserSession.is_active == True).update({'is_active': False}, synchronize_session=False)
            
        flash(f"Company '{company.company_name}' has been suspended and all active sessions terminated.", 'warning')
    else:
        company.is_active = True
        flash(f"Company '{company.company_name}' has been activated.", 'success')
        
    db.session.commit()
    return redirect(url_for('superadmin_bp.list_companies'))

def delete_company_action(company_id):
    company = Company.query.get_or_404(company_id)
    flash("Deleting a company is disabled for safety. Please suspend the company instead.", "danger")
    return redirect(url_for('superadmin_bp.list_companies'))

def create_company_action():
    if request.method == 'POST':
        company_name = request.form.get('company_name')
        admin_name = request.form.get('admin_name')
        admin_email = request.form.get('admin_email')
        admin_password = request.form.get('admin_password')
        
        if not all([company_name, admin_name, admin_email, admin_password]):
            flash("All fields are required.", "danger")
            return render_template('superadmin/create_company.html', title='Add Company')
            
        existing_user = User.query.filter_by(email=admin_email).first()
        if existing_user:
            flash("Email already registered in the system.", "danger")
            return render_template('superadmin/create_company.html', title='Add Company')
            
        try:
            company = Company(company_name=company_name)
            db.session.add(company)
            db.session.flush()
            
            admin_role = Role.query.filter_by(name='Admin').first()
            if not admin_role:
                admin_role = Role(name='Admin', description='Full system management')
                db.session.add(admin_role)
                db.session.flush()
                
            hashed_password = bcrypt.generate_password_hash(admin_password).decode('utf-8')
            user = User(
                company_id=company.id,
                role_id=admin_role.id,
                email=admin_email,
                password_hash=hashed_password
            )
            db.session.add(user)
            db.session.flush()
            
            employee = Employee(
                user_id=user.id,
                company_id=company.id,
                full_name=admin_name
            )
            db.session.add(employee)
            db.session.commit()
            
            flash(f"Company '{company_name}' successfully provisioned. Admin account created.", "success")
            return redirect(url_for('superadmin_bp.list_companies'))
            
        except Exception as e:
            db.session.rollback()
            flash("An error occurred while provisioning the company.", "danger")
            print(f"Error creating company: {e}")
            
    return render_template('superadmin/create_company.html', title='Add Company')

def list_users_action():
    company_id = request.args.get('company_id')
    
    query = User.query
    if company_id:
        query = query.filter_by(company_id=company_id)
        
    users = query.filter(User.role_id != None).order_by(User.created_at.desc()).all()
    companies = Company.query.order_by(Company.company_name.asc()).all()
    
    return render_template('superadmin/users.html', users=users, companies=companies, selected_company_id=company_id, title='All Users')
