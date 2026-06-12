# DevTrack ERP

DevTrack ERP is a robust, multi-tenant SaaS application built with Flask and Python, designed to streamline project management, time tracking, expense reporting, invoicing, and payroll for modern businesses. 

Built with enterprise-grade architecture, it features strict Role-Based Access Control (RBAC), data isolation between tenants, and a secure backend powered by SQLAlchemy and WTForms.

---

## 🚀 Key Features

### 🏢 Multi-Tenant SaaS Architecture
- **Super Admin Portal:** A dedicated platform administrator can effortlessly provision, suspend, and manage multiple isolated companies (tenants).
- **Data Isolation:** Every database query is strictly scoped by `company_id`, ensuring 100% data privacy between different companies.

### 🔐 Role-Based Access Control (RBAC)
Custom middleware enforces access across five distinct roles:
1. **Super Admin:** Platform management and company provisioning.
2. **Admin:** Full access to their company's settings, payroll, and financials.
3. **Project Manager:** Can manage assigned projects, approve timesheets, and review project expenses.
4. **Accountant:** Global access to invoices, payroll processing, and financial reporting.
5. **Employee:** Standard access to log time, submit expenses, and view personal profiles.

### 💼 Project & Time Management
- Create projects, assign employees, and set strict financial budgets.
- Employees can log billable and non-billable hours via Timesheets.
- Automated budget threshold alerts notify managers when a project is nearing its spending limit.

### 💰 Finance & Invoicing
- **Dynamic Itemized Billing:** Instantly generate invoices from approved, billable timesheets.
- **Payment Tracking:** Log partial or full payments. Invoice statuses automatically transition from "Sent" to "Partial" to "Paid" based on remaining balances.
- **Expense Tracking:** Employees can submit reimbursable expenses, which flow directly into project cost calculations.

### 🏦 Payroll Processing
- Automated monthly payroll generation.
- Supports distinct logic for **Full-time (Monthly)** and **Hourly** employees.
- Dynamically integrates allowances, deductions, and approved timesheets to calculate precise `net_salary`.

### 🔔 Real-Time Notifications
- System-wide notification center to alert users of timesheet approvals, project assignments, and budget warnings.

---

## 🛠 Tech Stack

- **Backend:** Python, Flask, Gunicorn
- **Database:** PostgreSQL, SQLAlchemy (ORM), Alembic (Migrations)
- **Security:** Flask-Bcrypt, WTForms (Backend Validation & CSRF Protection)
- **Frontend:** HTML5, Jinja2 Templates, Bootstrap 5
- **DevOps:** Docker, Docker Compose

---

## 🗄️ Database Models

The application's data is structured into the following SQLAlchemy models (found in `app/models/`):

- **[Company](app/models/company.py)**: Represents the tenant in our SaaS.
- **[User](app/models/user.py)** & **[Role](app/models/role.py)**: Core authentication and RBAC.
- **[Employee](app/models/employee.py)** & **[Department](app/models/department.py)**: Employee profiles, HR data, and organizational structure.
- **[Project](app/models/project.py)** & **[Client](app/models/client.py)**: Project management, budgets, and client relations.
- **[Timesheet](app/models/timesheet.py)**: Employee time logging against projects.
- **[Expense](app/models/expense.py)** & **[Company Expense](app/models/company_expense.py)**: Project-specific expenses, expense categories, budget alerts, and overall company overheads.
- **[Invoice](app/models/invoice.py)**: Client billing, itemized invoice entries, and payment tracking.
- **[Payroll](app/models/payroll.py)**: Monthly payroll runs and individual employee payroll items.
- **[Notification](app/models/notification.py)**: System notifications for users.
- **[Report](app/models/report.py)**: Saved financial and project reports.
- **[User Session](app/models/user_session.py)**: Tracking active user sessions for security and auditing.

---

## 💻 Local Development Setup

### Prerequisites
- Docker and Docker Compose installed on your machine.
- Git.

### 1. Clone the Repository
```bash
git clone <repository-url>
cd FLASK_FINAL_PROJECT
```

### 2. Configure Environment Variables
Copy the example environment file and configure your secrets:
```bash
cp .env.example .env
```
Ensure your `.env` file contains strong, secure values:
```env
DB_USER=DevTrack_Admin
DB_PASSWORD=YourSecurePassword123!
DB_NAME=DevTrack_ERP
SECRET_KEY=your_cryptographically_secure_random_key
```

### 3. Spin Up the Containers
Build and start the application using Docker Compose:
```bash
docker-compose up --build -d
```
*Note: The database volume is persistent. If you run `docker-compose down`, your data will safely remain on your host machine.*

### 4. Access the Application
- The web app will be available at `http://localhost:8000`

---

## 🛡 Security Notes

- **Never** commit the `.env` file to version control.
- All form submissions are protected against Cross-Site Request Forgery (CSRF) via WTForms.
- Database IDs and Foreign Keys are strictly validated (`coerce=int`) to prevent injection and forced browsing attacks.
- Do not run the APScheduler in a multi-worker Gunicorn environment without a dedicated lock or job store to prevent duplicate job executions.

---

