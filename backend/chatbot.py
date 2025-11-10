# backend/chatbot.py
import json
import os
import re
import random
import unicodedata
from typing import Dict, Tuple, Optional, Any
from sqlalchemy.orm import Session
import models
# --- ¡AQUÍ ESTÁ LA CORRECCIÓN! ---
# Eliminamos 'generar_grafico_percentil' porque ya no existe en utils.py
from utils import (
    calcular_imc,
    # generar_grafico_percentil, <--- ELIMINADO
    clasificar_por_percentil,
    cargar_percentiles_db,
    generar_grafico_historial
)
# --- FIN DE LA CORRECCIÓN ---
from datetime import date
import spacy

# --- INICIO DE CONFIGURACIÓN DE NLU (spaCy) ---

def _setup_nlp():
    """Carga el modelo de spaCy y añade las reglas de entidad."""
    try:
        nlp = spacy.load("es_core_news_sm")
    except IOError:
        print("Error: Modelo 'es_core_news_sm' no encontrado.")
        print("Ejecuta: python -m spacy download es_core_news_sm")
        nlp = spacy.blank("es")

    # Usar nlp.pipe_names para evitar añadir el pipe varias veces en reloads
    if "entity_ruler" not in nlp.pipe_names:
        ruler = nlp.add_pipe("entity_ruler", before="ner")
        patterns = [
            # --- Patrones de Nivel 1 (Con Unidades - Alta Confianza) ---
            {
                "label": "PESO_KG",
                "pattern": [{"LIKE_NUM": True}, {"LOWER": {"IN": ["kg", "kgs", "kilo", "kilos", "kilogramos"]}}]
            },
            {
                "label": "TALLA_M",
                "pattern": [{"LIKE_NUM": True}, {"LOWER": {"IN": ["m", "metro", "metros", "mts"]}}]
            },
            {
                "label": "TALLA_CM",
                "pattern": [{"LIKE_NUM": True}, {"LOWER": {"IN": ["cm", "cms", "centimetro", "centimetros"]}}]
            },
            
            # --- Patrones de Nivel 2 (Con Palabras Clave - Media Confianza) ---
            # Ej. "pesa 65", "peso de 65"
            {
                "label": "PESO_SIMPLE",
                "pattern": [{"LOWER": {"IN": ["pesa", "peso"]}}, {"LIKE_NUM": True}]
            },
            {
                "label": "PESO_SIMPLE",
                "pattern": [{"LOWER": "peso"}, {"LOWER": "de"}, {"LIKE_NUM": True}]
            },
            # ¡MEJORA! Patrón invertido: "65 pesa"
            {
                "label": "PESO_SIMPLE",
                "pattern": [{"LIKE_NUM": True}, {"LOWER": "pesa"}]
            },

            # Ej. "mide 173", "talla de 173", "estatura 173"
            {
                "label": "TALLA_SIMPLE",
                "pattern": [{"LOWER": {"IN": ["mide", "talla", "estatura"]}}, {"LIKE_NUM": True}]
            },
            {
                "label": "TALLA_SIMPLE",
                "pattern": [{"LOWER": {"IN": ["talla", "estatura"]}}, {"LOWER": "de"}, {"LIKE_NUM": True}]
            },
            # ¡MEJORA! Patrón invertido: "173 mide"
            {
                "label": "TALLA_SIMPLE",
                "pattern": [{"LIKE_NUM": True}, {"LOWER": "mide"}]
            }
        ]
        ruler.add_patterns(patterns)
    return nlp

nlp = _setup_nlp()
# --- FIN DE CONFIGURACIÓN DE NLU ---


# --- Funciones de Utilidad (sin cambios) ---
def normalizar_texto(texto: str) -> str:
    texto = texto.lower().strip()
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    return texto

def extraer_numero(texto: str) -> Optional[float]:
    texto = texto.strip().replace(',', '.')
    match = re.search(r'\d+\.?\d*', texto)
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None

def generar_reporte_resumen(imc: float, edad: int, peso: float, talla: float, clasificacion: str, nombre: Optional[str] = None) -> str:
    talla_cm = int(talla * 100)
    titulo = f"\n📋 Resultado para {nombre} ({edad} años):\n" if nombre else f"\n📋 Resultado para niño/a de {edad} años:\n"
    intro = f"👶 Para {nombre}" if nombre else f"👶 Para tu pequeño/a de {edad} años"
    resumen = (
        f"{titulo}"
        f"• Peso: {peso} kg\n"
        f"• Estatura: {talla_cm} cm\n"
        f"• IMC: {round(imc, 2)}\n"
        f"• Categoría: {clasificacion.upper()}\n\n"
        f"{intro} ({peso}kg, {talla_cm}cm):\n\n"
    )
    if "bajo peso" in clasificacion:
        consejos = (
            "⭐ Consejos prácticos:\n"
            "• Consulta con el pediatra para descartar causas médicas.\n"
            "• Ofrece comidas pequeñas y frecuentes, ricas en nutrientes.\n"
            "• Incluye alimentos saludables con calorías: aceite de oliva, aguacate, frutos secos.\n\n"
            "💡 Recuerda: Cada niño crece a su propio ritmo. La paciencia es clave."
        )
    elif "peso normal" in clasificacion:
        consejos = (
            "✅ ¡Excelente! El peso está en rango saludable. Sigue así:\n"
            "• Mantén una dieta equilibrada con frutas, verduras y proteínas.\n"
            "• Fomenta actividad física diaria: juegos, deportes, baile.\n"
            "• Limita azúcares, refrescos y alimentos ultraprocesados.\n\n"
            "💡 Consejo: Los buenos hábitos hoy son salud mañana."
        )
    elif "riesgo de sobrepeso" in clasificacion:
        consejos = (
            "⚠️ Atención: Riesgo de sobrepeso detectado.\n"
            "• Reduce el consumo de azúcares, golosinas y frituras.\n"
            "• Aumenta la actividad física a 60 minutos diarios mínimo.\n"
            "• Establece horarios regulares de comida, sin forzar.\n\n"
            "💡 Consejo: El ejemplo familiar es fundamental. Cambien juntos."
        )
    else:
        consejos = (
            "🚨 Importante: Se detecta obesidad. Actúa con amor y apoyo:\n"
            "• Consulta con un pediatra o nutricionista certificado.\n"
            "• Implementa cambios familiares: alimentación saludable y ejercicio.\n"
            "• Refuerza positivamente, evita etiquetas o culpas.\n\n"
            "💡 Importante: No hagas dietas restrictivas sin supervisión médica."
        )
    return resumen + consejos

def _calcular_edad(fecha_nacimiento: date) -> int:
    # ... (sin cambios)
    hoy = date.today()
    edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
    return edad

# --- LÓGICA PRINCIPAL DEL CHATBOT (REFACTORIZADA CON NLU) ---

def procesar_mensaje(db: Session, mensaje: str, conversation_id: str | None, paciente: models.Paciente) -> Tuple[str, bool, Optional[str], str]:
    
    mensaje = mensaje.strip()
    if not mensaje:
        return "No recibí nada 😅. Por favor, escribe un dato válido.", False, None, conversation_id or ""

    # 1. Obtener o crear la conversación (sin cambios)
    if not conversation_id:
        calculo = models.Calculo(paciente_id=paciente.id)
        db.add(calculo)
        db.commit()
        db.refresh(calculo)
        conversation_id = calculo.id
    else:
        calculo = db.query(models.Calculo).filter(models.Calculo.id == conversation_id).first()
        if not calculo or calculo.paciente_id != paciente.id:
            calculo = models.Calculo(paciente_id=paciente.id)
            db.add(calculo)
            db.commit()
            db.refresh(calculo)
            conversation_id = calculo.id

    # 2. Comando: Reiniciar (sin cambios)
    if normalizar_texto(mensaje) in ["reiniciar", "nuevo", "empezar", "cancelar", "otro calculo", "reset"]:
        nuevo_calculo = models.Calculo(paciente_id=paciente.id)
        db.add(nuevo_calculo)
        db.commit()
        db.refresh(nuevo_calculo)
        return f"🔄 Ok, nuevo cálculo para {paciente.nombre}. ¿Cuánto pesa actualmente? (en kg)", False, None, nuevo_calculo.id

    # 3. Comando: Si el cálculo ya está completo (sin cambios)
    if calculo.talla is not None and calculo.peso is not None:
        return f"📊 Cálculo para {paciente.nombre} ya completado. Escribe 'nuevo' para un nuevo cálculo.", False, None, conversation_id

    # 4. --- LÓGICA NLU Y MÁQUINA DE ESTADOS (CORREGIDA) ---
    
    doc = nlp(mensaje)
    datos_actualizados_nlu = False
    confirmacion_talla = ""
    
    # --- PASO A: "Slot-Filling" con NLU (Busca todas las entidades) ---
    
    if calculo.peso is None:
        for ent in doc.ents:
            if ent.label_ == "PESO_KG":
                peso_encontrado = extraer_numero(ent.text)
                if peso_encontrado and 0 < peso_encontrado < 200:
                    calculo.peso = peso_encontrado
                    datos_actualizados_nlu = True
                    break
            elif ent.label_ == "PESO_SIMPLE":
                peso_encontrado = extraer_numero(ent.text)
                if peso_encontrado and 0 < peso_encontrado < 200:
                    calculo.peso = peso_encontrado
                    datos_actualizados_nlu = True
                    break
    
    if calculo.talla is None:
        for ent in doc.ents:
            if ent.label_ == "TALLA_M":
                talla_encontrada = extraer_numero(ent.text)
                if talla_encontrada and 0 < talla_encontrada <= 2.5:
                    calculo.talla = talla_encontrada
                    datos_actualizados_nlu = True
                    break
            
            if ent.label_ == "TALLA_CM":
                talla_cm = extraer_numero(ent.text)
                if talla_cm and 0 < talla_cm <= 250:
                    calculo.talla = talla_cm / 100.0
                    confirmacion_talla = f"📏 Detecté {talla_cm} cm. Lo convertí a {calculo.talla} metros. "
                    datos_actualizados_nlu = True
                    break

            if ent.label_ == "TALLA_SIMPLE":
                talla_raw = extraer_numero(ent.text)
                if talla_raw:
                    if talla_raw > 2.5 and talla_raw <= 250: # Asumir CM
                        calculo.talla = talla_raw / 100.0
                        confirmacion_talla = f"📏 Detecté {talla_raw} cm. Lo convertí a {calculo.talla} metros. "
                    elif talla_raw > 0 and talla_raw <= 2.5: # Asumir Metros
                        calculo.talla = talla_raw
                    datos_actualizados_nlu = True
                    break

    if datos_actualizados_nlu:
        db.commit()

    # --- PASO B: Máquina de Estados (Solo si NLU NO encontró nada) ---
    
    entidades_encontradas = [ent.label_ for ent in doc.ents]
    nlu_no_encontro_nada = not any(label in ["PESO_KG", "TALLA_M", "TALLA_CM", "PESO_SIMPLE", "TALLA_SIMPLE"] for label in entidades_encontradas)
    
    if nlu_no_encontro_nada:
        numero_simple = extraer_numero(mensaje)
        if numero_simple is not None:
            if calculo.peso is None:
                if 0 < numero_simple < 200:
                    calculo.peso = numero_simple
                    db.commit()
                else:
                    return "⚠️ Peso fuera de rango razonable (0-200 kg). Verifica el dato.", False, None, conversation_id
            
            elif calculo.talla is None:
                talla_raw = numero_simple
                if talla_raw > 2.5 and talla_raw <= 250: # Asumir CM
                    calculo.talla = talla_raw / 100.0
                    confirmacion_talla = f"📏 Detecté {talla_raw} cm. Lo convertí a {calculo.talla} metros. "
                    db.commit()
                elif talla_raw > 0 and talla_raw <= 2.5: # Asumir Metros
                    calculo.talla = talla_raw
                    db.commit()
                else:
                    return "📐 Talla no válida. Debe estar entre 0 y 2.5 metros. Ejemplo: 1.15", False, None, conversation_id

    # --- PASO C: Revisión Final y Respuesta ---
    
    if calculo.peso is None:
        return f"¡Hola! 👋 Estoy listo para calcular el IMC de {paciente.nombre}.\n\n¿Cuál es su PESO actual? (ej: 15.5 kg)", False, None, conversation_id

    if calculo.talla is None:
        return f"Anotado, {calculo.peso} kg. Ahora, ¿cuál es su estatura? (en metros ej: 1.10, o en cm ej: 110)", False, None, conversation_id
    
    # ¡Ambos campos están llenos! Proceder al cálculo.
    try:
        # --- CÁLCULO FINAL (Sin cambios, ya está correcto) ---
        edad = _calcular_edad(paciente.fecha_nacimiento)
        sexo = paciente.sexo
        nombre = paciente.nombre
        
        tablas_percentiles = cargar_percentiles_db(db)
        if not tablas_percentiles.get(sexo) or not tablas_percentiles.get(sexo).get(str(edad)):
            return f"📊 Lo siento, no tengo datos de percentiles para {sexo} de {edad} años.", False, None, conversation_id

        imc = calcular_imc(calculo.peso, calculo.talla)
        clasificacion = clasificar_por_percentil(imc, edad, sexo, tablas_percentiles)

        calculo.imc = round(imc, 2)
        calculo.clasificacion = clasificacion
        db.commit() 

        historial_completo = db.query(models.Calculo).filter(
            models.Calculo.paciente_id == paciente.id,
            models.Calculo.imc != None
        ).order_by(models.Calculo.timestamp).all()
        
        graph_id = generar_grafico_historial(paciente, historial_completo, db)
        
        calculo.graph_id = graph_id
        db.commit()

        mensaje_resultado = confirmacion_talla
        mensaje_resultado += "✨ ¡Listo! Procesando datos...\n\n"
        mensaje_resultado += generar_reporte_resumen(imc, edad, calculo.peso, calculo.talla, clasificacion, nombre)
        mensaje_resultado += "\n\n🔁 ¿Deseas realizar otro cálculo? Escribe 'nuevo'."

        return mensaje_resultado, True, graph_id, conversation_id

    except Exception as e:
        print(f"Error detallado en chatbot.py: {e}") 
        return f"❌ Error inesperado al procesar los datos: {str(e)}", False, None, conversation_id