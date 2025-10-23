# backend/main.py

from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from chatbot import procesar_mensaje, reiniciar_estado
import os
from typing import Dict, Any

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

# Modelo de entrada para el chatbot
class Mensaje(BaseModel):
    texto: str

class RespuestaChat(BaseModel):
    respuesta: str
    grafico: bool
    graph_id: str | None = None

# Ruta para enviar mensajes
@app.post("/mensaje", response_model=RespuestaChat)
async def recibir_mensaje(msg: Mensaje) -> Dict[str, Any]:
    """
    Procesa un mensaje del usuario y retorna la respuesta del chatbot.
    
    Args:
        msg: Mensaje del usuario
    
    Returns:
        Dict con respuesta, indicador de gráfico y ID del gráfico si aplica
    """
    respuesta, mostrar_grafico, graph_id = procesar_mensaje(msg.texto)
    return {"respuesta": respuesta, "grafico": mostrar_grafico, "graph_id": graph_id}

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

# Ruta para reiniciar el estado conversacional
@app.get("/reiniciar")
def reiniciar() -> Dict[str, str]:
    """
    Reinicia el estado conversacional del chatbot.
    
    Returns:
        Dict con mensaje de confirmación
    """
    reiniciar_estado()
    return {"mensaje": "Estado reiniciado correctamente."}

# Ruta de bienvenida inicial
@app.get("/bienvenida")
def bienvenida() -> Dict[str, Any]:
    """
    Retorna el mensaje de bienvenida y reinicia el estado.
    
    Returns:
        Dict con mensaje de bienvenida y estado inicial
    """
    reiniciar_estado()
    return {
        "respuesta": "👋 ¡Hola! Soy tu asistente de IMC para niñas y niños.\n\nVamos a empezar. ¿Cómo se llama el menor?",
        "grafico": False,
        "graph_id": None
    }
