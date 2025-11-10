# backend/tasks.py
import time
from worker import celery_app
from database import SessionLocal
import models
import os

# --- LÓGICA DE FIREBASE (FCM) ---
# Esta sección se importa pero fallará si no tienes el archivo de credenciales.
# Lo dejaremos listo para cuando configuremos Firebase.
import firebase_admin
from firebase_admin import credentials, messaging

# TODO: Reemplaza "path/to/serviceAccountKey.json" con la ruta real de tu clave.
SERVICE_ACCOUNT_KEY_PATH = "serviceAccountKey.json" # <--- ¡IMPORTANTE!

if os.path.exists(SERVICE_ACCOUNT_KEY_PATH):
    cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
    firebase_admin.initialize_app(cred)
    FIREBASE_CONFIGURADO = True
    print("Firebase Admin SDK inicializado.")
else:
    FIREBASE_CONFIGURADO = False
    print("ADVERTENCIA: 'serviceAccountKey.json' no encontrado. Las notificaciones FCM fallarán.")
# --- FIN LÓGICA FIREBASE ---


@celery_app.task(name="enviar_notificacion_a_usuario")
def enviar_notificacion_a_usuario(user_id: int, message_title: str, message_body: str):
    """
    Tarea asíncrona que envía una notificación a todos los dispositivos 
    registrados de un usuario específico.
    """
    db = SessionLocal()
    try:
        print(f"--- [TAREA INICIADA] Buscando dispositivos para User ID: {user_id} ---")
        
        # 1. Buscar los tokens FCM del usuario en la BD
        devices = db.query(models.UserDevice).filter(models.UserDevice.user_id == user_id).all()
        
        if not devices:
            print(f"--- [TAREA] No se encontraron dispositivos para User ID: {user_id} ---")
            return f"No hay dispositivos registrados para el usuario {user_id}"

        fcm_tokens = [device.fcm_token for device in devices]
        print(f"--- [TAREA] {len(fcm_tokens)} tokens encontrados. Intentando enviar... ---")

        # 2. Verificar si Firebase está listo
        if not FIREBASE_CONFIGURADO:
            print("--- [TAREA ERROR] Firebase Admin no está configurado. Omitiendo envío. ---")
            # Simulamos el tiempo que tomaría
            time.sleep(3)
            return "Simulación de envío completada (Firebase no configurado)."

        # 3. Crear el mensaje de FCM
        notification = messaging.Notification(
            title=message_title,
            body=message_body,
        )
        
        # 4. Enviar a todos los dispositivos (tokens) de ese usuario
        message = messaging.MulticastMessage(
            tokens=fcm_tokens,
            notification=notification,
        )
        
        response = messaging.send_multicast(message)
        
        print(f"--- [TAREA COMPLETADA] Éxito: {response.success_count}, Fallos: {response.failure_count} ---")
        
        # Opcional: Manejar tokens fallidos (ej. si el usuario desinstaló la app)
        if response.failure_count > 0:
            responses = response.responses
            tokens_a_eliminar = []
            for idx, resp in enumerate(responses):
                if not resp.success:
                    # Si el error es por token no registrado, lo eliminamos de la BD
                    if resp.exception.code in ('UNREGISTERED', 'INVALID_REGISTRATION_TOKEN'):
                        tokens_a_eliminar.append(fcm_tokens[idx])
            
            if tokens_a_eliminar:
                print(f"--- [TAREA] Eliminando {len(tokens_a_eliminar)} tokens obsoletos... ---")
                db.query(models.UserDevice).filter(
                    models.UserDevice.fcm_token.in_(tokens_a_eliminar)
                ).delete(synchronize_session=False)
                db.commit()

        return f"Éxito: {response.success_count}, Fallos: {response.failure_count}"

    except Exception as e:
        print(f"--- [TAREA ERROR] Fallo catastrófico: {e} ---")
        db.rollback()
        return str(e)
    finally:
        db.close()


@celery_app.task(name="tasks.programar_recordatorios_diarios")
def programar_recordatorios_diarios(mensaje_general: str):
    """
    Tarea programada (BEAT) que busca a TODOS los usuarios y les 
    envía un recordatorio.
    """
    print("--- [BEAT INICIADO] Ejecutando tarea programada 'programar_recordatorios_diarios' ---")
    db = SessionLocal()
    try:
        # En un futuro, aquí iría lógica compleja (ej. "buscar usuarios que no
        # han registrado peso en 7 días").
        # Por ahora, se lo enviamos a todos como prueba.
        usuarios = db.query(models.User).all()
        
        for user in usuarios:
            print(f"--- [BEAT] Encolando tarea para Usuario: {user.email} (ID: {user.id}) ---")
            
            # Por cada usuario, encolamos una tarea individual.
            # Esto es más robusto que enviar todo desde el "beat".
            enviar_notificacion_a_usuario.delay(
                user_id=user.id,
                message_title="Recordatorio de Salud",
                message_body=f"¡Hola! {mensaje_general}"
            )
            
        print(f"--- [BEAT COMPLETADO] {len(usuarios)} tareas encoladas. ---")
        
    except Exception as e:
        print(f"--- [BEAT ERROR] {e} ---")
    finally:
        db.close()