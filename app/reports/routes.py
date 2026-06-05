from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Expense, Project, Employee, Invoice, PayrollItem
from app.utils.decorators import role_required

reports_bp = Blueprint('reports_bp', __name__)

@reports_bp.route('/reports')
@login_required
@role_required('Admin', 'Accountant', 'Project Manager')
def dashboard():
    company_id = current_user.company_id
    
    if current_user.role.name == 'Project Manager':
        emp_id = current_user.employee.id if current_user.employee else None
        projects = Project.query.filter_by(company_id=company_id, project_manager_id=emp_id).all()
    else:
        projects = Project.query.filter_by(company_id=company_id).all()
        
    project_names = [p.name for p in projects]
    project_budgets = [float(p.budget) for p in projects]
    project_expenses = [float(sum(e.amount for e in p.expenses if e.status == 'Approved')) for p in projects]
    
    if current_user.role.name == 'Project Manager':
        project_ids = [p.id for p in projects]
        invoices = Invoice.query.filter(Invoice.company_id==company_id, Invoice.project_id.in_(project_ids)).all() if project_ids else []
        all_expenses = Expense.query.filter(Expense.company_id==company_id, Expense.status=='Approved', Expense.project_id.in_(project_ids)).all() if project_ids else []
        
        from app.models.project import EmployeeProject
        if project_ids:
            employees = Employee.query.join(EmployeeProject).filter(
                EmployeeProject.project_id.in_(project_ids),
                EmployeeProject.removed_at == None
            ).distinct().all()
        else:
            employees = []
            
        employee_ids = [e.id for e in employees]
        payroll_items = PayrollItem.query.join(Employee).filter(Employee.id.in_(employee_ids)).all() if employee_ids else []
    else:
        invoices = Invoice.query.filter_by(company_id=company_id).all()
        all_expenses = Expense.query.filter_by(company_id=company_id, status='Approved').all()
        payroll_items = PayrollItem.query.join(Employee).filter(Employee.company_id == company_id).all()
        employees = Employee.query.filter_by(company_id=company_id).all()
        
    total_income = sum(float(i.total_amount) for i in invoices if i.status in ['Paid', 'Partial', 'Sent'])
    total_expense = sum(float(e.amount) for e in all_expenses)
    total_payroll = sum(float(pi.net_salary) for pi in payroll_items)
    
    total_costs = total_expense + total_payroll
    
    employee_names = [e.full_name for e in employees]
    employee_costs = []
    for emp in employees:
        emp_payroll = sum(float(pi.net_salary) for pi in emp.payroll_items)
        emp_expenses = sum(float(e.amount) for e in emp.submitted_expenses if e.status == 'Approved')
        employee_costs.append(emp_payroll + emp_expenses)
        
    return render_template('reports/index.html', 
        project_names=project_names, 
        project_budgets=project_budgets, 
        project_expenses=project_expenses,
        total_income=total_income,
        total_costs=total_costs,
        employee_names=employee_names,
        employee_costs=employee_costs,
        title='Financial Reports'
    )
