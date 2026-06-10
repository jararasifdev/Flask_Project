from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import PayrollRun, PayrollItem, Employee, Timesheet, CompanyExpense
from app.forms import GeneratePayrollForm, EditPayrollItemForm
from app.utils.decorators import role_required
from app.utils.notifications import create_notification
from datetime import datetime
import calendar

payroll_bp = Blueprint('payroll_bp', __name__)

@payroll_bp.route('/payroll', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Accountant')
def list_runs():
    runs = PayrollRun.query.filter_by(company_id=current_user.company_id).order_by(PayrollRun.payroll_month.desc()).all()
    form = GeneratePayrollForm()
    
    if form.validate_on_submit():
        month = form.payroll_month.data

        existing_run = PayrollRun.query.filter_by(company_id=current_user.company_id, payroll_month=month).first()
        if existing_run:
            flash(f'Payroll for {month.strftime("%B %Y")} already exists.', 'warning')
            return redirect(url_for('payroll_bp.list_runs'))
            
        new_run = PayrollRun(
            company_id=current_user.company_id,
            payroll_month=month,
            generated_by_employee_id=current_user.employee.id if current_user.employee else None
        )
        db.session.add(new_run)
        db.session.flush()
 
        employees = Employee.query.filter_by(company_id=current_user.company_id).all()
        for emp in employees:
            if emp.user and emp.user.role.name == 'Admin':
                continue
                
            if emp.employment_type == 'Hourly':
                start_date = month.replace(day=1)
                last_day = calendar.monthrange(month.year, month.month)[1]
                end_date = month.replace(day=last_day)
                
                approved_timesheets = Timesheet.query.filter(
                    Timesheet.employee_id == emp.id,
                    Timesheet.work_date >= start_date,
                    Timesheet.work_date <= end_date,
                    Timesheet.status == 'Approved'
                ).all()
                total_hours = sum(ts.total_hours for ts in approved_timesheets)
                base_salary = float(emp.hourly_rate or 0) * float(total_hours)
            else:
                base_salary = float(emp.monthly_salary or 0)
                
            item = PayrollItem(
                payroll_run_id=new_run.id,
                employee_id=emp.id,
                base_salary=base_salary,
                net_salary=base_salary
            )
            db.session.add(item)
            
        db.session.commit()
        flash('Payroll generated successfully.', 'success')
        return redirect(url_for('payroll_bp.view_run', run_id=new_run.id))
        
    return render_template('payroll/index.html', runs=runs, form=form, title='Payroll Management')

@payroll_bp.route('/payroll/<run_id>', methods=['GET'])
@login_required
@role_required('Admin', 'Accountant')
def view_run(run_id):
    run = PayrollRun.query.filter_by(id=run_id, company_id=current_user.company_id).first_or_404()
    
    search_query = request.args.get('search', '').strip()
    if search_query:
        items = [item for item in run.payroll_items if search_query.lower() in item.employee.full_name.lower()]
    else:
        items = run.payroll_items
        
    return render_template('payroll/view.html', run=run, items=items, search_query=search_query, title=f'Payroll Run - {run.payroll_month.strftime("%B %Y")}')

@payroll_bp.route('/payroll/item/<item_id>', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Accountant')
def edit_item(item_id):
    item = PayrollItem.query.join(PayrollRun).filter(PayrollItem.id == item_id, PayrollRun.company_id == current_user.company_id).first_or_404()
    run = item.payroll_run
    
    if run.status != 'Draft':
        flash('Cannot edit items for a finalized payroll run.', 'danger')
        return redirect(url_for('payroll_bp.view_run', run_id=run.id))
        
    form = EditPayrollItemForm()
    
    if form.validate_on_submit():
        item.base_salary = form.base_salary.data
        item.overtime_amount = form.overtime_amount.data or 0
        item.bonus_amount = form.bonus_amount.data or 0
        item.deductions = form.deductions.data or 0
        item.net_salary = item.base_salary + item.overtime_amount + item.bonus_amount - item.deductions
        
        db.session.commit()
        flash('Payroll item updated successfully.', 'success')
        return redirect(url_for('payroll_bp.view_run', run_id=run.id))
        
    elif request.method == 'GET':
        form.base_salary.data = item.base_salary
        form.overtime_amount.data = item.overtime_amount
        form.bonus_amount.data = item.bonus_amount
        form.deductions.data = item.deductions
        
    return render_template('payroll/edit_item.html', item=item, form=form, title='Edit Payroll Item')

@payroll_bp.route('/payroll/<run_id>/approve', methods=['POST'])
@login_required
@role_required('Admin', 'Accountant')
def approve_run(run_id):
    run = PayrollRun.query.filter_by(id=run_id, company_id=current_user.company_id).first_or_404()
    run.status = 'Approved'
    for item in run.payroll_items:
        item.status = 'Paid'
        
        if item.employee.user_id:
            create_notification(
                company_id=current_user.company_id,
                user_id=item.employee.user_id,
                type_name='Payroll Generation',
                title='Payroll Finalized',
                message=f'Your payroll for {run.payroll_month.strftime("%B %Y")} has been finalized. Net salary: ${item.net_salary:.2f}.'
            )
            
        if item.net_salary > 0:
            expense = CompanyExpense(
                company_id=current_user.company_id,
                title=f"Payroll - {item.employee.full_name} - {run.payroll_month.strftime('%b %Y')}",
                amount=item.net_salary,
                expense_date=datetime.now().date(),
                description=f"Payroll disbursement for {item.employee.full_name} for the month of {run.payroll_month.strftime('%B %Y')}."
            )
            db.session.add(expense)
            
    db.session.commit()
    flash('Payroll run approved and finalized.', 'success')
    return redirect(url_for('payroll_bp.view_run', run_id=run.id))
