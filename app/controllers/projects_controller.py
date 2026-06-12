from flask import current_app, render_template, redirect, url_for, flash, request
from flask_login import current_user
from datetime import datetime, timezone
from app import db
from app.models.project import Project, EmployeeProject
from app.models.client import Client
from app.models.employee import Employee
from app.models.user import User
from app.models.role import Role
from app.forms.project_forms import ProjectForm, AssignEmployeeForm

def create_project_action():
    if current_user.role.name not in ['Admin', 'Project Manager', 'Accountant', 'Employee']:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard_bp.dashboard'))

    form = ProjectForm()
    
    clients = Client.query.filter_by(company_id=current_user.company_id, is_active=True).all()
    form.client_id.choices = [(c.id, c.client_name) for c in clients]
    
    project_managers = Employee.query.join(User).join(Role).filter(
        Employee.company_id == current_user.company_id,
        Employee.is_active == True,
        Role.name == 'Project Manager'
    ).all()
    form.project_manager_id.choices = [('', 'Select Manager')] + [(e.id, e.full_name) for e in project_managers]

    if form.validate_on_submit():
        if current_user.role.name != 'Admin':
            flash('Only Admins can create new projects.', 'danger')
            return redirect(url_for('projects_bp.create_project'))
            
        project = Project(
            company_id=current_user.company_id,
            client_id=form.client_id.data,
            project_manager_id=form.project_manager_id.data or None,
            status=form.status.data,
            name=form.name.data,
            description=form.description.data,
            budget=form.budget.data,
            start_date=form.start_date.data,
            estimated_end_date=form.estimated_end_date.data
        )
        try:
            db.session.add(project)
            db.session.commit()
            flash('Project created successfully!', 'success')
            return redirect(url_for('projects_bp.create_project'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error creating project: {str(e)}')
            flash('Error creating project. Please try again.', 'danger')

    status_filter = request.args.get('status')

    if current_user.role.name == 'Employee':
        emp_id = current_user.employee.id if current_user.employee else None
        query = Project.query.join(EmployeeProject).filter(
            Project.company_id == current_user.company_id,
            EmployeeProject.employee_id == emp_id,
            EmployeeProject.removed_at == None
        )
    elif current_user.role.name == 'Project Manager':
        emp_id = current_user.employee.id if current_user.employee else None
        query = Project.query.outerjoin(EmployeeProject).filter(
            Project.company_id == current_user.company_id,
            db.or_(Project.project_manager_id == emp_id, EmployeeProject.employee_id == emp_id)
        )
    else:
        query = Project.query.filter_by(company_id=current_user.company_id)

    if status_filter:
        query = query.filter(Project.status == status_filter)

    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page=page, per_page=10, error_out=False)
    projects = pagination.items

    return render_template('projects/index.html', form=form, projects=projects, pagination=pagination, title='Projects', current_status=status_filter)

def view_project_action(project_id):
    project = Project.query.filter_by(id=project_id, company_id=current_user.company_id).first_or_404()
    
    if current_user.role.name == 'Project Manager':
        emp_id = current_user.employee.id if current_user.employee else None
        if project.project_manager_id != emp_id:
            flash('Unauthorized access', 'danger')
            return redirect(url_for('projects_bp.create_project'))
            
    elif current_user.role.name == 'Employee':
        emp_id = current_user.employee.id if current_user.employee else None
        is_assigned = EmployeeProject.query.filter_by(
            project_id=project.id, 
            employee_id=emp_id, 
            removed_at=None
        ).first()
        if not is_assigned:
            flash('Unauthorized access', 'danger')
            return redirect(url_for('projects_bp.create_project'))

    active_employees = Employee.query.join(EmployeeProject).filter(
        EmployeeProject.project_id == project.id,
        EmployeeProject.removed_at == None
    ).all()
    
    assign_form = AssignEmployeeForm()
    assigned_ids = [e.id for e in active_employees]
    query = Employee.query.join(User).join(Role).filter(
        Employee.company_id == current_user.company_id,
        Employee.is_active == True,
        Role.name == 'Employee'
    )
    if assigned_ids:
        query = query.filter(~Employee.id.in_(assigned_ids))
    employees = query.all()
    assign_form.employee_id.choices = [(e.id, e.full_name) for e in employees]
    
    total_expenses = sum(exp.amount for exp in project.expenses if exp.status == 'Approved')
    
    return render_template('projects/view.html', project=project, assign_form=assign_form, total_expenses=total_expenses, active_employees=active_employees)

def assign_project_action(project_id):
    project = Project.query.filter_by(id=project_id, company_id=current_user.company_id).first_or_404()
    
    if current_user.role.name not in ['Admin', 'Project Manager']:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('projects_bp.view_project', project_id=project.id))

    assign_form = AssignEmployeeForm()
    assigned_ids = [a.employee_id for a in EmployeeProject.query.filter_by(project_id=project.id, removed_at=None).all()]
    query = Employee.query.join(User).join(Role).filter(
        Employee.company_id == current_user.company_id,
        Employee.is_active == True,
        Role.name == 'Employee'
    )
    if assigned_ids:
        query = query.filter(~Employee.id.in_(assigned_ids))
    employees = query.all()
    assign_form.employee_id.choices = [(e.id, e.full_name) for e in employees]

    if assign_form.validate_on_submit():
        emp_id = assign_form.employee_id.data
        if not EmployeeProject.query.filter_by(employee_id=emp_id, project_id=project.id, removed_at=None).first():
            try:
                assignment = EmployeeProject(employee_id=emp_id, project_id=project.id)
                db.session.add(assignment)
                db.session.commit()
                flash('Employee assigned to project successfully.', 'success')
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f'Error assigning employee: {str(e)}')
                flash('Error assigning employee. Please try again.', 'danger')
        else:
            flash('Employee is already assigned to this project.', 'warning')
            
    return redirect(url_for('projects_bp.view_project', project_id=project.id))

def remove_project_employee_action(project_id, employee_id):
    if current_user.role.name not in ['Admin', 'Project Manager']:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('projects_bp.view_project', project_id=project_id))
        
    assignment = EmployeeProject.query.filter_by(project_id=project_id, employee_id=employee_id, removed_at=None).first()
    if assignment:
        try:
            assignment.removed_at = datetime.now(timezone.utc)
            db.session.commit()
            flash('Employee removed from project.', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error removing employee: {str(e)}')
            flash('Error removing employee. Please try again.', 'danger')
    return redirect(url_for('projects_bp.view_project', project_id=project_id))

def change_project_status_action(project_id):
    if current_user.role.name not in ['Admin', 'Project Manager']:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('projects_bp.view_project', project_id=project_id))
        
    project = Project.query.filter_by(id=project_id, company_id=current_user.company_id).first_or_404()
    status = request.form.get('status')
    if status in ['Not Started', 'In Progress', 'On Hold', 'Completed', 'Cancelled']:
        try:
            project.status = status
            db.session.commit()
            flash('Project status updated.', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating project status: {str(e)}')
            flash('Error updating project status. Please try again.', 'danger')
    return redirect(url_for('projects_bp.view_project', project_id=project.id))
