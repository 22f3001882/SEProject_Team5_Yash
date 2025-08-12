from celery.schedules import crontab
from flask import current_app as app
from backend_celery.tasks import (
    send_daily_spending_reminders, 
    send_weekly_spending_reminders,
    send_weekly_parent_summaries, 
    process_recurring_allowances
)

celery_app = app.extensions['celery']

@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Daily spending reminders at 6 PM
    sender.add_periodic_task(
        crontab(hour=15, minute=37), 
        send_daily_spending_reminders.s(), 
        name='Send daily spending reminders to children'
    )
    
    # Weekly spending reminders on Sundays at 10 AM
    sender.add_periodic_task(
        crontab(hour=15, minute=50, day_of_week=2), 
        send_weekly_spending_reminders.s(), 
        name='Send weekly spending reminders to children'
    )
    
    # Weekly parent summaries on Sundays at 8 PM
    sender.add_periodic_task(
        crontab(hour=15, minute=50, day_of_week=2), 
        send_weekly_parent_summaries.s(), 
        name='Send weekly financial summaries to parents'
    )
    
    # Daily check for recurring allowances at 9 AM
    sender.add_periodic_task(
        crontab(hour=17, minute=48), 
        process_recurring_allowances.s(), 
        name='Process recurring allowances'
    )