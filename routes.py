http://localhost:5000/superadmin/login?secret=master_key
http://localhost:5000/register?secret=admin_setup

docker-compose exec db psql -U DevTrack_Admin -d DevTrack_ERP

54.196.111.197

from app import db
from app.models import User, Company, Employee, Role, UserSession
old_superadmin = User.query.filter_by(email="superadmin@gmail.com").first()
if old_superadmin:
    # 1. Clear any active login sessions first
    UserSession.query.filter_by(user_id=old_superadmin.id).delete()
    
    # 2. Delete the associated employee
    old_employee = Employee.query.filter_by(user_id=old_superadmin.id).first()
    if old_employee:
        db.session.delete(old_employee)
        
    # 3. Delete the user
    db.session.delete(old_superadmin)
# 4. Delete the dummy company
dummy_company = Company.query.filter_by(company_name="System Admin").first()
if dummy_company:
    db.session.delete(dummy_company)
    
db.session.commit()
print("Old Super Admin and dummy company fully deleted!")