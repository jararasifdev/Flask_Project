import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import db
from datetime import datetime
from app.models.project import Project, EmployeeProject
from app.models.expense import Expense, ExpenseCategory, BudgetAlert
from app.models.company_expense import CompanyExpense
from app.models.project import EmployeeProject
from app.utils.notifications import create_notification
from app.forms.expense_forms import ExpenseForm, ExpenseReviewForm, ExpenseCategoryForm
from app.utils.decorators import role_required
from app.models.user import User
from app.models.role import Role

expenses_bp = Blueprint('expenses_bp', __name__, url_prefix='/expenses')

@expenses_bp.route('/company', methods=['GET'])
@login_required
@role_required('Admin', 'Accountant')
def list_company_expenses():
    expenses = CompanyExpense.query.filter_by(company_id=current_user.company_id).order_by(CompanyExpense.expense_date.desc()).all()
    total_overhead = sum(e.amount for e in expenses)
    return render_template('expenses/company.html', expenses=expenses, total_overhead=total_overhead, title='Company Expenses')

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
        if percentage >= 100 or percentage >= 80:
            if project.project_manager_id and project.project_manager and project.project_manager.user_id:
                pm_user_id = project.project_manager.user_id
                create_notification(
                    company_id=project.company_id,
                    user_id=pm_user_id,
                    type_name='Budget Alert',
                    title='Budget Exceeded' if percentage >= 100 else 'Budget Warning',
                    message=f'Project {project.name} budget status: {percentage:.1f}%'
                )
                
            admin_role = Role.query.filter_by(name='Admin').first()
            admins = User.query.filter_by(company_id=project.company_id, role_id=admin_role.id).all() if admin_role else []
            for admin in admins:
                create_notification(
                    company_id=project.company_id,
                    user_id=admin.id,
                    type_name='Budget Alert',
                    title='Budget Exceeded' if percentage >= 100 else 'Budget Warning',
                    message=f'Project {project.name} budget status: {percentage:.1f}%'
                )

@expenses_bp.route('/', methods=['GET'])
@login_required
def list_expenses():
    status_filter = request.args.get('status')
    project_filter = request.args.get('project_id')

    query = Expense.query

    if current_user.role.name == 'Employee':
        emp_id = current_user.employee.id if current_user.employee else None
        query = query.filter_by(company_id=current_user.company_id, employee_id=emp_id)
        projects = Project.query.join(EmployeeProject).filter(
            Project.company_id == current_user.company_id,
            EmployeeProject.employee_id == emp_id,
            EmployeeProject.removed_at == None
        ).all()
    elif current_user.role.name == 'Project Manager':
        emp_id = current_user.employee.id if current_user.employee else None
        query = query.join(Project).filter(
            Expense.company_id == current_user.company_id,
            db.or_(Expense.employee_id == emp_id, Project.project_manager_id == emp_id)
        )
        projects = Project.query.filter(
            Project.company_id == current_user.company_id,
            Project.project_manager_id == emp_id
        ).all()
    else:
        query = query.filter_by(company_id=current_user.company_id)
        projects = Project.query.filter_by(company_id=current_user.company_id).all()

    if status_filter:
        query = query.filter(Expense.status == status_filter)
    if project_filter:
        query = query.filter(Expense.project_id == project_filter)

    expenses = query.order_by(Expense.submitted_at.desc()).all()

    return render_template('expenses/index.html', expenses=expenses, projects=projects, current_status=status_filter, current_project=project_filter, title='Expenses')

@expenses_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_expense():
    form = ExpenseForm()
    
    if current_user.role.name == 'Employee':
        emp_id = current_user.employee.id if current_user.employee else None
        projects = Project.query.join(EmployeeProject).filter(
            Project.company_id == current_user.company_id,
            EmployeeProject.employee_id == emp_id,
            EmployeeProject.removed_at == None
        ).all()
    elif current_user.role.name == 'Project Manager':
        emp_id = current_user.employee.id if current_user.employee else None
        projects = Project.query.outerjoin(EmployeeProject, 
            db.and_(EmployeeProject.project_id == Project.id, EmployeeProject.removed_at == None)
        ).filter(
            Project.company_id == current_user.company_id,
            db.or_(EmployeeProject.employee_id == emp_id, Project.project_manager_id == emp_id)
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
        
        project = Project.query.get(expense.project_id)
        admin_role = Role.query.filter_by(name='Admin').first()
        admins = User.query.filter_by(company_id=current_user.company_id, role_id=admin_role.id).all() if admin_role else []
        
        if project and project.project_manager and project.project_manager.user_id:
            pm_user_id = project.project_manager.user_id
            if pm_user_id != current_user.id:
                create_notification(
                    company_id=current_user.company_id,
                    user_id=pm_user_id,
                    type_name='New Expense',
                    title='New Expense Submitted',
                    message=f"{current_user.employee.full_name} submitted a new expense of ${expense.amount} for project '{project.name}'."
                )
                
        for admin in admins:
            if admin.id != current_user.id:
                create_notification(
                    company_id=current_user.company_id,
                    user_id=admin.id,
                    type_name='New Expense',
                    title='New Expense Submitted',
                    message=f"{current_user.employee.full_name} submitted a new expense of ${expense.amount} for project '{project.name}'."
                )
                
        db.session.commit()

        flash('Expense submitted successfully!', 'success')
        return redirect(url_for('expenses_bp.list_expenses'))

    return render_template('expenses/submit.html', form=form)

@expenses_bp.route('/<expense_id>/review', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Project Manager', 'Accountant')
def review_expense(expense_id):

    expense = Expense.query.filter_by(id=expense_id, company_id=current_user.company_id).first_or_404()
    
    if current_user.role.name == 'Project Manager':
        emp_id = current_user.employee.id if current_user.employee else None
        if expense.project.project_manager_id != emp_id:
            flash('Unauthorized to review this expense.', 'danger')
            return redirect(url_for('expenses_bp.list_expenses'))
            
    form = ExpenseReviewForm()

    if form.validate_on_submit():
        expense.status = form.status.data
        expense.approved_by_employee_id = current_user.employee.id if current_user.employee else None
        expense.approved_at = datetime.utcnow()
        
        db.session.commit()
        
        if expense.status == 'Approved':
            check_budget_threshold(expense.project)
            db.session.commit()
        
        if expense.employee and expense.employee.user_id:
            create_notification(
                company_id=current_user.company_id,
                user_id=expense.employee.user_id,
                type_name='Expense Update',
                title=f'Expense {expense.status}',
                message=f'Your expense of ${expense.amount} for project {expense.project.name} has been {expense.status.lower()}.'
            )
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
