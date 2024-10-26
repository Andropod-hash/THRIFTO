# myproject/celery.py
from celery import Celery
from celery.schedules import crontab  # Ensure this import is included
import os

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

# Create the Celery app
app = Celery('myproject')

# Configure Celery using Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks
app.autodiscover_tasks()

# Configure periodic tasks
app.conf.beat_schedule = {
    'check-contributions-morning': {
        'task': 'notifications.tasks.check_contributions',
        'schedule': crontab(hour=9, minute=0),  # Use crontab directly
        'options': {'expires': 3600}
    },
    'check-contributions-evening': {
        'task': 'notifications.tasks.check_contributions',
        'schedule': crontab(hour=21, minute=0),  # Use crontab directly
        'options': {'expires': 3600}
    }
}

# Task routing
app.conf.task_routes = {
    'notifications.tasks.check_contributions': {'queue': 'periodic'},
    'notifications.tasks.send_reminder_email': {'queue': 'emails'}
}
