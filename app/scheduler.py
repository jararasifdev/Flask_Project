from flask_apscheduler import APScheduler
from app.utils.billing import generate_weekly_invoices

scheduler = APScheduler()

def init_scheduler(app):
    scheduler.init_app(app)
    
    def run_weekly_billing():
        with app.app_context():
            
            generate_weekly_invoices()

    scheduler.add_job(id='weekly_invoices', func=run_weekly_billing, trigger='cron', day_of_week='fri', hour=23, minute=59)
    scheduler.start()

