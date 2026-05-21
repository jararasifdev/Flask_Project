from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    role_name = current_user.role.name

    mock_stats = {
        'Admin': {
            'total_employees': 12,
            'total_projects': 8,
            'pending_expenses': '$1,250',
            'invoices_due': 3
        },
        'Project Manager': {
            'active_projects': 3,
            'team_members': 8,
            'pending_approvals': 5,
            'budget_used': '65%'
        },
        'Accountant': {
            'pending_payrolls': 12,
            'unpaid_invoices': 4,
            'expense_reports': 7,
            'monthly_revenue': '$45,000'
        },
        'Employee': {
            'assigned_projects': 2,
            'pending_timesheets': 1,
            'submitted_expenses': '$120',
            'next_payroll': 'Oct 31'
        }
    }

    if role_name == 'Admin':
        return render_template('dashboard/admin.html', stats=mock_stats['Admin'])
    elif role_name == 'Project Manager':
        return render_template('dashboard/manager.html', stats=mock_stats['Project Manager'])
    elif role_name == 'Accountant':
        return render_template('dashboard/accountant.html', stats=mock_stats['Accountant'])
    elif role_name == 'Employee':
        return render_template('dashboard/employee.html', stats=mock_stats['Employee'])
    else:
        abort(403)
