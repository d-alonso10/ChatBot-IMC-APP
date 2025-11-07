# backend/main.py

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload  # <--- ¡IMPORTANTE!
import os
from typing import Dict, Any, List

# Importaciones locales
import models, schemas, auth, utils, chatbot
from database import SessionLocal, engine

# Crear las tablas en la base de datos
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API IMC Pediátrico",
    description="Servicio de chatbot para calcular IMC infantil y generar recomendaciones",
    version="2.0.0"
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
    """Dependencia para obtener la sesión de BD."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    """
    Dependencia para obtener el usuario actual a partir del token JWT.
    Protege los endpoints.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    email = auth.verificar_token(token)
    if email is None:
        raise credentials_exception
    
    # --- ¡SOLUCIÓN DE CARGA ANSIOSA (EAGER LOADING)! ---
    user = db.query(models.User).options(
        joinedload(models.User.pacientes)
    ).filter(models.User.email == email).first()
    # --- FIN DE LA SOLUCIÓN ---
    
    if user is None:
        raise credentials_exception
    return user

# --- Endpoints de Autenticación y Usuarios ---

@app.post("/users/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Registra un nuevo usuario (tutor/padre)."""
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = models.User(email=user.email, password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Cargar explícitamente los pacientes (lista vacía) para la respuesta
    db.query(models.User).options(
        joinedload(models.User.pacientes)
    ).filter(models.User.id == new_user.id).first()

    return new_user

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Genera un token JWT para el login."""
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
    """Devuelve los datos del usuario logueado (y sus pacientes)."""
    return current_user

# --- Endpoints de Pacientes (Protegidos) ---

@app.post("/pacientes/crear", response_model=schemas.Paciente)
def create_paciente_for_user(
    paciente: schemas.PacienteCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """Crea un nuevo perfil de paciente para el usuario logueado."""
    # --- ¡CORRECCIÓN Pydantic v1! ---
    # .model_dump() es v2, .dict() es v1
    nuevo_paciente = models.Paciente(**paciente.dict(), tutor_id=current_user.id)
    # --- FIN CORRECCIÓN ---
    db.add(nuevo_paciente)
    db.commit()
    db.refresh(nuevo_paciente)
    return nuevo_paciente

@app.get("/pacientes/me", response_model=List[schemas.Paciente])
def read_user_pacientes(
    current_user: models.User = Depends(get_current_user)
):
    """Devuelve la lista de pacientes del usuario logueado."""
    return current_user.pacientes

@app.get("/pacientes/{paciente_id}/historial", response_model=List[schemas.Calculo])
def get_historial_paciente(
    paciente_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Obtiene la lista de todos los cálculos completados de un paciente."""
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
    """Genera y devuelve el gráfico CON EL HISTORIAL COMPLETO de un paciente."""
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

# --- Endpoints del Chat (Protegidos y Refactorizados) ---

@app.post("/mensaje", response_model=schemas.RespuestaChat)
async def recibir_mensaje(
    msg: schemas.Mensaje, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Procesa un mensaje del usuario para un paciente específico.
    """
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
    """
    Obtiene un gráfico específico por su ID único.
    """
    path = os.path.join("graficos", f"grafico_{graph_id}.png")
    if os.path.exists(path):
        return FileResponse(path, media_type="image/png")
    return JSONResponse(content={"error": "Gráfico no disponible."}, status_code=404)