# backend/chatbot.py
import json
import os
import re
import random
import unicodedata
from typing import Dict, Tuple, Optional, Any
from sqlalchemy.orm import Session
import models
from utils import calcular_imc, generar_grafico_percentil, clasificar_por_percentil, cargar_percentiles_db
from datetime import date

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
    # (Esta función no necesita cambios, la mantenemos igual)
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
    """Función helper para calcular la edad a partir de la fecha de nacimiento."""
    hoy = date.today()
    edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
    return edad

# --- LÓGICA PRINCIPAL DEL CHATBOT (REFACTORIZADA) ---

def procesar_mensaje(db: Session, mensaje: str, conversation_id: str | None, paciente: models.Paciente) -> Tuple[str, bool, Optional[str], str]:
    """
    Procesa el mensaje del usuario para un paciente específico.
    La máquina de estados ahora es mucho más simple:
    1. Espera Peso
    2. Espera Talla
    3. Calcula y Finaliza
    """
    mensaje = mensaje.strip()
    if not mensaje:
        return "No recibí nada 😅. Por favor, escribe un dato válido.", False, None, conversation_id or ""

    # Obtener o crear la conversación (objeto Calculo)
    if not conversation_id:
        # Es un nuevo cálculo para este paciente
        calculo = models.Calculo(paciente_id=paciente.id)
        db.add(calculo)
        db.commit()
        db.refresh(calculo)
        conversation_id = calculo.id
    else:
        calculo = db.query(models.Calculo).filter(models.Calculo.id == conversation_id).first()
        if not calculo or calculo.paciente_id != paciente.id:
            # Si el ID es inválido o no pertenece al paciente, crea uno nuevo
            calculo = models.Calculo(paciente_id=paciente.id)
            db.add(calculo)
            db.commit()
            db.refresh(calculo)
            conversation_id = calculo.id

    # --- Máquina de Estados Simplificada ---

    # Comando: Reiniciar (ahora solo limpia el cálculo actual)
    if normalizar_texto(mensaje) in ["reiniciar", "nuevo", "empezar", "cancelar", "otro calculo", "reset"]:
        nuevo_calculo = models.Calculo(paciente_id=paciente.id)
        db.add(nuevo_calculo)
        db.commit()
        db.refresh(nuevo_calculo)
        return f"🔄 Ok, nuevo cálculo para {paciente.nombre}. ¿Cuánto pesa actualmente? (en kg)", False, None, nuevo_calculo.id

    # Etapa 0: Si el cálculo ya está completo
    if calculo.talla is not None and calculo.peso is not None:
        return f"📊 Cálculo para {paciente.nombre} ya completado. Escribe 'nuevo' para un nuevo cálculo.", False, None, conversation_id

    # Etapa 1: Esperando el Peso
    if calculo.peso is None:
        numero = extraer_numero(mensaje)
        if numero is None:
            return "🚫 El peso debe ser un número. Puedes usar decimales (ejemplo: 15.5).", False, None, conversation_id
        
        peso = numero
        if peso <= 0 or peso > 200: # Validación
            return "⚠️ Peso fuera de rango razonable (0-200 kg). Verifica el dato.", False, None, conversation_id
        
        calculo.peso = peso
        db.commit()
        return f"Anotado, {peso} kg. Ahora, ¿cuál es su estatura? (en metros ej: 1.10, o en cm ej: 110)", False, None, conversation_id

    # Etapa 2: Esperando la Talla (y Cálculo Final)
    elif calculo.talla is None:
        numero = extraer_numero(mensaje)
        if numero is None:
            return "📐 La talla debe ser un número en metros (ej: 1.15) o en cm (ej: 115).", False, None, conversation_id
        
        talla = numero
        confirmacion = ""
        
        if talla > 2.5: # Conversión de CM a M
            if talla <= 250:
                talla = talla / 100
                confirmacion = f"📏 Detecté {numero} cm. Lo convertí a {talla} metros. "
            else:
                return "📐 Talla fuera de rango. Ingresa en metros (ejemplo: 1.15).", False, None, conversation_id
        
        if talla <= 0 or talla > 2.5:
            return "📐 Talla no válida. Debe estar entre 0 y 2.5 metros. Ejemplo: 1.15", False, None, conversation_id
        
        calculo.talla = talla
        
        try:
            # --- CÁLCULO FINAL ---
            # 1. Obtener datos fijos del paciente
            edad = _calcular_edad(paciente.fecha_nacimiento)
            sexo = paciente.sexo
            nombre = paciente.nombre
            
            # 2. Cargar tablas de la BD
            tablas_percentiles = cargar_percentiles_db(db)
            if not tablas_percentiles.get(sexo) or not tablas_percentiles.get(sexo).get(str(edad)):
                return f"📊 Lo siento, no tengo datos de percentiles para {sexo} de {edad} años.", False, None, conversation_id

            # 3. Calcular todo
            imc = calcular_imc(calculo.peso, calculo.talla)
            clasificacion = clasificar_por_percentil(imc, edad, sexo, tablas_percentiles)

            # 4. Guardar resultados en la BD (¡ANTES de generar el gráfico!)
            calculo.imc = round(imc, 2)
            calculo.clasificacion = clasificacion
            db.commit() # Guardamos el cálculo actual

            # 5. Generar el GRÁFICO DE HISTORIAL
            # Obtenemos el historial COMPLETO (incluyendo el que acabamos de guardar)
            historial_completo = db.query(models.Calculo).filter(
                models.Calculo.paciente_id == paciente.id,
                models.Calculo.imc != None
            ).order_by(models.Calculo.timestamp).all()
            
            # Llamamos a la nueva función del gráfico
            graph_id = generar_grafico_historial(paciente, historial_completo, db)
            
            # Guardamos el ID del gráfico en el cálculo (aunque ya no es tan crucial)
            calculo.graph_id = graph_id
            db.commit()

            # 6. Generar reporte
            mensaje_resultado = confirmacion
            mensaje_resultado += "✨ ¡Listo! Procesando datos...\n\n"
            mensaje_resultado += generar_reporte_resumen(imc, edad, calculo.peso, calculo.talla, clasificacion, nombre)
            mensaje_resultado += "\n\n🔁 ¿Deseas realizar otro cálculo? Escribe 'nuevo'."

            return mensaje_resultado, True, graph_id, conversation_id

        except Exception as e:
            return f"❌ Error inesperado al procesar los datos: {str(e)}", False, None, conversation_id
            
    # Fallback por si algo se rompe
    return "Lo siento, algo salió mal. Escribe 'nuevo' para reintentar.", False, None, conversation_id