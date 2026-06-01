from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from app import db
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    role_name = current_user.role.name
    company_id = current_user.company_id

    from app.models.project import Project, EmployeeProject
    from app.models.expense import Expense, ExpenseCategory
    from app.models.employee import Employee

    stats = {}
    charts = {}

    if role_name == 'Admin':
        stats = {
            'total_employees': Employee.query.filter_by(company_id=company_id).count(),
            'total_projects': Project.query.filter_by(company_id=company_id).count(),
            'pending_expenses': Expense.query.filter_by(company_id=company_id, status='Pending').count(),
            'invoices_due': 0 
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

        from app.models.client import Client
        clients_proj_data = db.session.query(Client.company_name, func.count(Project.id)).outerjoin(Project, Client.id == Project.client_id).filter(Client.company_id == company_id).group_by(Client.company_name).all()
        charts['projects_per_client'] = {
            'labels': [row[0] for row in clients_proj_data],
            'data': [row[1] for row in clients_proj_data]
        }

        return render_template('dashboard/admin.html', stats=stats, charts=charts)

    elif role_name == 'Project Manager':
        emp_id = current_user.employee.id if current_user.employee else None
        team_members_count = db.session.query(func.count(func.distinct(EmployeeProject.employee_id))).join(Project).filter(Project.project_manager_id == emp_id, EmployeeProject.removed_at == None).scalar() or 0
        managed_projects = Project.query.filter_by(project_manager_id=emp_id).all()
        total_budget = sum(p.budget for p in managed_projects)
        total_expenses = db.session.query(func.sum(Expense.amount)).join(Project).filter(Project.project_manager_id == emp_id, Expense.status == 'Approved').scalar() or 0
        budget_used = f"{(total_expenses / total_budget * 100):.1f}%" if total_budget > 0 else '0%'

        stats = {
            'active_projects': Project.query.filter_by(project_manager_id=emp_id, status='In Progress').count(),
            'team_members': team_members_count,
            'pending_approvals': Expense.query.join(Project).filter(Project.project_manager_id==emp_id, Expense.status=='Pending').count() if emp_id else 0,
            'budget_used': budget_used
        }

        proj_status_data = db.session.query(Project.status, func.count(Project.id)).filter_by(project_manager_id=emp_id).group_by(Project.status).all()
        charts['projects_status'] = {
            'labels': [row[0] for row in proj_status_data],
            'data': [row[1] for row in proj_status_data]
        }

        return render_template('dashboard/manager.html', stats=stats, charts=charts)

    elif role_name == 'Accountant':
        stats = {
            'pending_payrolls': 0, 
            'unpaid_invoices': 0, 
            'expense_reports': Expense.query.filter_by(company_id=company_id, status='Pending').count(),
            'monthly_revenue': '$0' 
        }

        exp_status_data = db.session.query(Expense.status, func.count(Expense.id)).filter_by(company_id=company_id).group_by(Expense.status).all()
        charts['expenses_status'] = {
            'labels': [row[0] for row in exp_status_data],
            'data': [row[1] for row in exp_status_data]
        }

        return render_template('dashboard/accountant.html', stats=stats, charts=charts)

    elif role_name == 'Employee':
        emp_id = current_user.employee.id if current_user.employee else None
        stats = {
            'assigned_projects': EmployeeProject.query.filter_by(employee_id=emp_id, removed_at=None).count() if emp_id else 0,
            'pending_timesheets': 0, 
            'submitted_expenses': Expense.query.filter_by(employee_id=emp_id).count() if emp_id else 0,
            'next_payroll': 'N/A' 
        }

        my_exp_status = db.session.query(Expense.status, func.count(Expense.id)).filter_by(employee_id=emp_id).group_by(Expense.status).all()
        charts['my_expenses_status'] = {
            'labels': [row[0] for row in my_exp_status],
            'data': [row[1] for row in my_exp_status]
        }

        return render_template('dashboard/employee.html', stats=stats, charts=charts)

    else:
        abort(403)
