import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "FINANCE_CORE.settings")
app = Celery("FINANCE_CORE_CELERY_APP")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
