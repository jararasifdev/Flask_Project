from flask import current_app, render_template, redirect, url_for, flash, request
from flask_login import current_user
from app import db, bcrypt
from app.models import Employee, User, Role, Department, UserSession
from app.forms import AddEmployeeForm, EditEmployeeForm

def list_employees_action():
    search_query = request.args.get('search', '').strip()
    
    query = Employee.query.join(User).join(Role).filter(
        Employee.company_id == current_user.company_id,
        Employee.is_active == True,
        Role.name != 'Admin'
    )
    
    if search_query:
        query = query.filter(
            db.or_(
                Employee.full_name.ilike(f'%{search_query}%'),
                User.email.ilike(f'%{search_query}%')
            )
        )
        
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page=page, per_page=10, error_out=False)
    employees = pagination.items
    return render_template('employees/list.html', employees=employees, pagination=pagination, search_query=search_query, title="Manage Employees")

def create_employee_action():
    form = AddEmployeeForm()

    roles = Role.query.all()
    form.role_id.choices = [(r.id, r.name) for r in roles if r.name != 'Admin']
    
    departments = Department.query.filter_by(company_id=current_user.company_id, is_active=True).all()
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
            hourly_rate=form.hourly_rate.data,
            monthly_salary=form.monthly_salary.data
        )
        try:
            db.session.add(employee)
            db.session.commit()
            flash('Employee account successfully created!', 'success')
            return redirect(url_for('employees_bp.list_employees'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error creating employee: {str(e)}')
            flash('Error creating employee. Please try again.', 'danger')

    return render_template('employees/create.html', form=form, title="Add Employee")

def edit_employee_action(employee_id):
    employee = Employee.query.filter_by(id=employee_id, company_id=current_user.company_id).first_or_404()
    user = employee.user
    form = EditEmployeeForm()

    roles = Role.query.all()
    form.role_id.choices = [(r.id, r.name) for r in roles if r.name != 'Admin']
    
    departments = Department.query.filter_by(company_id=current_user.company_id, is_active=True).all()
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
        employee.hourly_rate = form.hourly_rate.data
        employee.monthly_salary = form.monthly_salary.data
        
        try:
            db.session.commit()
            flash('Employee profile successfully updated!', 'success')
            return redirect(url_for('employees_bp.list_employees'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating employee: {str(e)}')
            flash('Error updating employee. Please try again.', 'danger')

    elif request.method == 'GET':
        form.full_name.data = employee.full_name
        form.email.data = user.email
        form.role_id.data = user.role_id
        form.department_id.data = employee.department_id if employee.department_id else ''
        form.phone.data = employee.phone
        form.employment_type.data = employee.employment_type
        form.joining_date.data = employee.joining_date
        form.hourly_rate.data = employee.hourly_rate
        form.monthly_salary.data = employee.monthly_salary

    return render_template('employees/edit.html', form=form, employee=employee, title="Edit Employee")

def delete_employee_action(employee_id):
    employee = Employee.query.filter_by(id=employee_id, company_id=current_user.company_id).first_or_404()
    user = employee.user
    
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('employees_bp.list_employees'))

    try:
        UserSession.query.filter_by(user_id=user.id).delete()
        user.is_active = False
        employee.is_active = False
        db.session.commit()
        flash('Employee account deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting employee: {str(e)}')
        flash('Error deleting employee. Please try again.', 'danger')
        
    return redirect(url_for('employees_bp.list_employees'))
