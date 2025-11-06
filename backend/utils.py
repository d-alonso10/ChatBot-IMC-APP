import matplotlib.pyplot as plt
import os
import uuid
from typing import Dict, Any, List
from datetime import date
from sqlalchemy.orm import Session
import models  # <--- IMPORTANTE: Añadir import de models 

def calcular_imc(peso: float, talla: float) -> float:
    """
    Calcula el Índice de Masa Corporal (IMC).
    
    Args:
        peso: Peso del menor en kilogramos
        talla: Talla del menor en metros
    
    Returns:
        float: Índice de Masa Corporal calculado
    """
    return peso / (talla ** 2)

def clasificar_por_percentil(imc: float, edad: int, sexo: str, tablas: Dict[str, Any]) -> str:
    """
    Clasifica el IMC según los percentiles definidos en las tablas por edad y sexo.
    
    Args:
        imc: Índice de Masa Corporal calculado
        edad: Edad del menor en años
        sexo: Sexo del menor ('niño' o 'niña')
        tablas: Diccionario con datos de percentiles por edad y sexo
    
    Returns:
        str: Clasificación del IMC (bajo peso, peso normal, riesgo de sobrepeso, obesidad)
    """
    try:
        edad_str = str(edad)
        datos = tablas[sexo][edad_str]

        if imc < datos["p5"]:
            return "bajo peso (percentil < 5)"
        elif imc < datos["p85"]:
            return "peso normal (percentil 5-85)"
        elif imc < datos["p95"]:
            return "riesgo de sobrepeso (percentil 85-95)"
        else:
            return "obesidad (percentil > 95)"
    except KeyError:
        return "No hay datos para esa edad o sexo."

def generar_grafico_percentil(imc_usuario: float, edad: int, sexo: str, tablas: Dict[str, Any]) -> str:
    """
    Genera un gráfico del IMC comparado con percentiles saludables por edad y sexo.
    Guarda el gráfico con un nombre único basado en UUID.
    
    Args:
        imc_usuario: IMC calculado del menor
        edad: Edad del menor en años
        sexo: Sexo del menor ('niño' o 'niña')
        tablas: Diccionario con datos de percentiles por edad y sexo
    
    Returns:
        str: ID único del gráfico generado (UUID)
    """
    edad_int = int(edad)
    
    # Asegurarse de que las claves sean strings para la búsqueda
    edades_str = tablas.get(sexo, {}).keys()
    if not edades_str:
        raise KeyError(f"No se encontraron datos de percentiles para el sexo: {sexo}")
        
    edades = sorted([int(k) for k in edades_str])
    
    # Convertir edades a string al acceder al dict
    p5 = [tablas[sexo][str(e)]["p5"] for e in edades]
    p85 = [tablas[sexo][str(e)]["p85"] for e in edades]
    p95 = [tablas[sexo][str(e)]["p95"] for e in edades]

    plt.figure(figsize=(10, 6))
    plt.plot(edades, p5, label="Límite mínimo saludable", linestyle="--", color="orange", linewidth=2.5)
    plt.plot(edades, p85, label="Inicio del sobrepeso", linestyle="--", color="orangered", linewidth=2.5)
    plt.plot(edades, p95, label="Límite de obesidad", linestyle="--", color="crimson", linewidth=2.5)

    # Punto del menor
    plt.scatter([edad_int], [imc_usuario], color="red", s=150, edgecolors="black",
                linewidths=2, zorder=5, label=f"Niño/a ({imc_usuario:.1f})")

    # Recomendación visual (usar str(edad) para buscar)
    try:
        datos_edad_actual = tablas[sexo][str(edad)]
    except KeyError:
         raise KeyError(f"No se encontraron datos de percentiles para la edad: {edad}")

    if imc_usuario < datos_edad_actual["p5"]:
        texto = "Recomendación: Bajo peso, evalúe con pediatra."
    elif imc_usuario < datos_edad_actual["p85"]:
        texto = "Recomendación: Peso saludable, siga con buenos hábitos."
    elif imc_usuario < datos_edad_actual["p95"]:
        texto = "Recomendación: Riesgo de sobrepeso, controle dieta y actividad."
    else:
        texto = "Recomendación: Obesidad, consultar especialista."


    # Mostrar recomendación sobre el gráfico
    plt.text(edad_int + 0.5, imc_usuario + 0.5, texto,
             fontsize=12, weight='bold', color='black',
             bbox=dict(facecolor='lightyellow', edgecolor='gray', boxstyle='round,pad=0.4'))

    plt.title("Gráfico de Percentiles de IMC (1 a 18 años)", fontsize=16)
    plt.xlabel("Edad (años)", fontsize=13)
    plt.ylabel("IMC", fontsize=13)
    plt.xticks(fontsize=11)
    plt.yticks(fontsize=11)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(fontsize=11)
    plt.tight_layout()

    # Generar nombre único para el gráfico
    graph_id = str(uuid.uuid4())
    graph_filename = f"grafico_{graph_id}.png"
    
    os.makedirs("graficos", exist_ok=True)
    plt.savefig(os.path.join("graficos", graph_filename))
    plt.close()
    
    return graph_id

# --- NUEVA FUNCIÓN AÑADIDA ---

def cargar_percentiles_db(db: Session) -> Dict[str, Any]:
    """
    Carga los datos de percentiles desde la base de datos y los formatea
    en el diccionario anidado que espera la lógica del chatbot.
    
    Args:
        db: Sesión de base de datos
    
    Returns:
        Dict[str, Any]: Diccionario formateado {'niño': {'1': {...}, ...}, 'niña': ...}
    """
    tablas = {"niño": {}, "niña": {}}
    try:
        todos_los_percentiles = db.query(models.Percentil).all()
        
        if not todos_los_percentiles:
            raise Exception("Base de datos de percentiles vacía. ¿Ejecutaste importar_datos.py?")

        for p in todos_los_percentiles:
            edad_str = str(p.edad)
            if p.sexo not in tablas:
                tablas[p.sexo] = {}
            
            tablas[p.sexo][edad_str] = {
                "p5": p.p5,
                "p85": p.p85,
                "p95": p.p95
            }
        
        return tablas
        
    except Exception as e:
        print(f"Error crítico al cargar percentiles desde la BD: {e}")
        # Retornar vacío hará que el chatbot falle con un error controlado
        return {"niño": {}, "niña": {}}
    
def _calcular_edad_en_meses(fecha_nacimiento: date, fecha_calculo: date) -> int:
    """Calcula la edad en meses en una fecha específica."""
    return (fecha_calculo.year - fecha_nacimiento.year) * 12 + (fecha_calculo.month - fecha_nacimiento.month)

def generar_grafico_historial(paciente: models.Paciente, historial: List[models.Calculo], db: Session) -> str:
    """
    Genera un gráfico de percentiles con la LÍNEA DE HISTORIAL completa del paciente.
    """
    # 1. Cargar las tablas de percentiles
    tablas = cargar_percentiles_db(db)
    sexo = paciente.sexo
    
    edades_str = tablas.get(sexo, {}).keys()
    if not edades_str:
        raise KeyError(f"No se encontraron datos de percentiles para el sexo: {sexo}")
        
    edades_percentiles = sorted([int(k) for k in edades_str])
    
    p5 = [tablas[sexo][str(e)]["p5"] for e in edades_percentiles]
    p85 = [tablas[sexo][str(e)]["p85"] for e in edades_percentiles]
    p95 = [tablas[sexo][str(e)]["p95"] for e in edades_percentiles]

    # 2. Preparar datos del historial del paciente
    historial_puntos = []
    for calculo in historial:
        if calculo.imc is None: # Omitir cálculos incompletos
            continue
        # Usamos la edad en meses para mayor precisión en el gráfico
        edad_meses = _calcular_edad_en_meses(paciente.fecha_nacimiento, calculo.timestamp.date())
        # Convertimos a "años" fraccionales para el eje X
        edad_fraccional = edad_meses / 12.0
        historial_puntos.append((edad_fraccional, calculo.imc))
    
    # Ordenar por edad para que la línea se dibuje correctamente
    historial_puntos.sort(key=lambda x: x[0])
    
    historial_edades = [p[0] for p in historial_puntos]
    historial_imcs = [p[1] for p in historial_puntos]

    # 3. Dibujar el Gráfico
    plt.figure(figsize=(10, 6))
    
    # Líneas de percentiles
    plt.plot(edades_percentiles, p5, label="Límite mínimo saludable", linestyle="--", color="orange", linewidth=2.5)
    plt.plot(edades_percentiles, p85, label="Inicio del sobrepeso", linestyle="--", color="orangered", linewidth=2.5)
    plt.plot(edades_percentiles, p95, label="Límite de obesidad", linestyle="--", color="crimson", linewidth=2.5)

    # ¡LA MAGIA! Línea de historial del paciente
    if len(historial_puntos) > 0:
        plt.plot(historial_edades, historial_imcs, 
                 label=f"Evolución de {paciente.nombre}", 
                 color="blue", 
                 linewidth=2, 
                 marker='o', # Poner un punto en cada cálculo
                 markersize=8)
        
        # Marcar el último punto de forma especial
        plt.scatter([historial_edades[-1]], [historial_imcs[-1]], 
                    color="red", s=150, edgecolors="black", 
                    linewidths=2, zorder=5, label="Último Cálculo")

    plt.title(f"Curva de Crecimiento de {paciente.nombre}", fontsize=16)
    plt.xlabel("Edad (años)", fontsize=13)
    plt.ylabel("IMC", fontsize=13)
    plt.xticks(fontsize=11)
    plt.yticks(fontsize=11)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(fontsize=11)
    plt.tight_layout()

    # 4. Guardar Gráfico
    # Usamos el ID del paciente para el nombre. De esta forma, el gráfico
    # se sobrescribe y actualiza cada vez, evitando crear basura.
    graph_id = f"historial_{paciente.id}"
    graph_filename = f"grafico_{graph_id}.png"
    
    os.makedirs("graficos", exist_ok=True)
    plt.savefig(os.path.join("graficos", graph_filename))
    plt.close()
    
    return graph_id