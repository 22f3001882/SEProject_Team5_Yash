from celery import Celery, Task
from flask import Flask
from celery.schedules import crontab

class CeleryConfig():
    broker_url = 'redis://localhost:6379/0'
    result_backend = 'redis://localhost:6379/1'
    timezone = 'Asia/Kolkata'
    beat_schedule = {
        # Daily spending reminders at 6 PM
        'send-daily-spending-reminders': {
            'task': 'tasks.send_daily_spending_reminders',
            'schedule': crontab(hour=18, minute=0),
        },
        # Weekly spending reminders on Sundays at 10 AM
        'send-weekly-spending-reminders': {
            'task': 'tasks.send_weekly_spending_reminders',
            'schedule': crontab(hour=10, minute=0, day_of_week=0),
        },
        # Weekly parent summaries on Sundays at 8 PM
        'send-weekly-parent-summaries': {
            'task': 'tasks.send_weekly_parent_summaries',
            'schedule': crontab(hour=20, minute=0, day_of_week=0),
        },
        # Daily check for recurring allowances at 9 AM
        'process-recurring-allowances': {
            'task': 'tasks.process_recurring_allowances',
            'schedule': crontab(hour=9, minute=0),
        },
    }


def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(CeleryConfig)
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app