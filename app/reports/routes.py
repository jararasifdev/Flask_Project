from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import Expense, Project, Employee, Invoice, PayrollItem, PayrollRun, EmployeeProject
from app.utils.decorators import role_required
from datetime import datetime, timedelta
import math

reports_bp = Blueprint('reports_bp', __name__)

@reports_bp.route('/reports')
@login_required
@role_required('Admin', 'Accountant', 'Project Manager')
def dashboard():
    company_id = current_user.company_id
    
    timeframe = request.args.get('timeframe', 'all_time')
    today = datetime.now()
    start_date = None
    end_date = None
    
    if timeframe == 'this_month':
        start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = today
    elif timeframe == 'last_month':
        first_day_of_this_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = first_day_of_this_month - timedelta(seconds=1)
        start_date = end_date.replace(day=1)
    elif timeframe == 'this_quarter':
        current_quarter = math.ceil(today.month / 3)
        start_month = 3 * current_quarter - 2
        start_date = today.replace(month=start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = today
    elif timeframe == 'last_quarter':
        current_quarter = math.ceil(today.month / 3)
        if current_quarter == 1:
            start_month = 10
            start_date = today.replace(year=today.year-1, month=start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start_month = 3 * (current_quarter - 1) - 2
            start_date = today.replace(month=start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        if start_month == 10:
            next_quarter_start = start_date.replace(year=start_date.year + 1, month=1)
        else:
            next_quarter_start = start_date.replace(month=start_month + 3)
        end_date = next_quarter_start - timedelta(seconds=1)
    elif timeframe == 'custom':
        start_str = request.args.get('start_date')
        end_str = request.args.get('end_date')
        if start_str:
            try:
                start_date = datetime.strptime(start_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid start date format. Please use YYYY-MM-DD.', 'danger')
        if end_str:
            try:
                end_date = datetime.strptime(end_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            except ValueError:
                flash('Invalid end date format. Please use YYYY-MM-DD.', 'danger')
        
    if current_user.role.name == 'Project Manager':
        emp_id = current_user.employee.id if current_user.employee else None
        projects = Project.query.filter_by(company_id=company_id, project_manager_id=emp_id).all()
    else:
        projects = Project.query.filter_by(company_id=company_id).all()
        
    project_names = [p.name for p in projects]
    project_budgets = [float(p.budget) for p in projects]
    
    project_expenses = []
    for p in projects:
        approved_project_expenses = [expense for expense in p.expenses if expense.status == 'Approved']
        if start_date and end_date:
            approved_project_expenses = [expense for expense in approved_project_expenses if expense.created_at and start_date <= expense.created_at <= end_date]
        project_expenses.append(float(sum(expense.amount for expense in approved_project_expenses)))
    
    if current_user.role.name == 'Project Manager':
        project_ids = [p.id for p in projects]
        invoices_query = Invoice.query.filter(Invoice.company_id==company_id, Invoice.project_id.in_(project_ids)) if project_ids else None
        all_expenses_query = Expense.query.filter(Expense.company_id==company_id, Expense.status=='Approved', Expense.project_id.in_(project_ids)) if project_ids else None
    
        if project_ids:
            employees = Employee.query.join(EmployeeProject).filter(
                EmployeeProject.project_id.in_(project_ids),
                EmployeeProject.removed_at == None
            ).distinct().all()
        else:
            employees = []
            
        employee_ids = [e.id for e in employees]
        payroll_items_query = PayrollItem.query.join(Employee).filter(Employee.id.in_(employee_ids)) if employee_ids else None
    else:
        invoices_query = Invoice.query.filter_by(company_id=company_id)
        all_expenses_query = Expense.query.filter_by(company_id=company_id, status='Approved')
        payroll_items_query = PayrollItem.query.join(Employee).filter(Employee.company_id == company_id)
        employees = Employee.query.filter_by(company_id=company_id).all()
        
    if start_date and end_date:
        if invoices_query is not None:
            invoices_query = invoices_query.filter(Invoice.created_at >= start_date, Invoice.created_at <= end_date)
        if all_expenses_query is not None:
            all_expenses_query = all_expenses_query.filter(Expense.created_at >= start_date, Expense.created_at <= end_date)
        if payroll_items_query is not None:
            payroll_items_query = payroll_items_query.join(PayrollRun, PayrollRun.id == PayrollItem.payroll_run_id).filter(PayrollRun.payroll_month >= start_date.date(), PayrollRun.payroll_month <= end_date.date())

    invoices = invoices_query.all() if invoices_query is not None else []
    all_expenses = all_expenses_query.all() if all_expenses_query is not None else []
    payroll_items = payroll_items_query.all() if payroll_items_query is not None else []
        
    total_income = sum(float(i.total_amount) for i in invoices if i.status in ['Paid', 'Partial', 'Sent'])
    total_expense = sum(float(e.amount) for e in all_expenses)
    total_payroll = sum(float(pi.net_salary) for pi in payroll_items)
    total_costs = total_expense + total_payroll
    employees = [e for e in employees if e.user and e.user.role.name != 'Admin']
    
    employee_names = [e.full_name for e in employees]
    employee_costs = []
    for emp in employees:
        employee_payroll_items = emp.payroll_items
        approved_expenses = [expense for expense in emp.submitted_expenses if expense.status == 'Approved']
        
        if start_date and end_date:
            employee_payroll_items = [payroll_item for payroll_item in employee_payroll_items if payroll_item.payroll_run and start_date.date() <= payroll_item.payroll_run.payroll_month <= end_date.date()]
            approved_expenses = [expense for expense in approved_expenses if expense.created_at and start_date <= expense.created_at <= end_date]
            
        emp_payroll = sum(float(payroll_item.net_salary) for payroll_item in employee_payroll_items)
        emp_expenses = sum(float(expense.amount) for expense in approved_expenses)
        employee_costs.append(emp_payroll + emp_expenses)
        
    return render_template('reports/index.html', 
        project_names=project_names, 
        project_budgets=project_budgets, 
        project_expenses=project_expenses,
        total_income=total_income,
        total_costs=total_costs,
        employee_names=employee_names,
        employee_costs=employee_costs,
        timeframe=timeframe,
        title='Financial Reports'
    )
