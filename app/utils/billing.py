from datetime import datetime, timedelta, timezone
from app import db
from app.models import Expense, Invoice, InvoiceItem, Project

def generate_weekly_invoices():
    """
    Finds all approved, uninvoiced expenses and generates weekly invoices per project.
    Groups expenses by project and creates an invoice with line items for each expense.
    """
    try:
        expenses = Expense.query.filter_by(
            status='Approved',
            is_invoiced=False
        ).all()

        if not expenses:
            print("No new approved expenses to invoice.")
            return

        grouped_expenses = {}
        for expense in expenses:
            if expense.project_id not in grouped_expenses:
                grouped_expenses[expense.project_id] = []
            grouped_expenses[expense.project_id].append(expense)

        for project_id, project_expenses in grouped_expenses.items():
            project = Project.query.get(project_id)
            if not project:
                continue

            company_id = project.company_id
            client_id = project.client_id
            
            date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
            today_invoices = Invoice.query.filter(
                Invoice.company_id == company_id,
                Invoice.invoice_number.like(f"INV-{date_str}-%")
            ).count()
            
            invoice_number = f"INV-{date_str}-{today_invoices + 1:03d}"
            
            issue_date = datetime.now(timezone.utc).date()
            due_date = issue_date + timedelta(days=14)

            invoice = Invoice(
                company_id=company_id,
                project_id=project_id,
                client_id=client_id,
                status='Draft',
                invoice_number=invoice_number,
                issue_date=issue_date,
                due_date=due_date,
                notes="Automated weekly invoice for project expenses and billable hours."
            )
            db.session.add(invoice)
            db.session.flush()

            subtotal = 0.0

            for expense in project_expenses:
                description = f"Expense: {expense.category.name}"
                if expense.description:
                    description += f" - {expense.description}"

                item = InvoiceItem(
                    invoice_id=invoice.id,
                    description=description,
                    quantity=1.0,
                    rate=expense.amount,
                    amount=expense.amount
                )
                db.session.add(item)
                
                subtotal += float(expense.amount)
                
                expense.is_invoiced = True
                expense.invoice_id = invoice.id
            
            invoice.subtotal = subtotal
            invoice.total_amount = subtotal + float(invoice.tax_amount or 0.0)

        db.session.commit()
        print(f"Successfully generated invoices for {len(grouped_expenses)} projects.")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error generating weekly invoices: {str(e)}")
