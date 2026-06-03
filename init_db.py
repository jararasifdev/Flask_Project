from app import create_app, db
from app.models import Role

app = create_app()

def init_db():
    with app.app_context():
        print("Populating roles...")
        roles = [
            {'name': 'Admin', 'description': 'Full system management'},
            {'name': 'Accountant', 'description': 'Payroll, invoices, expenses, and financial management'},
            {'name': 'Project Manager', 'description': 'Project and team management'},
            {'name': 'Employee', 'description': 'Expense submission and time tracking'}
        ]
        
        for role_data in roles:
            role = Role.query.filter_by(name=role_data['name']).first()
            if not role:
                role = Role(name=role_data['name'], description=role_data['description'])
                db.session.add(role)
                print(f"Added role: {role_data['name']}")
        
        db.session.commit()
        print("Database initialization complete.")

if __name__ == '__main__':
    init_db()
