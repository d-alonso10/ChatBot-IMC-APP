# backend/main.py

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
import os
from typing import Dict, Any, List
from datetime import date

# Importaciones locales
import models, schemas, auth, utils, chatbot
from database import SessionLocal, engine

# --- ¡NUEVA IMPORTACIÓN! ---
from tasks import enviar_notificacion_a_usuario

# Crear las tablas en la base de datos
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API IMC Pediátrico",
    description="Servicio de chatbot para calcular IMC infantil y generar recomendaciones",
    version="2.1.0" # Versión B1
)

# --- Configuración de CORS (sin cambios) ---
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Dependencias de BD y Autenticación ---

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    email = auth.verificar_token(token)
    if email is None:
        raise credentials_exception
    
    # --- ¡CARGA ANSIOSA (EAGER LOADING) MODIFICADA! ---
    # Ahora también cargamos los dispositivos
    user = db.query(models.User).options(
        joinedload(models.User.pacientes),
        joinedload(models.User.devices) 
    ).filter(models.User.email == email).first()
    # --- FIN DE LA MODIFICACIÓN ---
    
    if user is None:
        raise credentials_exception
    return user

# --- Endpoints de Autenticación y Usuarios ---

@app.post("/users/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = models.User(email=user.email, password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Cargar relaciones vacías para la respuesta
    db.query(models.User).options(
        joinedload(models.User.pacientes),
        joinedload(models.User.devices)
    ).filter(models.User.id == new_user.id).first()

    return new_user

# ... (Endpoint /token sin cambios) ...
@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verificar_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.crear_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

# --- ¡NUEVO ENDPOINT PARA REGISTRAR DISPOSITIVO FCM! ---
@app.post("/users/me/register-device", response_model=schemas.UserDevice)
def register_fcm_device(
    device: schemas.UserDeviceCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Registra un token FCM de un dispositivo (Flutter) para el usuario logueado.
    Si el token ya existe, simplemente actualiza la hora.
    """
    
    # Verificar si el token ya existe
    db_device = db.query(models.UserDevice).filter(
        models.UserDevice.fcm_token == device.fcm_token
    ).first()
    
    if db_device:
        # Si ya existe y pertenece a este usuario, solo actualizamos el timestamp
        if db_device.user_id == current_user.id:
            db_device.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_device)
            return db_device
        else:
            # Si el token existe pero con OTRO usuario (raro, pero posible si
            # alguien desinstala y reinstala la app con otra cuenta),
            # lo reasignamos al usuario actual.
            db_device.user_id = current_user.id
            db_device.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_device)
            return db_device
            
    # Si no existe, crear uno nuevo
    new_device = models.UserDevice(
        fcm_token=device.fcm_token,
        user_id=current_user.id
    )
    db.add(new_device)
    
    try:
        db.commit()
        db.refresh(new_device)
    except IntegrityError:
        db.rollback()
        # Manejar condición de carrera (si dos requests llegan al mismo tiempo)
        db_device = db.query(models.UserDevice).filter(
            models.UserDevice.fcm_token == device.fcm_token
        ).first()
        if db_device:
            return db_device
        else:
            raise HTTPException(status_code=500, detail="Error al registrar el dispositivo")

    return new_device

# --- Endpoints de Pacientes (sin cambios) ---
@app.post("/pacientes/crear", response_model=schemas.Paciente)
def create_paciente_for_user(
    paciente: schemas.PacienteCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    nuevo_paciente = models.Paciente(**paciente.dict(), tutor_id=current_user.id)
    db.add(nuevo_paciente)
    db.commit()
    db.refresh(nuevo_paciente)
    return nuevo_paciente

@app.get("/pacientes/me", response_model=List[schemas.Paciente])
def read_user_pacientes(
    current_user: models.User = Depends(get_current_user)
):
    return current_user.pacientes

# ... (Todos los endpoints de /pacientes/{id}/* se mantienen igual) ...
@app.get("/pacientes/{paciente_id}/historial", response_model=List[schemas.Calculo])
def get_historial_paciente(
    paciente_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    paciente = db.query(models.Paciente).filter(
        models.Paciente.id == paciente_id,
        models.Paciente.tutor_id == current_user.id
    ).first()
    if not paciente:
        raise HTTPException(status_code=403, detail="Paciente no autorizado")
    historial = db.query(models.Calculo).filter(
        models.Calculo.paciente_id == paciente_id,
        models.Calculo.imc != None
    ).order_by(models.Calculo.timestamp.desc()).all()
    return historial

@app.get("/pacientes/{paciente_id}/historial/grafico")
async def get_grafico_historial(
    paciente_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    paciente = db.query(models.Paciente).filter(
        models.Paciente.id == paciente_id,
        models.Paciente.tutor_id == current_user.id
    ).first()
    if not paciente:
        raise HTTPException(status_code=403, detail="Paciente no autorizado")
    historial = db.query(models.Calculo).filter(
        models.Calculo.paciente_id == paciente.id,
        models.Calculo.imc != None
    ).order_by(models.Calculo.timestamp).all()
    if not historial:
        raise HTTPException(status_code=404, detail="No hay historial de cálculos para este paciente")
    try:
        graph_id = utils.generar_grafico_historial(paciente, historial, db)
        path = os.path.join("graficos", f"grafico_{graph_id}.png")
        if os.path.exists(path):
            return FileResponse(path, media_type="image/png")
        else:
            raise HTTPException(status_code=500, detail="Error al generar el gráfico")
    except Exception as e:
        return JSONResponse(content={"error": f"Error al generar gráfico: {str(e)}"}, status_code=500)

@app.get("/pacientes/{paciente_id}/grafico/peso")
async def get_grafico_peso(
    paciente_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    paciente = db.query(models.Paciente).filter(
        models.Paciente.id == paciente_id,
        models.Paciente.tutor_id == current_user.id
    ).first()
    if not paciente:
        raise HTTPException(status_code=403, detail="Paciente no autorizado")
    historial = db.query(models.Calculo).filter(
        models.Calculo.paciente_id == paciente.id,
        models.Calculo.peso != None
    ).order_by(models.Calculo.timestamp).all()
    if not historial:
        raise HTTPException(status_code=404, detail="No hay historial de cálculos para este paciente")
    try:
        graph_id = utils.generar_grafico_simple(historial, paciente, "peso")
        path = os.path.join("graficos", f"grafico_{graph_id}.png")
        if os.path.exists(path):
            return FileResponse(path, media_type="image/png")
        else:
            raise HTTPException(status_code=500, detail="Error al generar el gráfico")
    except Exception as e:
        return JSONResponse(content={"error": f"Error al generar gráfico: {str(e)}"}, status_code=500)

@app.get("/pacientes/{paciente_id}/grafico/talla")
async def get_grafico_talla(
    paciente_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    paciente = db.query(models.Paciente).filter(
        models.Paciente.id == paciente_id,
        models.Paciente.tutor_id == current_user.id
    ).first()
    if not paciente:
        raise HTTPException(status_code=403, detail="Paciente no autorizado")
    historial = db.query(models.Calculo).filter(
        models.Calculo.paciente_id == paciente.id,
        models.Calculo.talla != None
    ).order_by(models.Calculo.timestamp).all()
    if not historial:
        raise HTTPException(status_code=404, detail="No hay historial de cálculos para este paciente")
    try:
        graph_id = utils.generar_grafico_simple(historial, paciente, "talla")
        path = os.path.join("graficos", f"grafico_{graph_id}.png")
        if os.path.exists(path):
            return FileResponse(path, media_type="image/png")
        else:
            raise HTTPException(status_code=500, detail="Error al generar el gráfico")
    except Exception as e:
        return JSONResponse(content={"error": f"Error al generar gráfico: {str(e)}"}, status_code=500)

@app.get("/pacientes/{paciente_id}/exportar-pdf")
async def exportar_pdf_paciente(
    paciente_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    paciente = db.query(models.Paciente).options(
        joinedload(models.Paciente.tutor) 
    ).filter(
        models.Paciente.id == paciente_id,
        models.Paciente.tutor_id == current_user.id
    ).first()
    if not paciente:
        raise HTTPException(status_code=403, detail="Paciente no autorizado")
    historial = db.query(models.Calculo).filter(
        models.Calculo.paciente_id == paciente_id,
        models.Calculo.imc != None
    ).order_by(models.Calculo.timestamp.desc()).all()
    if not historial:
        raise HTTPException(status_code=404, detail="No hay historial para exportar")
    try:
        pdf_buffer = utils.generar_reporte_pdf(paciente, historial, db)
        filename = f"Reporte_{paciente.nombre.replace(' ', '_')}_{date.today()}.pdf"
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        print(f"Error generando PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Error al generar el PDF: {e}")

# --- Endpoints del Chat (sin cambios) ---
@app.post("/mensaje", response_model=schemas.RespuestaChat)
async def recibir_mensaje(
    msg: schemas.Mensaje, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
) -> Dict[str, Any]:
    paciente = db.query(models.Paciente).filter(
        models.Paciente.id == msg.paciente_id,
        models.Paciente.tutor_id == current_user.id
    ).first()
    
    if not paciente:
        raise HTTPException(status_code=403, detail="Paciente no encontrado o no autorizado")

    respuesta, mostrar_grafico, graph_id, conv_id = chatbot.procesar_mensaje(
        db, msg.texto, msg.conversation_id, paciente
    )
    
    return {
        "respuesta": respuesta, 
        "grafico": mostrar_grafico, 
        "graph_id": graph_id,
        "conversation_id": conv_id
    }

# --- Endpoint de Gráficos (sin cambios) ---
@app.get("/grafico/{graph_id}")
async def obtener_grafico(graph_id: str):
    path = os.path.join("graficos", f"grafico_{graph_id}.png")
    if os.path.exists(path):
        return FileResponse(path, media_type="image/png")
    return JSONResponse(content={"error": "Gráfico no disponible."}, status_code=404)


# --- ¡ENDPOINT DE PRUEBA MODIFICADO! ---
@app.post("/test/enviar-notificacion-ahora", status_code=status.HTTP_202_ACCEPTED)
async def test_enviar_notificacion_ahora(
    current_user: models.User = Depends(get_current_user)
):
    """
    Endpoint de prueba para verificar que Celery y FCM funcionan.
    Llama a la tarea asíncrona 'enviar_notificacion_a_usuario'
    para el usuario logueado.
    """
    
    mensaje_push_titulo = "¡Prueba de Notificación!"
    mensaje_push_cuerpo = f"Hola {current_user.email}, ¡Celery y FCM funcionan!"

    # --- Aquí ocurre la magia ---
    # .delay() le dice a Celery que ejecute esta tarea en segundo plano
    enviar_notificacion_a_usuario.delay(
        user_id=current_user.id, 
        message_title=mensaje_push_titulo,
        message_body=mensaje_push_cuerpo
    )
    
    print(f"Endpoint: Tarea de notificación para {current_user.email} (ID: {current_user.id}) ha sido encolada.")

    # Devolvemos una respuesta inmediata al usuario
    return {
        "message": "Tarea de notificación encolada. Revisa tu dispositivo y la consola del worker."
    }