# backend/main.py

from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from chatbot import procesar_mensaje
import os
from typing import Dict, Any

# Importar modelos y base de datos
import models
from database import SessionLocal, engine

# Crear las tablas en la base de datos
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API IMC Pediátrico",
    description="Servicio de chatbot para calcular IMC infantil y generar recomendaciones",
    version="1.0.0"
)

# Configuración de CORS
# En producción, establecer la variable de entorno ALLOWED_ORIGINS con los dominios permitidos
# Ejemplo: ALLOWED_ORIGINS="https://miapp.com,https://www.miapp.com"
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependencia para obtener la sesión de BD
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Modelo de entrada para el chatbot
class Mensaje(BaseModel):
    texto: str
    conversation_id: str | None = None  # El frontend debe enviar esto

class RespuestaChat(BaseModel):
    respuesta: str
    grafico: bool
    graph_id: str | None = None
    conversation_id: str | None = None

# Ruta para enviar mensajes
@app.post("/mensaje", response_model=RespuestaChat)
async def recibir_mensaje(msg: Mensaje, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Procesa un mensaje del usuario y retorna la respuesta del chatbot.
    
    Args:
        msg: Mensaje del usuario con conversation_id
        db: Sesión de base de datos
    
    Returns:
        Dict con respuesta, indicador de gráfico, ID del gráfico y conversation_id
    """
    respuesta, mostrar_grafico, graph_id, conv_id = procesar_mensaje(db, msg.texto, msg.conversation_id)
    return {
        "respuesta": respuesta, 
        "grafico": mostrar_grafico, 
        "graph_id": graph_id,
        "conversation_id": conv_id
    }

# Ruta para obtener un gráfico específico por su ID
@app.get("/grafico/{graph_id}")
async def obtener_grafico(graph_id: str):
    """
    Obtiene un gráfico específico por su ID único.
    
    Args:
        graph_id: ID único del gráfico (UUID)
    
    Returns:
        Archivo de imagen PNG del gráfico
    """
    path = os.path.join("graficos", f"grafico_{graph_id}.png")
    if os.path.exists(path):
        return FileResponse(path, media_type="image/png")
    return JSONResponse(content={"error": "Gráfico no disponible."}, status_code=404)

# Ruta de bienvenida inicial - ahora crea una nueva conversación
@app.get("/bienvenida")
def bienvenida(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Crea una nueva conversación y retorna el mensaje de bienvenida.
    
    Returns:
        Dict con mensaje de bienvenida, estado inicial y conversation_id
    """
    # Crear una nueva conversación en la base de datos
    nuevo_calculo = models.Calculo()
    db.add(nuevo_calculo)
    db.commit()
    db.refresh(nuevo_calculo)

    return {
        "respuesta": "👋 ¡Hola! Soy tu asistente de IMC para niñas y niños.\n\nVamos a empezar. ¿Cómo se llama el menor?",
        "grafico": False,
        "graph_id": None,
        "conversation_id": nuevo_calculo.id  # Devuelve el nuevo ID de conversación
    }