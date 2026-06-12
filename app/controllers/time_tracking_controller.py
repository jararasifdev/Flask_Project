from flask import current_app,render_template, redirect, url_for, flash, request
from flask_login import current_user
from app import db
from app.models import Timesheet, Project, Expense, ExpenseCategory, EmployeeProject, Role, User, Employee
from app.forms import TimesheetForm, ReviewTimesheetForm
from app.utils.notifications import create_notification
from datetime import datetime, date, timedelta
from decimal import Decimal
from app.controllers.expenses_controller import check_budget_threshold

def list_timesheets_action():
    status_filter = request.args.get('status')
    project_filter = request.args.get('project_id')
    search_filter = request.args.get('search', '').strip()

    query = Timesheet.query

    if current_user.role.name in ['Admin', 'Project Manager','Accountant']:
        if current_user.role.name == 'Admin' or current_user.role.name == 'Accountant':
            query = query.filter_by(company_id=current_user.company_id)
            projects = Project.query.filter_by(company_id=current_user.company_id).all()
        else:
            query = query.join(Project).filter(
                Project.company_id == current_user.company_id,
                db.or_(Project.project_manager_id == current_user.employee.id, Timesheet.employee_id == current_user.employee.id)
            )
            projects = Project.query.filter(
                Project.company_id == current_user.company_id,
                Project.project_manager_id == current_user.employee.id
            ).all()
    else:
        query = query.filter_by(employee_id=current_user.employee.id)
        emp_id = current_user.employee.id if current_user.employee else None
        projects = Project.query.join(EmployeeProject).filter(
            Project.company_id == current_user.company_id,
            EmployeeProject.employee_id == emp_id,
            EmployeeProject.removed_at == None
        ).all()
        
    if status_filter:
        query = query.filter(Timesheet.status == status_filter)
    if project_filter:
        query = query.filter(Timesheet.project_id == project_filter)
    if search_filter:
        query = query.join(Employee, Timesheet.employee_id == Employee.id).filter(Employee.full_name.ilike(f'%{search_filter}%'))
        
    timesheets = query.order_by(Timesheet.work_date.desc()).all()
        
    return render_template('time_tracking/index.html', timesheets=timesheets, projects=projects, current_status=status_filter, current_project=project_filter, search_query=search_filter, title='Time Tracking')

def log_time_action():
    form = TimesheetForm()
    
    if current_user.role.name == 'Admin':
        projects = Project.query.filter_by(company_id=current_user.company_id).all()
    else:
        projects = Project.query.outerjoin(EmployeeProject, 
            db.and_(EmployeeProject.project_id == Project.id, EmployeeProject.removed_at == None)
        ).filter(
            Project.company_id == current_user.company_id,
            db.or_(
                Project.project_manager_id == current_user.employee.id,
                EmployeeProject.employee_id == current_user.employee.id
            )
        ).all()
        
    form.project_id.choices = [(p.id, p.name) for p in projects]
    
    if form.validate_on_submit():
        start = form.start_time.data
        end = form.end_time.data
        
        dummy_date = date.today()
        dt_start = datetime.combine(dummy_date, start)
        dt_end = datetime.combine(dummy_date, end)
        
        if dt_end <= dt_start:
            dt_end += timedelta(days=1)
            
        delta = dt_end - dt_start
        total_hours = delta.total_seconds() / 3600.0

        timesheet = Timesheet(
            company_id=current_user.company_id,
            employee_id=current_user.employee.id,
            project_id=form.project_id.data,
            work_date=form.work_date.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            total_hours=total_hours,
            is_billable=form.is_billable.data,
            task_description=form.task_description.data
        )
        db.session.add(timesheet)
        
        project = Project.query.get(timesheet.project_id)
        
        admin_role = Role.query.filter_by(name='Admin').first()
        admins = User.query.filter_by(company_id=current_user.company_id, role_id=admin_role.id).all() if admin_role else []
        
        if current_user.role.name == 'Employee' and project and project.project_manager and project.project_manager.user_id:
            pm_user_id = project.project_manager.user_id
            if pm_user_id != current_user.id:
                create_notification(
                    company_id=current_user.company_id,
                    user_id=pm_user_id,
                    type_name='Time Logged',
                    title='New Time Logged',
                    message=f"{current_user.employee.full_name} logged {total_hours:.2f} hours for project '{project.name}'."
                )
                
        for admin in admins:
            if admin.id != current_user.id:
                create_notification(
                    company_id=current_user.company_id,
                    user_id=admin.id,
                    type_name='Time Logged',
                    title='New Time Logged',
                    message=f"{current_user.employee.full_name} logged {total_hours:.2f} hours for project '{project.name}'."
                )
                
        try:
            db.session.commit()
            flash('Time logged successfully.', 'success')
            return redirect(url_for('time_tracking_bp.list_timesheets'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error logging time: {str(e)}')
            flash('Error logging time. Please try again.', 'danger')
        
    return render_template('time_tracking/log_time.html', form=form, title='Log Time')

def review_timesheet_action(timesheet_id):
    timesheet = Timesheet.query.filter_by(id=timesheet_id, company_id=current_user.company_id).first_or_404()
    
    if timesheet.employee_id == current_user.employee.id and current_user.role.name != 'Admin':
        flash('You cannot review your own timesheets. This must be done by an Admin.', 'danger')
        return redirect(url_for('time_tracking_bp.list_timesheets'))

    form = ReviewTimesheetForm()
    
    if form.validate_on_submit():
        try:
            timesheet.status = form.status.data
            timesheet.approved_by_employee_id = current_user.employee.id
            timesheet.approved_at = datetime.utcnow()
            db.session.commit()
            
            if form.status.data == 'Approved' and timesheet.is_billable:
                category = ExpenseCategory.query.filter_by(name='Billable Hours', company_id=current_user.company_id).first()
                if not category:
                    category = ExpenseCategory(name='Billable Hours', description='Approved billable timesheet hours', company_id=current_user.company_id)
                    db.session.add(category)
                    db.session.flush()
                    
                emp = timesheet.employee
                rate = emp.hourly_rate if emp.hourly_rate else (emp.monthly_salary / 160 if emp.monthly_salary else 0)
                amount = Decimal(str(float(timesheet.total_hours) * float(rate)))
                
                expense = Expense(
                    company_id=current_user.company_id,
                    project_id=timesheet.project_id,
                    employee_id=timesheet.employee_id,
                    category_id=category.id,
                    amount=amount,
                    description=f"Billable hours on {timesheet.work_date}: {timesheet.task_description or 'No description'}",
                    status='Approved',
                    approved_by_employee_id=current_user.employee.id
                )
                db.session.add(expense)
                db.session.commit()

                check_budget_threshold(timesheet.project)
                db.session.commit()
            
            status_word = "Approved" if form.status.data == 'Approved' else "Rejected"
            create_notification(
                company_id=current_user.company_id,
                user_id=timesheet.employee.user.id,
                type_name='Timesheet Update',
                title=f'Timesheet {status_word}',
                message=f'Your timesheet for {timesheet.work_date.strftime("%Y-%m-%d")} on project {timesheet.project.name} has been {status_word.lower()}.'
            )
            db.session.commit()
            
            flash(f'Timesheet {status_word.lower()} successfully.', 'success')
            return redirect(url_for('time_tracking_bp.list_timesheets'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error reviewing timesheet: {str(e)}')
            flash(f'Error reviewing timesheet. Please try again.', 'danger')
        
    return render_template('time_tracking/review.html', timesheet=timesheet, form=form, title='Review Timesheet')

def view_timesheet_action(timesheet_id):
    timesheet = Timesheet.query.filter_by(id=timesheet_id, company_id=current_user.company_id).first_or_404()

    if current_user.role.name not in ['Admin', 'Accountant', 'Project Manager']:
        if timesheet.employee_id != current_user.employee.id:
            flash('Access denied.', 'danger')
    return render_template('time_tracking/view.html', timesheet=timesheet, title='View Timesheet')

def approve_all_action():
    query = Timesheet.query.filter_by(company_id=current_user.company_id, status='Pending')
    
    if current_user.role.name == 'Project Manager':
        query = query.join(Project).filter(Project.project_manager_id == current_user.employee.id)

    project_filter = request.form.get('project_id')
    search_filter = request.form.get('search', '').strip()
    
    if project_filter:
        query = query.filter(Timesheet.project_id == project_filter)
    if search_filter:
        query = query.join(Employee, Timesheet.employee_id == Employee.id).filter(Employee.full_name.ilike(f'%{search_filter}%'))
        
    pending_timesheets = query.all()
    count = 0
    
    category = None
    for timesheet in pending_timesheets:
        if timesheet.employee_id == current_user.employee.id and current_user.role.name != 'Admin':
            continue
            
        timesheet.status = 'Approved'
        timesheet.approved_by_employee_id = current_user.employee.id
        timesheet.approved_at = datetime.utcnow()
        count += 1
        
        if timesheet.is_billable:
            if not category:
                category = ExpenseCategory.query.filter_by(name='Billable Hours', company_id=current_user.company_id).first()
                if not category:
                    category = ExpenseCategory(name='Billable Hours', description='Approved billable timesheet hours', company_id=current_user.company_id)
                    db.session.add(category)
                    db.session.flush()
                    
            emp = timesheet.employee
            rate = emp.hourly_rate if emp.hourly_rate else (emp.monthly_salary / 160 if emp.monthly_salary else 0)
            amount = Decimal(str(float(timesheet.total_hours) * float(rate)))
            
            expense = Expense(
                company_id=current_user.company_id,
                project_id=timesheet.project_id,
                employee_id=timesheet.employee_id,
                category_id=category.id,
                amount=amount,
                description=f"Billable hours on {timesheet.work_date}: {timesheet.task_description or 'No description'}",
                status='Approved',
                approved_by_employee_id=current_user.employee.id
            )
            db.session.add(expense)
            check_budget_threshold(timesheet.project)
            
        create_notification(
            company_id=current_user.company_id,
            user_id=timesheet.employee.user.id,
            type_name='Timesheet Update',
            title='Timesheet Approved',
            message=f'Your timesheet for {timesheet.work_date.strftime("%Y-%m-%d")} on project {timesheet.project.name} has been approved.'
        )
        
    try:
        db.session.commit()
        flash(f'Successfully approved {count} pending timesheets.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error approving timesheets: {str(e)}')
        flash(f'Error approving timesheets. Please try again.', 'danger')
        
    return redirect(url_for('time_tracking_bp.list_timesheets', project_id=project_filter, search=search_filter, status='Pending'))
