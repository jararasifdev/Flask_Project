from flask import current_app, render_template, redirect, url_for, flash, request
from flask_login import current_user
from app import db
from app.models import Department, Employee, User, Role
from app.forms import DepartmentForm, AssignEmployeeForm

def list_departments_action():
    departments = Department.query.filter_by(company_id=current_user.company_id, is_active=True).all()
    return render_template('departments/list.html', departments=departments, title="Manage Departments")

def create_department_action():
    form = DepartmentForm()
    if form.validate_on_submit():
        existing_dept = Department.query.filter(
            Department.company_id == current_user.company_id,
            db.func.lower(Department.name) == form.name.data.lower()
        ).first()

        if existing_dept:
            flash(f"A department named '{form.name.data}' already exists.", 'danger')
            return render_template('departments/create.html', form=form, title="Create Department")

        dept = Department(
            company_id=current_user.company_id,
            name=form.name.data,
            description=form.description.data
        )
        try:
            db.session.add(dept)
            db.session.commit()
            flash('Department created successfully.', 'success')
            return redirect(url_for('departments_bp.list_departments'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error creating department: {str(e)}')
            flash('Error creating department. Please try again.', 'danger')
    return render_template('departments/create.html', form=form, title="Create Department")

def view_department_action(department_id):
    department = Department.query.filter_by(id=department_id, company_id=current_user.company_id).first_or_404()
    form = DepartmentForm()
    assign_form = AssignEmployeeForm()

    employees = Employee.query.join(User).join(Role).filter(
        Employee.company_id == current_user.company_id,
        Employee.is_active == True,
        Employee.department_id.is_(None),
        Role.name != 'Admin'
    ).all()
    assign_form.employee_id.choices = [(e.id, e.full_name) for e in employees]
    
    if form.validate_on_submit():
        existing_dept = Department.query.filter(
            Department.id != department.id,
            Department.company_id == current_user.company_id,
            db.func.lower(Department.name) == form.name.data.lower()
        ).first()
        
        if existing_dept:
            flash(f"Another department named '{form.name.data}' already exists.", 'danger')
            return render_template('departments/view.html', form=form, assign_form=assign_form, department=department, title="Manage Department")

        try:
            department.name = form.name.data
            department.description = form.description.data
            db.session.commit()
            flash('Department updated successfully.', 'success')
            return redirect(url_for('departments_bp.view_department', department_id=department.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating department: {str(e)}')
            flash('Error updating department. Please try again.', 'danger')
        
    elif request.method == 'GET':
        form.name.data = department.name
        form.description.data = department.description
        
    return render_template('departments/view.html', form=form, assign_form=assign_form, department=department, title="Manage Department")

def assign_employee_action(department_id):
    department = Department.query.filter_by(id=department_id, company_id=current_user.company_id).first_or_404()
    assign_form = AssignEmployeeForm()
    
    employees = Employee.query.join(User).join(Role).filter(
        Employee.company_id == current_user.company_id,
        Employee.is_active == True,
        Employee.department_id.is_(None),
        Role.name != 'Admin'
    ).all()
    assign_form.employee_id.choices = [(e.id, e.full_name) for e in employees]
    
    if assign_form.validate_on_submit():
        try:
            emp_id = assign_form.employee_id.data
            employee = Employee.query.filter_by(id=emp_id, company_id=current_user.company_id).first_or_404()
            employee.department_id = department.id
            db.session.commit()
            flash(f'{employee.full_name} assigned to department successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error assigning employee: {str(e)}')
            flash('Error assigning employee. Please try again.', 'danger')
            
    return redirect(url_for('departments_bp.view_department', department_id=department.id))

def remove_employee_from_department_action(department_id, employee_id):
    department = Department.query.filter_by(id=department_id, company_id=current_user.company_id).first_or_404()
    employee = Employee.query.filter_by(id=employee_id, department_id=department.id, company_id=current_user.company_id).first_or_404()
    
    try:
        employee.department_id = None
        db.session.commit()
        flash(f'{employee.full_name} removed from the department.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error removing employee: {str(e)}')
        flash('Error removing employee. Please try again.', 'danger')
    return redirect(url_for('departments_bp.view_department', department_id=department.id))

def delete_department_action(department_id):
    department = Department.query.filter_by(id=department_id, company_id=current_user.company_id).first_or_404()
    
    if department.employees:
        flash('Cannot delete department because it contains employees.', 'danger')
        return redirect(url_for('departments_bp.list_departments'))

    try:
        department.is_active = False
        db.session.commit()
        flash('Department deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting department: {str(e)}')
        flash('Error deleting department. Please try again.', 'danger')
    return redirect(url_for('departments_bp.list_departments'))
