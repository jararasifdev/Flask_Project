from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db, bcrypt
from app.models import Employee, User, Role, Department, UserSession
from app.forms import AddEmployeeForm, EditEmployeeForm
from app.utils.decorators import role_required

employees_bp = Blueprint('employees_bp', __name__)

@employees_bp.route('/employees')
@login_required
@role_required('Admin')
def list_employees():
    search_query = request.args.get('search', '').strip()
    
    query = Employee.query.join(User).join(Role).filter(
        Employee.company_id == current_user.company_id,
        Role.name != 'Admin'
    )
    
    if search_query:
        query = query.filter(
            db.or_(
                Employee.full_name.ilike(f'%{search_query}%'),
                User.email.ilike(f'%{search_query}%')
            )
        )
        
    employees = query.all()
    return render_template('employees/list.html', employees=employees, search_query=search_query, title="Manage Employees")

@employees_bp.route('/employees/create', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def create_employee():
    form = AddEmployeeForm()

    roles = Role.query.all()
    form.role_id.choices = [(r.id, r.name) for r in roles if r.name != 'Admin']
    
    departments = Department.query.filter_by(company_id=current_user.company_id).all()
    form.department_id.choices = [('', 'No Department')] + [(d.id, d.name) for d in departments]

    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email address is already in use.', 'danger')
            return render_template('employees/create.html', form=form, title="Add Employee")

        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        
        user = User(
            company_id=current_user.company_id,
            role_id=form.role_id.data,
            email=form.email.data,
            password_hash=hashed_password
        )
        db.session.add(user)
        db.session.flush()
        
        dept_id = form.department_id.data if form.department_id.data != '' else None
        
        employee = Employee(
            user_id=user.id,
            company_id=current_user.company_id,
            department_id=dept_id,
            full_name=form.full_name.data,
            phone=form.phone.data,
            employment_type=form.employment_type.data,
            joining_date=form.joining_date.data,
            monthly_salary=form.monthly_salary.data
        )
        db.session.add(employee)
        db.session.commit()
        
        flash('Employee account successfully created!', 'success')
        return redirect(url_for('employees_bp.list_employees'))

    return render_template('employees/create.html', form=form, title="Add Employee")

@employees_bp.route('/employees/<employee_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def edit_employee(employee_id):
    employee = Employee.query.filter_by(id=employee_id, company_id=current_user.company_id).first_or_404()
    user = employee.user
    form = EditEmployeeForm()

    roles = Role.query.all()
    form.role_id.choices = [(r.id, r.name) for r in roles if r.name != 'Admin']
    
    departments = Department.query.filter_by(company_id=current_user.company_id).all()
    form.department_id.choices = [('', 'No Department')] + [(d.id, d.name) for d in departments]

    if form.validate_on_submit():
        existing_user = User.query.filter(User.email == form.email.data, User.id != user.id).first()
        if existing_user:
            flash('Email address is already in use by another user.', 'danger')
            return render_template('employees/edit.html', form=form, employee=employee, title="Edit Employee")

        user.email = form.email.data
        user.role_id = form.role_id.data
        
        dept_id = form.department_id.data if form.department_id.data != '' else None
        
        employee.department_id = dept_id
        employee.full_name = form.full_name.data
        employee.phone = form.phone.data
        employee.employment_type = form.employment_type.data
        employee.joining_date = form.joining_date.data
        employee.monthly_salary = form.monthly_salary.data
        
        db.session.commit()
        flash('Employee profile successfully updated!', 'success')
        return redirect(url_for('employees_bp.list_employees'))

    elif request.method == 'GET':
        form.full_name.data = employee.full_name
        form.email.data = user.email
        form.role_id.data = user.role_id
        form.department_id.data = employee.department_id if employee.department_id else ''
        form.phone.data = employee.phone
        form.employment_type.data = employee.employment_type
        form.joining_date.data = employee.joining_date
        form.monthly_salary.data = employee.monthly_salary

    return render_template('employees/edit.html', form=form, employee=employee, title="Edit Employee")

@employees_bp.route('/employees/<employee_id>/delete', methods=['POST'])
@login_required
@role_required('Admin')
def delete_employee(employee_id):
    employee = Employee.query.filter_by(id=employee_id, company_id=current_user.company_id).first_or_404()
    user = employee.user
    
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('employees_bp.list_employees'))

    UserSession.query.filter_by(user_id=user.id).delete()
    db.session.delete(employee)
    db.session.delete(user)
    db.session.commit()
    
    flash('Employee account deleted successfully.', 'success')
    return redirect(url_for('employees_bp.list_employees'))
