import json
import os
from utils import calcular_imc, generar_grafico_percentil, clasificar_por_percentil

estado = {
    "edad": None,
    "sexo": None,
    "peso": None,
    "talla": None
}

def reiniciar_estado():
    global estado
    for key in estado:
        estado[key] = None

def generar_reporte_resumen(imc, edad, peso, talla, clasificacion):
    talla_cm = int(talla * 100)
    resumen = (
        f"\n📋 Resultado para niño de {edad} años:\n"
        f"• Peso: {peso} kg\n"
        f"• Estatura: {talla_cm} cm\n"
        f"• IMC: {round(imc, 2)}\n"
        f"• Categoría: {clasificacion.upper()}\n\n"
        f"👶 Para tu pequeño de {edad} años ({peso}kg, {talla_cm}cm):\n\n"
    )

    if "bajo peso" in clasificacion:
        consejos = (
            "⭐ Consejos prácticos:\n"
            "1. Consulta con el pediatra para descartar causas médicas o nutricionales.\n"
            "2. Ofrécele comidas pequeñas, frecuentes y ricas en nutrientes.\n"
            "3. Añade alimentos con calorías saludables como aceite de oliva, palta o frutos secos molidos.\n\n"
            "💡 Recuerda: Cada niño crece a su propio ritmo."
        )
    elif "peso normal" in clasificacion:
        consejos = (
            "✅ ¡Buen trabajo! Sigue promoviendo estos hábitos:\n"
            "1. Dieta equilibrada rica en frutas, verduras y agua.\n"
            "2. Tiempo activo diario: jugar, correr o bailar.\n"
            "3. Limitar el consumo de azúcar y comida procesada.\n\n"
            "💡 Consejo: La prevención empieza con buenos hábitos."
        )
    elif "riesgo de sobrepeso" in clasificacion:
        consejos = (
            "📉 Riesgo de sobrepeso:\n"
            "1. Reduce azúcares, golosinas y frituras.\n"
            "2. Aumenta la actividad física: mínimo 60 minutos al día.\n"
            "3. No forzar a comer, pero establecer horarios regulares.\n\n"
            "💡 Consejo: Dar ejemplo desde casa ayuda mucho."
        )
    else:
        consejos = (
            "🚨 Atención: El niño presenta obesidad.\n"
            "1. Acude a un pediatra o nutricionista.\n"
            "2. Haz cambios familiares: comida saludable y más actividad.\n"
            "3. Refuerza con amor y apoyo, sin etiquetar ni culpar.\n\n"
            "💡 Tip: No hagas dietas estrictas sin guía médica."
        )

    return resumen + consejos

def procesar_mensaje(mensaje):
    global estado

    mensaje = mensaje.strip()
    if not mensaje:
        return "No recibí nada 😅. Por favor, escribe un dato válido.", False

    # Etapa 1: Edad
    if estado["edad"] is None:
        try:
            edad = int(mensaje)
            if edad < 1 or edad > 18:
                return "📆 Ingresa una edad entre 1 y 18 años.", False
            estado["edad"] = edad
            return "👦 ¿Cuál es el sexo del menor? (escribe 'niño' o 'niña')", False
        except ValueError:
            return "⚠️ Edad no válida. Usa solo números (ej: 5).", False

    # Etapa 2: Sexo
    elif estado["sexo"] is None:
        sexo = mensaje.lower()
        if sexo not in ["niño", "niña"]:
            return "🚻 Por favor, responde con 'niño' o 'niña'.", False
        estado["sexo"] = sexo
        return "⚖️ ¿Cuánto pesa el menor? (en kg, ej: 15.2)", False

    # Etapa 3: Peso
    elif estado["peso"] is None:
        try:
            peso = float(mensaje.replace(",", "."))
            if peso <= 0 or peso > 200:
                return "⚠️ Peso fuera de rango. Ingresa un número realista.", False
            estado["peso"] = peso
            return "📏 ¿Cuál es su talla? (en metros, ej: 1.10)", False
        except ValueError:
            return "🚫 Peso no válido. Usa números como 15.5.", False

    # Etapa 4: Talla
    elif estado["talla"] is None:
        try:
            talla = float(mensaje.replace(",", "."))
            if talla <= 0 or talla > 2.5:
                return "📐 Talla no válida. Ej: 1.15", False
            estado["talla"] = talla

            imc = calcular_imc(estado["peso"], estado["talla"])
            edad = estado["edad"]
            sexo = estado["sexo"]

            ruta_tabla = os.path.join("data", "tablas_percentiles.json")
            try:
                with open(ruta_tabla, "r", encoding="utf-8") as f:
                    tablas = json.load(f)
            except Exception:
                return "❌ No se pudo leer la tabla de percentiles.", False

            if str(edad) not in tablas.get(sexo, {}):
                return f"📊 No hay datos de percentiles para {sexo} de {edad} años.", False

            clasificacion = clasificar_por_percentil(imc, edad, sexo, tablas)
            generar_grafico_percentil(imc, edad, sexo, tablas)

            mensaje = (
                f"✅ El IMC del menor es: {round(imc, 2)} y se encuentra en la categoría: *{clasificacion.upper()}*.\n\n"
            )
            mensaje += generar_reporte_resumen(imc, edad, estado["peso"], estado["talla"], clasificacion)
            mensaje += "\n\n🔁 ¿Deseas calcular otro IMC? Escribe 'reiniciar'."

            return mensaje, True

        except ValueError:
            return "🚫 Talla no válida. Usa formato como 1.20", False

    # Comando: Reiniciar
    elif mensaje.lower() in ["reiniciar", "nuevo", "calcular otro"]:
        reiniciar_estado()
        return "🔄 Comenzamos de nuevo... ¿Qué edad tiene el menor?", False

    # Cualquier otro texto no esperado
    else:
        return "🤖 Aún estoy esperando el dato anterior. Si te confundiste, escribe 'reiniciar'.", False
