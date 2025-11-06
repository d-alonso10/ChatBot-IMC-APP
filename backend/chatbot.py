import json
import os
import re
import random
import unicodedata
from typing import Dict, Tuple, Optional, Any
from sqlalchemy.orm import Session
import models
from utils import calcular_imc, generar_grafico_percentil, clasificar_por_percentil, cargar_percentiles_db

def normalizar_texto(texto: str) -> str:
    """
    Normaliza texto removiendo tildes y convirtiendo a minúsculas.
    
    Args:
        texto: Texto a normalizar
    
    Returns:
        str: Texto normalizado sin tildes y en minúsculas
    """
    texto = texto.lower().strip()
    # Remover tildes
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    return texto

def extraer_numero(texto: str) -> Optional[float]:
    """
    Extrae un número de un texto, ignorando unidades como 'kg', 'm', 'cm'.
    
    Args:
        texto: Texto que puede contener un número con unidades
    
    Returns:
        Optional[float]: Número extraído o None si no se encuentra
    """
    # Remover espacios y reemplazar coma por punto
    texto = texto.strip().replace(',', '.')
    
    # Buscar patrón de número (entero o decimal)
    match = re.search(r'\d+\.?\d*', texto)
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None

def generar_reporte_resumen(imc: float, edad: int, peso: float, talla: float, clasificacion: str, nombre: Optional[str] = None) -> str:
    """
    Genera un reporte personalizado con consejos según la clasificación del IMC.
    
    Args:
        imc: Índice de Masa Corporal calculado
        edad: Edad del menor en años
        peso: Peso del menor en kilogramos
        talla: Talla del menor en metros
        clasificacion: Categoría del IMC (bajo peso, peso normal, riesgo de sobrepeso, obesidad)
        nombre: Nombre del menor (opcional)
    
    Returns:
        str: Reporte completo con resumen y consejos personalizados
    """
    talla_cm = int(talla * 100)
    
    # Personalizar con nombre si está disponible
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

def procesar_mensaje(db: Session, mensaje: str, conversation_id: str | None) -> Tuple[str, bool, Optional[str], str]:
    """
    Procesa el mensaje del usuario y gestiona el flujo conversacional del chatbot.
    
    Args:
        db: Sesión de base de datos
        mensaje: Texto enviado por el usuario
        conversation_id: ID de la conversación existente (opcional)
    
    Returns:
        Tuple[str, bool, Optional[str], str]: (respuesta_texto, mostrar_grafico, graph_id, conversation_id)
    """
    mensaje = mensaje.strip()
    if not mensaje:
        return "No recibí nada 😅. Por favor, escribe un dato válido.", False, None, conversation_id or ""

    # Obtener o crear la conversación
    if not conversation_id:
        # Si no hay ID, crea una nueva conversación
        calculo = models.Calculo()
        db.add(calculo)
        db.commit()
        db.refresh(calculo)
        conversation_id = calculo.id
    else:
        calculo = db.query(models.Calculo).filter(models.Calculo.id == conversation_id).first()
        if not calculo:
            # Si el ID es inválido, crea uno nuevo
            calculo = models.Calculo()
            db.add(calculo)
            db.commit()
            db.refresh(calculo)
            conversation_id = calculo.id

    # Comando: Reiniciar
    if normalizar_texto(mensaje) in ["reiniciar", "nuevo", "calcular otro", "empezar", "comenzar", "cancelar", "inicio", "otro calculo", "reset", "volver"]:
        # Crea una nueva conversación
        nuevo_calculo = models.Calculo()
        db.add(nuevo_calculo)
        db.commit()
        db.refresh(nuevo_calculo)
        return "🔄 ¡Perfecto! Comenzamos de nuevo. ¿Cómo se llama el menor?", False, None, nuevo_calculo.id

    # Etapa 0: Nombre
    if calculo.nombre is None:
        nombre = mensaje.strip()
        if len(nombre) > 50:
            return "😅 El nombre es muy largo. Intenta con algo más corto.", False, None, conversation_id
        
        calculo.nombre = nombre
        db.commit()
        return f"¡Perfecto! 😊 Ahora, ¿qué edad tiene {nombre}? (en años)", False, None, conversation_id

    # Etapa 1: Edad
    elif calculo.edad is None:
        numero = extraer_numero(mensaje)
        if numero is None:
            return "⚠️ La edad debe ser un número entero. Ejemplo: 5", False, None, conversation_id
        
        edad = int(numero)
        if edad < 1 or edad > 18:
            return "📆 Por favor, ingresa una edad entre 1 y 18 años.", False, None, conversation_id
        
        calculo.edad = edad
        db.commit()
        
        # Respuestas variadas
        respuestas = [
            f"Entendido, {edad} años. ¿Es niño o niña?",
            f"Perfecto, {edad} años. Ahora dime, ¿cuál es su sexo? (niño/niña)",
            f"Muy bien. {calculo.nombre} tiene {edad} años. ¿Es niño o niña?"
        ]
        return random.choice(respuestas), False, None, conversation_id

    # Etapa 2: Sexo
    elif calculo.sexo is None:
        sexo_normalizado = normalizar_texto(mensaje)
        
        # Aceptar variaciones: niño, nino, masculino, varon, m, niña, nina, femenino, f
        if sexo_normalizado in ["nino", "niño", "masculino", "varon", "m", "hombre", "chico"]:
            sexo_validado = "niño"
        elif sexo_normalizado in ["nina", "niña", "femenino", "f", "mujer", "chica"]:
            sexo_validado = "niña"
        else:
            return "🚻 Por favor, responde con 'niño' o 'niña'.", False, None, conversation_id
        
        calculo.sexo = sexo_validado
        db.commit()
        
        # Respuestas variadas con confirmación sutil
        respuestas = [
            f"Ok, {sexo_validado}. Ahora, ¿cuánto pesa? (en kg, ejemplo: 15.5)",
            f"Entendido, {sexo_validado}. ¿Cuál es su peso en kilogramos? (ej: 20.3)",
            f"Perfecto. Siguiente dato: ¿cuánto pesa en kg?"
        ]
        return random.choice(respuestas), False, None, conversation_id

    # Etapa 3: Peso
    elif calculo.peso is None:
        numero = extraer_numero(mensaje)
        if numero is None:
            return "🚫 El peso debe ser un número. Puedes usar decimales (ejemplo: 15.5).", False, None, conversation_id
        
        peso = numero
        
        # Validación de rango razonable según edad
        edad = calculo.edad
        if peso <= 0 or peso > 200:
            return "⚠️ Peso fuera de rango razonable (0-200 kg). Verifica el dato.", False, None, conversation_id
        
        # Advertencia si el peso parece inusual para la edad
        if edad <= 5 and peso > 30:
            return f"⚠️ ¿{peso} kg para {edad} años? Parece alto. Si es correcto, envíalo de nuevo para confirmar.", False, None, conversation_id
        
        calculo.peso = peso
        db.commit()
        
        # Respuestas variadas con opción de cm o metros
        respuestas = [
            f"Anotado, {peso} kg. Último dato: ¿cuál es su estatura? (en metros ej: 1.10, o en cm ej: 110)",
            f"Perfecto, {peso} kg. Ahora la talla (en metros: 1.15 o en cm: 115)",
            f"Entendido, {peso} kg. ¿Y la estatura? (puedes usar metros como 1.20 o cm como 120)"
        ]
        return random.choice(respuestas), False, None, conversation_id

    # Etapa 4: Talla
    elif calculo.talla is None:
        numero = extraer_numero(mensaje)
        if numero is None:
            return "📐 La talla debe ser un número en metros (ej: 1.15) o en cm (ej: 115).", False, None, conversation_id
        
        talla = numero
        
        # Si el número es muy grande, probablemente lo ingresó en cm
        if talla > 2.5:
            if talla <= 250:  # Probablemente en cm
                talla = talla / 100
                confirmacion = f"📏 Detecté {numero} cm. Lo convertí a {talla} metros. "
            else:
                return "📐 Talla fuera de rango. Ingresa en metros (ejemplo: 1.15).", False, None, conversation_id
        else:
            confirmacion = ""
        
        if talla <= 0 or talla > 2.5:
            return "📐 Talla no válida. Debe estar entre 0 y 2.5 metros. Ejemplo: 1.15", False, None, conversation_id
        
        calculo.talla = talla
        
        try:
            # Cálculo final
            tablas_percentiles = cargar_percentiles_db(db)
            imc = calcular_imc(calculo.peso, calculo.talla)
            clasificacion = clasificar_por_percentil(imc, calculo.edad, calculo.sexo, tablas_percentiles)
            graph_id = generar_grafico_percentil(imc, calculo.edad, calculo.sexo, tablas_percentiles)

            # Guardar resultados en la BD
            calculo.imc = imc
            calculo.clasificacion = clasificacion
            calculo.graph_id = graph_id
            db.commit()

            # Frases de transición aleatorias
            transiciones = [
                "✨ ¡Listo! Déjame calcular...",
                "📊 Perfecto. Procesando datos...",
                "✅ ¡Entendido! Calculando el IMC..."
            ]
            mensaje_resultado = confirmacion
            mensaje_resultado += (
                f"{random.choice(transiciones)}\n\n"
                f"✅ El IMC es: {round(imc, 2)} - Categoría: *{clasificacion.upper()}*\n"
            )
            mensaje_resultado += generar_reporte_resumen(imc, calculo.edad, calculo.peso, calculo.talla, clasificacion, calculo.nombre)
            mensaje_resultado += "\n\n🔁 ¿Deseas calcular otro IMC? Escribe 'reiniciar'."

            return mensaje_resultado, True, graph_id, conversation_id

        except ValueError:
            return "🚫 Talla no válida. Usa formato como 1.20 (en metros).", False, None, conversation_id
        except Exception as e:
            return f"❌ Error inesperado al procesar los datos: {str(e)}", False, None, conversation_id

    # Si la conversación ya terminó
    else:
        return "📊 Cálculo completado. Escribe 'reiniciar' para empezar de nuevo.", False, None, conversation_id