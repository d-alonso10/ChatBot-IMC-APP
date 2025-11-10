# backend/worker.py
import os
from celery import Celery

# Configura la URL del broker (Redis)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["tasks"] # Lista de módulos que contienen tareas
)

# Configuración opcional
celery_app.conf.update(
    task_track_started=True,
    # --- ¡NUEVO! Configuración de Tareas Programadas (Celery Beat) ---
    # Esto define nuestro "cron job" o tarea programada.
    beat_schedule={
        'enviar-recordatorios-diarios': {
            'task': 'tasks.programar_recordatorios_diarios', # La tarea a ejecutar
            'schedule': 3600.0, # 3600 segundos = 1 hora. Cambia a 86400.0 para diario
            # 'schedule': crontab(hour=9, minute=0), # Para ejecutar todos los días a las 9:00 AM
            'args': ("¡Es hora de tu registro semanal!",), # Argumentos para la tarea
        },
    },
)
# (Para usar crontab, necesitarías: from celery.schedules import crontab)