from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from app import db
from sqlalchemy import func
from app.models import Client, Project, EmployeeProject, Expense, ExpenseCategory, Employee, Timesheet, User, Role, Invoice, PayrollItem, Payment
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    role_name = current_user.role.name
    company_id = current_user.company_id



    stats = {}
    charts = {}

    if role_name == 'Admin':
        stats = {
            'total_employees': Employee.query.join(User).join(Role).filter(Employee.company_id==company_id, Role.name != 'Admin').count(),
            'total_projects': Project.query.filter_by(company_id=company_id).count(),
            'pending_expenses': Expense.query.filter_by(company_id=company_id, status='Pending').count(),
            'invoices_due': Invoice.query.filter(Invoice.company_id==company_id, Invoice.status != 'Paid').count()
        }

        proj_status_data = db.session.query(Project.status, func.count(Project.id)).filter_by(company_id=company_id).group_by(Project.status).all()
        charts['projects_status'] = {
            'labels': [row[0] for row in proj_status_data],
            'data': [row[1] for row in proj_status_data]
        }

        exp_cat_data = db.session.query(ExpenseCategory.name, func.sum(Expense.amount)).join(Expense).filter(Expense.company_id==company_id, Expense.status=='Approved').group_by(ExpenseCategory.name).all()
        charts['expenses_category'] = {
            'labels': [row[0] for row in exp_cat_data],
            'data': [float(row[1]) for row in exp_cat_data]
        }

        clients_proj_data = db.session.query(Client.company_name, func.count(Project.id)).outerjoin(Project, Client.id == Project.client_id).filter(Client.company_id == company_id).group_by(Client.company_name).all()
        charts['projects_per_client'] = {
            'labels': [row[0] for row in clients_proj_data],
            'data': [row[1] for row in clients_proj_data]
        }

        logged_hours_data = db.session.query(Project.name, func.sum(Timesheet.total_hours)).join(Timesheet, Timesheet.project_id == Project.id).filter(Project.company_id == company_id, Timesheet.status == 'Approved').group_by(Project.name).all()
        charts['logged_hours_per_project'] = {
            'labels': [row[0] for row in logged_hours_data],
            'data': [float(row[1]) if row[1] else 0 for row in logged_hours_data]
        }

        return render_template('dashboard/admin.html', stats=stats, charts=charts)

    elif role_name == 'Project Manager':
        emp_id = current_user.employee.id if current_user.employee else None
        team_members_count = db.session.query(func.count(func.distinct(EmployeeProject.employee_id))).join(Project).filter(Project.project_manager_id == emp_id, EmployeeProject.removed_at == None).scalar() or 0
        managed_projects = Project.query.filter_by(project_manager_id=emp_id).all()
        total_budget = sum(p.budget for p in managed_projects)
        total_expenses = db.session.query(func.sum(Expense.amount)).join(Project).filter(Project.project_manager_id == emp_id, Expense.status == 'Approved').scalar() or 0
        budget_used = f"{(total_expenses / total_budget * 100):.1f}%" if total_budget > 0 else '0%'

        pending_expenses_count = Expense.query.join(Project).filter(Project.project_manager_id==emp_id, Expense.status=='Pending').count() if emp_id else 0
        pending_timesheets_count = Timesheet.query.join(Project).filter(Project.project_manager_id==emp_id, Timesheet.status=='Pending').count() if emp_id else 0
        
        stats = {
            'active_projects': Project.query.filter_by(project_manager_id=emp_id, status='In Progress').count(),
            'team_members': team_members_count,
            'pending_approvals': pending_expenses_count + pending_timesheets_count,
            'budget_used': budget_used
        }

        proj_status_data = db.session.query(Project.status, func.count(Project.id)).filter_by(project_manager_id=emp_id).group_by(Project.status).all()
        charts['projects_status'] = {
            'labels': [row[0] for row in proj_status_data],
            'data': [row[1] for row in proj_status_data]
        }

        logged_hours_data = db.session.query(Project.name, func.sum(Timesheet.total_hours)).join(Timesheet, Timesheet.project_id == Project.id).filter(Project.project_manager_id == emp_id, Timesheet.status == 'Approved').group_by(Project.name).all()
        charts['logged_hours_per_project'] = {
            'labels': [row[0] for row in logged_hours_data],
            'data': [float(row[1]) if row[1] else 0 for row in logged_hours_data]
        }

        expenses_data = db.session.query(Project.name, func.sum(Expense.amount)).join(Expense, Expense.project_id == Project.id).filter(Project.project_manager_id == emp_id, Expense.status == 'Approved').group_by(Project.name).all()
        charts['expenses_per_project'] = {
            'labels': [row[0] for row in expenses_data],
            'data': [float(row[1]) if row[1] else 0 for row in expenses_data]
        }

        return render_template('dashboard/manager.html', stats=stats, charts=charts)

    elif role_name == 'Accountant':
        now = datetime.utcnow()
        current_month = now.month
        current_year = now.year
        
        monthly_revenue = db.session.query(func.sum(Payment.amount_paid)).join(Invoice).filter(
            Invoice.company_id == company_id,
            db.extract('month', Payment.payment_date) == current_month,
            db.extract('year', Payment.payment_date) == current_year
        ).scalar() or 0.0

        stats = {
            'pending_payrolls': PayrollItem.query.join(Employee).filter(Employee.company_id==company_id, PayrollItem.status != 'Approved').count(), 
            'unpaid_invoices': Invoice.query.filter(Invoice.company_id==company_id, Invoice.status != 'Paid').count(),
            'expense_reports': Expense.query.filter_by(company_id=company_id, status='Pending').count(),
            'monthly_revenue': f"${monthly_revenue:,.2f}"
        }

        exp_status_data = db.session.query(Expense.status, func.count(Expense.id)).filter_by(company_id=company_id).group_by(Expense.status).all()
        charts['expenses_status'] = {
            'labels': [row[0] for row in exp_status_data],
            'data': [row[1] for row in exp_status_data]
        }
        
        inv_status_data = db.session.query(Invoice.status, func.count(Invoice.id)).filter_by(company_id=company_id).group_by(Invoice.status).all()
        charts['invoices_status'] = {
            'labels': [row[0] for row in inv_status_data],
            'data': [row[1] for row in inv_status_data]
        }

        return render_template('dashboard/accountant.html', stats=stats, charts=charts)

    elif role_name == 'Employee':

        emp_id = current_user.employee.id if current_user.employee else None
        
        now = datetime.utcnow()
        current_month = now.month
        current_year = now.year
        
        logged_hours = db.session.query(func.sum(Timesheet.total_hours)).filter(
            Timesheet.employee_id == emp_id,
            db.extract('month', Timesheet.work_date) == current_month,
            db.extract('year', Timesheet.work_date) == current_year,
            Timesheet.status == 'Approved'
        ).scalar() or 0
        
        stats = {
            'assigned_projects': EmployeeProject.query.filter_by(employee_id=emp_id, removed_at=None).count() if emp_id else 0,
            'pending_timesheets': Timesheet.query.filter_by(employee_id=emp_id, status='Pending').count() if emp_id else 0, 
            'submitted_expenses': Expense.query.filter_by(employee_id=emp_id).count() if emp_id else 0,
            'logged_hours_this_month': f"{logged_hours:.1f}" 
        }

        my_exp_status = db.session.query(Expense.status, func.count(Expense.id)).filter_by(employee_id=emp_id).group_by(Expense.status).all()
        charts['my_expenses_status'] = {
            'labels': [row[0] for row in my_exp_status],
            'data': [row[1] for row in my_exp_status]
        }
        
        today = now.date()
        week_dates = [today - timedelta(days=i) for i in range(6, -1, -1)]
        labels = [d.strftime('%a') for d in week_dates]
        data = [0] * 7
        
        recent_timesheets = Timesheet.query.filter(
            Timesheet.employee_id == emp_id,
            Timesheet.work_date >= week_dates[0],
            Timesheet.work_date <= today,
            Timesheet.status != 'Rejected'
        ).all()
        
        for ts in recent_timesheets:
            for i, d in enumerate(week_dates):
                if ts.work_date == d:
                    data[i] += float(ts.total_hours)
                    break
                    
        charts['weekly_hours'] = {
            'labels': labels,
            'data': data
        }

        return render_template('dashboard/employee.html', stats=stats, charts=charts)

    else:
        abort(403)
