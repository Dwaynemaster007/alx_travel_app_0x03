"""Celery application for the ALX Travel App.

Start a worker (with RabbitMQ running) from the directory holding manage.py:

    celery -A alx_travel_app worker -l info
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alx_travel_app.settings")

app = Celery("alx_travel_app")

# Read every CELERY_* setting from Django settings.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Find tasks.py in every installed app.
app.autodiscover_tasks()
