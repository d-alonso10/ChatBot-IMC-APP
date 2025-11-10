# backend/utils.py
import matplotlib.pyplot as plt
import os
import uuid
from typing import Dict, Any, List
from sqlalchemy.orm import Session
import models
from datetime import date, datetime

# --- Imports para PDF (Nuevos) ---
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.utils import ImageReader
import io

# --- Funciones Helper ---

def _calcular_edad(fecha_nacimiento: date) -> int:
    """Calcula la edad en años."""
    hoy = date.today()
    edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
    return edad

def _calcular_edad_en_meses(fecha_nacimiento: date, fecha_calculo: date) -> int:
    """Calcula la edad en meses en una fecha específica."""
    return (fecha_calculo.year - fecha_nacimiento.year) * 12 + (fecha_calculo.month - fecha_nacimiento.month)

def _get_edad_string(fecha_nacimiento: date, fecha_calculo: date) -> str:
    """Devuelve un string 'X años, Y meses'."""
    total_meses = _calcular_edad_en_meses(fecha_nacimiento, fecha_calculo)
    anios = total_meses // 12
    meses = total_meses % 12
    return f"{anios}a, {meses}m"

# --- Funciones de Cálculo y Clasificación (Sin Cambios) ---

def calcular_imc(peso: float, talla: float) -> float:
    """Calcula el Índice de Masa Corporal (IMC)."""
    return peso / (talla ** 2)

def clasificar_por_percentil(imc: float, edad: int, sexo: str, tablas: Dict[str, Any]) -> str:
    """Clasifica el IMC según los percentiles."""
    try:
        edad_str = str(edad)
        datos = tablas[sexo][edad_str]

        if imc < datos["p5"]:
            return "Bajo Peso"
        elif imc < datos["p85"]:
            return "Peso Normal"
        elif imc < datos["p95"]:
            return "Riesgo de Sobrepeso"
        else:
            return "Obesidad"
    except KeyError:
        return "No hay datos para esa edad o sexo."

def cargar_percentiles_db(db: Session) -> Dict[str, Any]:
    """Carga los datos de percentiles desde la base de datos."""
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
        return {"niño": {}, "niña": {}}

# --- Funciones de Gráficos (MODIFICADAS Y NUEVAS) ---

def generar_grafico_simple(
    historial: List[models.Calculo],
    paciente: models.Paciente,
    metrica: str # 'peso' o 'talla'
) -> str:
    """
    Genera un gráfico de línea simple para la evolución del peso o la talla.
    Guarda el gráfico con un ID único basado en el paciente y la métrica.
    """
    
    # 1. Preparar datos del historial
    historial_puntos = []
    for calculo in historial:
        valor = getattr(calculo, metrica)
        if valor is None:
            continue
        edad_meses = _calcular_edad_en_meses(paciente.fecha_nacimiento, calculo.timestamp.date())
        edad_fraccional = edad_meses / 12.0
        historial_puntos.append((edad_fraccional, valor))
    
    historial_puntos.sort(key=lambda x: x[0])
    
    historial_edades = [p[0] for p in historial_puntos]
    historial_valores = [p[1] for p in historial_puntos]

    # 2. Dibujar el Gráfico
    plt.figure(figsize=(10, 6))
    
    if len(historial_puntos) > 0:
        plt.plot(historial_edades, historial_valores, 
                 label=f"Evolución de {metrica}", 
                 color="blue", 
                 linewidth=2, 
                 marker='o',
                 markersize=8)
        
        plt.scatter([historial_edades[-1]], [historial_valores[-1]], 
                    color="red", s=150, edgecolors="black", 
                    linewidths=2, zorder=5, label="Último Cálculo")

    titulo_grafico = "Peso" if metrica == 'peso' else "Talla"
    label_y = "Peso (kg)" if metrica == 'peso' else "Talla (m)"
    
    plt.title(f"Curva de Crecimiento ({titulo_grafico}) de {paciente.nombre}", fontsize=16)
    plt.xlabel("Edad (años)", fontsize=13)
    plt.ylabel(label_y, fontsize=13)
    plt.xticks(fontsize=11)
    plt.yticks(fontsize=11)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(fontsize=11)
    plt.tight_layout()

    # 3. Guardar Gráfico
    graph_id = f"{metrica}_{paciente.id}"
    graph_filename = f"grafico_{graph_id}.png"
    
    os.makedirs("graficos", exist_ok=True)
    plt.savefig(os.path.join("graficos", graph_filename))
    plt.close()
    
    return graph_id

def generar_grafico_historial(
    paciente: models.Paciente,
    historial: List[models.Calculo],
    db: Session,
    return_bytes: bool = False
) -> str | io.BytesIO:
    """
    Genera el gráfico de percentiles con la LÍNEA DE HISTORIAL completa.
    Ahora puede devolver un ID o los bytes de la imagen (para el PDF).
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
        if calculo.imc is None:
            continue
        edad_meses = _calcular_edad_en_meses(paciente.fecha_nacimiento, calculo.timestamp.date())
        edad_fraccional = edad_meses / 12.0
        historial_puntos.append((edad_fraccional, calculo.imc))
    
    historial_puntos.sort(key=lambda x: x[0])
    
    historial_edades = [p[0] for p in historial_puntos]
    historial_imcs = [p[1] for p in historial_puntos]

    # 3. Dibujar el Gráfico
    plt.figure(figsize=(10, 6))
    
    plt.plot(edades_percentiles, p5, label="Límite mínimo saludable", linestyle="--", color="orange", linewidth=2.5)
    plt.plot(edades_percentiles, p85, label="Inicio del sobrepeso", linestyle="--", color="orangered", linewidth=2.5)
    plt.plot(edades_percentiles, p95, label="Límite de obesidad", linestyle="--", color="crimson", linewidth=2.5)

    if len(historial_puntos) > 0:
        plt.plot(historial_edades, historial_imcs, 
                 label=f"Evolución de {paciente.nombre}", 
                 color="blue", 
                 linewidth=2, 
                 marker='o',
                 markersize=8)
        
        plt.scatter([historial_edades[-1]], [historial_imcs[-1]], 
                    color="red", s=150, edgecolors="black", 
                    linewidths=2, zorder=5, label="Último Cálculo")

    plt.title(f"Curva de Crecimiento (IMC) de {paciente.nombre}", fontsize=16)
    plt.xlabel("Edad (años)", fontsize=13)
    plt.ylabel("IMC", fontsize=13)
    plt.xticks(fontsize=11)
    plt.yticks(fontsize=11)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(fontsize=11)
    plt.tight_layout()

    # 4. Guardar Gráfico (o devolver bytes)
    graph_id = f"historial_{paciente.id}"
    
    if return_bytes:
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png')
        plt.close()
        img_buffer.seek(0)
        return img_buffer
    else:
        graph_filename = f"grafico_{graph_id}.png"
        os.makedirs("graficos", exist_ok=True)
        plt.savefig(os.path.join("graficos", graph_filename))
        plt.close()
        return graph_id

# --- NUEVA FUNCIÓN DE PDF ---

def generar_reporte_pdf(paciente: models.Paciente, historial: List[models.Calculo], db: Session) -> io.BytesIO:
    """
    Genera un reporte PDF completo con el historial y el gráfico del paciente.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=cm, leftMargin=cm, topMargin=cm, bottomMargin=cm)
    styles = getSampleStyleSheet()
    story = []

    # 1. Título
    titulo = f"Reporte de Crecimiento Pediátrico"
    story.append(Paragraph(titulo, styles['h1']))
    story.append(Spacer(1, 0.25 * inch))

    # 2. Datos del Paciente
    story.append(Paragraph(f"<b>Paciente:</b> {paciente.nombre}", styles['Normal']))
    story.append(Paragraph(f"<b>Fecha de Nacimiento:</b> {paciente.fecha_nacimiento.strftime('%d/%m/%Y')}", styles['Normal']))
    story.append(Paragraph(f"<b>Sexo:</b> {paciente.sexo.capitalize()}", styles['Normal']))
    story.append(Paragraph(f"<b>Tutor:</b> {paciente.tutor.email}", styles['Normal']))
    story.append(Paragraph(f"<b>Fecha de Reporte:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 0.5 * inch))

    # 3. Gráfico de Historial IMC
    story.append(Paragraph("Gráfico de Evolución de IMC", styles['h2']))
    try:
        # Obtener los bytes del gráfico
        grafico_bytes = generar_grafico_historial(paciente, historial, db, return_bytes=True)
        # Ajustar el tamaño de la imagen al PDF
        img = Image(grafico_bytes)
        img.drawHeight = 5 * inch
        img.drawWidth = 7 * inch
        img.hAlign = 'CENTER'
        story.append(img)
    except Exception as e:
        story.append(Paragraph(f"Error al generar gráfico: {e}", styles['Normal']))
        
    story.append(Spacer(1, 0.5 * inch))

    # 4. Tabla de Historial
    story.append(Paragraph("Registros Históricos", styles['h2']))
    
    # Encabezados de la tabla
    data = [["Fecha", "Edad", "Peso (kg)", "Talla (m)", "IMC", "Clasificación"]]
    
    # Llenar la tabla con datos
    for calculo in historial:
        fecha_str = calculo.timestamp.strftime('%d/%m/%Y')
        edad_str = _get_edad_string(paciente.fecha_nacimiento, calculo.timestamp.date())
        data.append([
            fecha_str,
            edad_str,
            f"{calculo.peso:.1f}",
            f"{calculo.talla:.2f}",
            f"{calculo.imc:.1f}",
            calculo.clasificacion
        ])

    # Estilo de la tabla
    t = Table(data, colWidths=[1.5*inch, 1.5*inch, 1*inch, 1*inch, 0.8*inch, 2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#7E57C2")), # Cabecera morada
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#EDE7F6")), # Filas lila claro
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(t)
    doc.build(story)
    
    buffer.seek(0)
    return buffer