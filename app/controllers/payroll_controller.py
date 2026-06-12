from flask import current_app, render_template, redirect, url_for, flash, request
from flask_login import current_user
from app import db
from app.models import PayrollRun, PayrollItem, Employee, Timesheet, CompanyExpense
from app.forms import GeneratePayrollForm, EditPayrollItemForm
from app.utils.notifications import create_notification
from datetime import datetime
import calendar

def get_weekdays_in_month(year, month):
    num_days = calendar.monthrange(year, month)[1]
    weekdays = 0
    for day in range(1, num_days + 1):
        if calendar.weekday(year, month, day) < 5:
            weekdays += 1
    return weekdays

def list_runs_action():
    runs = PayrollRun.query.filter_by(company_id=current_user.company_id).order_by(PayrollRun.payroll_month.desc()).all()
    form = GeneratePayrollForm()
    return render_template('payroll/index.html', runs=runs, form=form, title='Payroll Management')

def generate_payroll_action():
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
            
            deductions = 0.0
            overtime_amount = 0.0
            
            if emp.employment_type == 'Hourly':
                base_salary = float(emp.hourly_rate or 0) * float(total_hours)
                net_salary = base_salary
            else:
                base_salary = float(emp.monthly_salary or 0)
                weekdays = get_weekdays_in_month(month.year, month.month)
                required_hours = weekdays * 8.0
                
                hourly_equivalent = base_salary / required_hours if required_hours > 0 else 0
                
                if total_hours < required_hours:
                    shortfall = required_hours - float(total_hours)
                    deductions = shortfall * hourly_equivalent
                elif total_hours > required_hours:
                    overtime_hours = float(total_hours) - required_hours
                    overtime_amount = overtime_hours * hourly_equivalent
                    
                net_salary = base_salary - deductions + overtime_amount
                
            item = PayrollItem(
                payroll_run_id=new_run.id,
                employee_id=emp.id,
                base_salary=base_salary,
                deductions=deductions,
                overtime_amount=overtime_amount,
                net_salary=net_salary
            )
            db.session.add(item)
            
        try:
            db.session.commit()
            flash('Payroll generated successfully.', 'success')
            return redirect(url_for('payroll_bp.view_run', run_id=new_run.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error generating payroll: {str(e)}')
            flash('Error generating payroll. Please try again.', 'danger')
        
    flash('Invalid form submission.', 'danger')
    return redirect(url_for('payroll_bp.list_runs'))

def view_run_action(run_id):
    run = PayrollRun.query.filter_by(id=run_id, company_id=current_user.company_id).first_or_404()
    
    search_query = request.args.get('search', '').strip()
    if search_query:
        items = [item for item in run.payroll_items if search_query.lower() in item.employee.full_name.lower()]
    else:
        items = run.payroll_items
        
    return render_template('payroll/view.html', run=run, items=items, search_query=search_query, title=f'Payroll Run - {run.payroll_month.strftime("%B %Y")}')

def edit_item_action(item_id):
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
        
        try:
            db.session.commit()
            flash('Payroll item updated successfully.', 'success')
            return redirect(url_for('payroll_bp.view_run', run_id=run.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating payroll item: {str(e)}')
            flash('Error updating payroll item. Please try again.', 'danger')
        
    elif request.method == 'GET':
        form.base_salary.data = item.base_salary
        form.overtime_amount.data = item.overtime_amount
        form.bonus_amount.data = item.bonus_amount
        form.deductions.data = item.deductions
        
    return render_template('payroll/edit_item.html', item=item, form=form, title='Edit Payroll Item')

def approve_run_action(run_id):
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
            
    try:
        db.session.commit()
        flash('Payroll run approved and finalized.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error approving payroll run: {str(e)}')
        flash('Error approving payroll run. Please try again.', 'danger')
    return redirect(url_for('payroll_bp.view_run', run_id=run.id))
