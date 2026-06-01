import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models.project import Project
from app.models.expense import Expense, ExpenseCategory, BudgetAlert
from app.forms.expense_forms import ExpenseForm, ExpenseReviewForm, ExpenseCategoryForm
from app.utils.decorators import role_required

expenses_bp = Blueprint('expenses_bp', __name__, url_prefix='/expenses')

def check_budget_threshold(project):
    total_approved = sum(exp.amount for exp in project.expenses if exp.status == 'Approved')
    budget = project.budget
    if budget > 0:
        percentage = (total_approved / budget) * 100
        if percentage >= 100:
            alert = BudgetAlert(
                company_id=project.company_id,
                project_id=project.id,
                alert_type='Budget Exceeded',
                message=f'Project has exceeded its budget of {budget}. Current expenses: {total_approved}'
            )
            db.session.add(alert)
        elif percentage >= 80:
            alert = BudgetAlert(
                company_id=project.company_id,
                project_id=project.id,
                alert_type='Budget Warning',
                message=f'Project has reached {percentage:.1f}% of its budget.'
            )
            db.session.add(alert)

@expenses_bp.route('/', methods=['GET'])
@login_required
def list_expenses():
    if current_user.role.name == 'Employee':
        emp_id = current_user.employee.id if current_user.employee else None
        expenses = Expense.query.filter_by(company_id=current_user.company_id, employee_id=emp_id).all()
    else:
        expenses = Expense.query.filter_by(company_id=current_user.company_id).all()
    return render_template('expenses/index.html', expenses=expenses)

@expenses_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_expense():
    form = ExpenseForm()
    
    if current_user.role.name == 'Employee':
        emp_id = current_user.employee.id if current_user.employee else None
        from app.models.project import EmployeeProject
        projects = Project.query.join(EmployeeProject).filter(
            Project.company_id == current_user.company_id,
            EmployeeProject.employee_id == emp_id,
            EmployeeProject.removed_at == None
        ).all()
    else:
        projects = Project.query.filter_by(company_id=current_user.company_id).all()
        
    form.project_id.choices = [(p.id, p.name) for p in projects]
    
    categories = ExpenseCategory.query.filter_by(company_id=current_user.company_id).all()
    form.category_id.choices = [(c.id, c.name) for c in categories]

    if form.validate_on_submit():
        filename = None
        if form.receipt_file.data:
            f = form.receipt_file.data
            filename = secure_filename(f.filename)
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'receipts')
            os.makedirs(upload_dir, exist_ok=True)
            f.save(os.path.join(upload_dir, filename))
            
        expense = Expense(
            company_id=current_user.company_id,
            project_id=form.project_id.data,
            employee_id=current_user.employee.id if current_user.employee else None,
            category_id=form.category_id.data,
            amount=form.amount.data,
            description=form.description.data,
            receipt_file=filename,
            status='Pending'
        )
        if not expense.employee_id:
            flash('You must have an associated employee profile to submit an expense.', 'danger')
            return redirect(url_for('expenses_bp.list_expenses'))
            
        db.session.add(expense)
        db.session.commit()
        flash('Expense submitted successfully!', 'success')
        return redirect(url_for('expenses_bp.list_expenses'))

    return render_template('expenses/submit.html', form=form)

@expenses_bp.route('/<expense_id>/review', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Project Manager', 'Accountant')
def review_expense(expense_id):

    expense = Expense.query.filter_by(id=expense_id, company_id=current_user.company_id).first_or_404()
    form = ExpenseReviewForm()

    if form.validate_on_submit():
        expense.status = form.status.data
        expense.approved_by_employee_id = current_user.employee.id if current_user.employee else None
        
        db.session.commit()
        
        if expense.status == 'Approved':
            check_budget_threshold(expense.project)
            db.session.commit()
            
        flash(f'Expense {expense.status.lower()} successfully.', 'success')
        return redirect(url_for('expenses_bp.list_expenses'))

    return render_template('expenses/review.html', form=form, expense=expense)

@expenses_bp.route('/categories', methods=['GET', 'POST'])
@login_required
def manage_categories():

    form = ExpenseCategoryForm()
    if form.validate_on_submit():
        category = ExpenseCategory(
            company_id=current_user.company_id,
            name=form.name.data,
            description=form.description.data
        )
        db.session.add(category)
        db.session.commit()
        flash('Category added successfully!', 'success')
        return redirect(url_for('expenses_bp.manage_categories'))
        
    categories = ExpenseCategory.query.filter_by(company_id=current_user.company_id).all()
    return render_template('expenses/categories.html', form=form, categories=categories)
