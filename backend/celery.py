# backend/celery.py
import os
from celery import Celery

# Remplace 'backend.settings' si ton settings module a un autre chemin
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

app = Celery("backend")

# Charge la config CELERY_... depuis settings.py (préfixe CELERY_)
app.config_from_object("django.conf:settings", namespace="CELERY")

# Découvre tasks.py dans les apps installées
app.autodiscover_tasks()

# (optionnel) un petit test logger
@app.task(bind=True)
def debug_task(self):
    print(f"Celery debug task id: {self.request.id}")
