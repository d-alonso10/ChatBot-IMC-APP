import json
import os
import re
import random
import unicodedata
from typing import Dict, Tuple, Optional, Any
from utils import calcular_imc, generar_grafico_percentil, clasificar_por_percentil

estado: Dict[str, Optional[Any]] = {
    "nombre": None,
    "edad": None,
    "sexo": None,
    "peso": None,
    "talla": None,
    "graph_id": None,
    "intentos_fallidos": 0
}

def reiniciar_estado() -> None:
    """
    Reinicia el estado conversacional del chatbot a valores iniciales.
    """
    global estado
    for key in estado:
        estado[key] = None
    estado["intentos_fallidos"] = 0

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

def procesar_mensaje(mensaje: str) -> Tuple[str, bool, Optional[str]]:
    """
    Procesa el mensaje del usuario y gestiona el flujo conversacional del chatbot.
    
    Args:
        mensaje: Texto enviado por el usuario
    
    Returns:
        Tuple[str, bool, Optional[str]]: (respuesta_texto, mostrar_grafico, graph_id)
    """
    global estado

    mensaje = mensaje.strip()
    if not mensaje:
        return "No recibí nada 😅. Por favor, escribe un dato válido.", False, None

    # Etapa 0: Nombre (opcional)
    if estado["nombre"] is None:
        nombre = mensaje.strip()
        if len(nombre) > 50:
            return "😅 El nombre es muy largo. Intenta con algo más corto.", False, None
        estado["nombre"] = nombre
        return f"¡Perfecto! 😊 Ahora, ¿qué edad tiene {nombre}? (en años)", False, None

    # Etapa 1: Edad
    elif estado["edad"] is None:
        numero = extraer_numero(mensaje)
        if numero is None:
            estado["intentos_fallidos"] += 1
            if estado["intentos_fallidos"] >= 3:
                return "🤔 Parece que hay confusión. La edad debe ser un número entero (ejemplo: 5, 10, 15). ¿Quieres reiniciar? Escribe 'reiniciar'.", False, None
            return "⚠️ La edad debe ser un número entero. Ejemplo: 5", False, None
        
        edad = int(numero)
        if edad < 1 or edad > 18:
            estado["intentos_fallidos"] += 1
            return "📆 Por favor, ingresa una edad entre 1 y 18 años.", False, None
        
        estado["edad"] = edad
        estado["intentos_fallidos"] = 0
        
        # Respuestas variadas
        respuestas = [
            f"Entendido, {edad} años. ¿Es niño o niña?",
            f"Perfecto, {edad} años. Ahora dime, ¿cuál es su sexo? (niño/niña)",
            f"Muy bien. {estado['nombre']} tiene {edad} años. ¿Es niño o niña?"
        ]
        return random.choice(respuestas), False, None

    # Etapa 2: Sexo
    elif estado["sexo"] is None:
        sexo_normalizado = normalizar_texto(mensaje)
        
        # Aceptar variaciones: niño, nino, masculino, varon, m, niña, nina, femenino, f
        if sexo_normalizado in ["nino", "niño", "masculino", "varon", "m", "hombre", "chico"]:
            estado["sexo"] = "niño"
        elif sexo_normalizado in ["nina", "niña", "femenino", "f", "mujer", "chica"]:
            estado["sexo"] = "niña"
        else:
            estado["intentos_fallidos"] += 1
            if estado["intentos_fallidos"] >= 3:
                return "🤔 No logro entender. Por favor responde con 'niño' o 'niña'. Si necesitas ayuda, escribe 'reiniciar'.", False, None
            return "🚻 Por favor, responde con 'niño' o 'niña'.", False, None
        
        estado["intentos_fallidos"] = 0
        
        # Respuestas variadas con confirmación
        respuestas = [
            f"Perfecto. Ahora, ¿cuánto pesa? (en kg, ejemplo: 15.5)",
            f"Entendido. ¿Cuál es su peso en kilogramos? (ej: 20.3)",
            f"Muy bien. Siguiente dato: ¿cuánto pesa en kg?"
        ]
        return random.choice(respuestas), False, None

    # Etapa 3: Peso
    elif estado["peso"] is None:
        numero = extraer_numero(mensaje)
        if numero is None:
            estado["intentos_fallidos"] += 1
            if estado["intentos_fallidos"] >= 3:
                return "🤔 El peso debe ser un número. Ejemplo: 15.5 o 20.3. ¿Necesitas reiniciar? Escribe 'reiniciar'.", False, None
            return "🚫 El peso debe ser un número. Puedes usar decimales (ejemplo: 15.5).", False, None
        
        peso = numero
        
        # Validación de rango razonable según edad
        edad = estado["edad"]
        if peso <= 0 or peso > 200:
            estado["intentos_fallidos"] += 1
            return "⚠️ Peso fuera de rango razonable (0-200 kg). Verifica el dato.", False, None
        
        # Advertencia si el peso parece inusual para la edad
        if edad <= 5 and peso > 30:
            return f"⚠️ ¿{peso} kg para {edad} años? Parece alto. Si es correcto, envíalo de nuevo para confirmar.", False, None
        
        estado["peso"] = peso
        estado["intentos_fallidos"] = 0
        
        # Respuestas variadas
        respuestas = [
            f"Anotado, {peso} kg. Un último dato: ¿cuál es su estatura en metros? (ej: 1.10)",
            f"Perfecto, {peso} kg. Ahora la talla en metros (ejemplo: 1.15)",
            f"Muy bien. Peso: {peso} kg. ¿Y la estatura? (en metros, ej: 1.20)"
        ]
        return random.choice(respuestas), False, None

    # Etapa 4: Talla
    elif estado["talla"] is None:
        numero = extraer_numero(mensaje)
        if numero is None:
            estado["intentos_fallidos"] += 1
            if estado["intentos_fallidos"] >= 3:
                return "🤔 La talla debe ser un número en metros. Ejemplo: 1.10 o 1.25. ¿Reiniciamos? Escribe 'reiniciar'.", False, None
            return "📐 La talla debe ser un número en metros. Ejemplo: 1.15", False, None
        
        talla = numero
        
        # Si el número es muy grande, probablemente lo ingresó en cm
        if talla > 2.5:
            if talla <= 250:  # Probablemente en cm
                talla = talla / 100
                confirmacion = f"📏 Detecté {numero} cm. Lo convertí a {talla} metros. "
            else:
                estado["intentos_fallidos"] += 1
                return "📐 Talla fuera de rango. Ingresa en metros (ejemplo: 1.15).", False, None
        else:
            confirmacion = ""
        
        if talla <= 0 or talla > 2.5:
            estado["intentos_fallidos"] += 1
            return "📐 Talla no válida. Debe estar entre 0 y 2.5 metros. Ejemplo: 1.15", False, None
        
        estado["talla"] = talla
        estado["intentos_fallidos"] = 0
        
        try:
            imc = calcular_imc(estado["peso"], estado["talla"])
            edad = estado["edad"]
            sexo = estado["sexo"]

            ruta_tabla = os.path.join("data", "tablas_percentiles.json")
            try:
                with open(ruta_tabla, "r", encoding="utf-8") as f:
                    tablas = json.load(f)
            except FileNotFoundError:
                return "❌ Error: No se encontró el archivo de tabla de percentiles (tablas_percentiles.json).", False, None
            except json.JSONDecodeError:
                return "❌ Error: El archivo de percentiles tiene un formato JSON inválido.", False, None
            except PermissionError:
                return "❌ Error: No se tienen permisos para leer el archivo de percentiles.", False, None

            if str(edad) not in tablas.get(sexo, {}):
                return f"📊 No hay datos de percentiles para {sexo} de {edad} años. Solo disponible para edades 1-18.", False, None

            clasificacion = clasificar_por_percentil(imc, edad, sexo, tablas)
            graph_id = generar_grafico_percentil(imc, edad, sexo, tablas)
            estado["graph_id"] = graph_id

            nombre = estado.get("nombre")
            mensaje_resultado = confirmacion if 'confirmacion' in locals() else ""
            mensaje_resultado += (
                f"✨ ¡Listo! Calculando...\n\n"
                f"✅ El IMC es: {round(imc, 2)} - Categoría: *{clasificacion.upper()}*\n"
            )
            mensaje_resultado += generar_reporte_resumen(imc, edad, estado["peso"], estado["talla"], clasificacion, nombre)
            mensaje_resultado += "\n\n🔁 ¿Deseas calcular otro IMC? Escribe 'reiniciar'."

            return mensaje_resultado, True, graph_id

        except ValueError:
            estado["intentos_fallidos"] += 1
            return "🚫 Talla no válida. Usa formato como 1.20 (en metros).", False, None
        except Exception as e:
            return f"❌ Error inesperado al procesar los datos: {str(e)}", False, None

    # Comando: Reiniciar
    if normalizar_texto(mensaje) in ["reiniciar", "nuevo", "calcular otro", "empezar", "comenzar"]:
        reiniciar_estado()
        return "🔄 ¡Perfecto! Comenzamos de nuevo. ¿Cómo se llama el menor?", False, None

    # Cualquier otro texto no esperado
    return "🤖 Aún estoy esperando el dato anterior. Si necesitas ayuda, escribe 'reiniciar'.", False, None
