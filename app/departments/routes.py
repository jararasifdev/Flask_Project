from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Department
from app.forms import DepartmentForm
from app.utils.decorators import role_required

departments_bp = Blueprint('departments_bp', __name__)

@departments_bp.route('/departments')
@login_required
@role_required('Admin')
def list_departments():
    departments = Department.query.filter_by(company_id=current_user.company_id).all()
    return render_template('departments/list.html', departments=departments, title="Manage Departments")

@departments_bp.route('/departments/create', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def create_department():
    form = DepartmentForm()
    if form.validate_on_submit():
        dept = Department(
            company_id=current_user.company_id,
            name=form.name.data,
            description=form.description.data
        )
        db.session.add(dept)
        db.session.commit()
        flash('Department created successfully.', 'success')
        return redirect(url_for('departments_bp.list_departments'))
    return render_template('departments/create.html', form=form, title="Create Department")

@departments_bp.route('/departments/<department_id>/delete', methods=['POST'])
@login_required
@role_required('Admin')
def delete_department(department_id):
    department = Department.query.filter_by(id=department_id, company_id=current_user.company_id).first_or_404()
    
    if department.employees:
        flash('Cannot delete department because it contains employees.', 'danger')
        return redirect(url_for('departments_bp.list_departments'))

    db.session.delete(department)
    db.session.commit()
    flash('Department deleted successfully.', 'success')
    return redirect(url_for('departments_bp.list_departments'))
