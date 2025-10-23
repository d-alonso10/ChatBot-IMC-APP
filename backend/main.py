# backend/main.py

from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from chatbot import procesar_mensaje, reiniciar_estado
import os

app = FastAPI(
    title="API IMC Pediátrico",
    description="Servicio de chatbot para calcular IMC infantil y generar recomendaciones",
    version="1.0.0"
)

# Permitir acceso desde Flutter u otros orígenes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Cambiar a orígenes específicos en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo de entrada para el chatbot
class Mensaje(BaseModel):
    texto: str

# Ruta para enviar mensajes
@app.post("/mensaje")
async def recibir_mensaje(msg: Mensaje):
    respuesta, mostrar_grafico = procesar_mensaje(msg.texto)
    return {"respuesta": respuesta, "grafico": mostrar_grafico}

# Ruta para obtener el gráfico del último resultado
@app.get("/grafico")
async def obtener_grafico():
    path = "ultima_grafica.png"
    if os.path.exists(path):
        return FileResponse(path, media_type="image/png")
    return JSONResponse(content={"error": "Gráfico no disponible."}, status_code=404)

# Ruta para reiniciar el estado conversacional
@app.get("/reiniciar")
def reiniciar():
    reiniciar_estado()
    return {"mensaje": "Estado reiniciado correctamente."}

# ✅ Nueva ruta: mensaje de bienvenida inicial
@app.get("/bienvenida")
def bienvenida():
    reiniciar_estado()
    return {
        "respuesta": "👋 ¡Hola! Soy tu asistente de IMC para niñas y niños.\n\nVamos a empezar. ¿Qué edad tiene el menor?",
        "grafico": False
    }
