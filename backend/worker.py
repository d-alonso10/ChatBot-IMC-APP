# backend/worker.py
import os
from celery import Celery

# --- ¡NUEVO PLAN C! ---
# Volvemos a Redis, pero en un puerto DIFERENTE para evitar conflictos con WSL
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6380/0") # <-- PUERTO 6380

celery_app = Celery(
    "tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["tasks"] # Lista de módulos que contienen tareas
)

# Configuración (sin cambios)
celery_app.conf.update(
    task_track_started=True,
    beat_schedule={
        'enviar-recordatorios-diarios': {
            'task': 'tasks.programar_recordatorios_diarios',
            'schedule': 3600.0, 
            'args': ("¡Es hora de tu registro semanal!",),
        },
    },
)