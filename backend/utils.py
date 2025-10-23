import matplotlib.pyplot as plt
import os

def calcular_imc(peso, talla):
    """
    Calcula el Índice de Masa Corporal (IMC).
    """
    return peso / (talla ** 2)

def clasificar_por_percentil(imc, edad, sexo, tablas):
    """
    Clasifica el IMC según los percentiles definidos en las tablas por edad y sexo.
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

def generar_grafico_percentil(imc_usuario, edad, sexo, tablas):
    """
    Genera un gráfico del IMC comparado con percentiles saludables por edad y sexo.
    Guarda el gráfico como 'ultima_grafica.png'.
    """
    edad_int = int(edad)
    edades = sorted([int(k) for k in tablas[sexo].keys()])

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

    # Recomendación visual
    if imc_usuario < tablas[sexo][str(edad)]["p5"]:
        texto = "Recomendación: Bajo peso, evalúe con pediatra."
    elif imc_usuario < tablas[sexo][str(edad)]["p85"]:
        texto = "Recomendación: Peso saludable, siga con buenos hábitos."
    elif imc_usuario < tablas[sexo][str(edad)]["p95"]:
        texto = "Recomendación: Riesgo de sobrepeso, controle dieta y actividad."
    else:
        texto = "Recomendación: Obesidad, consultar especialista."

    # Mostrar recomendación sobre el gráfico
    plt.text(edad_int + 0.5, imc_usuario + 0.5, texto,
             fontsize=12, weight='bold', color='black',
             bbox=dict(facecolor='lightyellow', edgecolor='gray', boxstyle='round,pad=0.4'))

    plt.title("Gráfico de Percentiles de IMC (1 a 12 años)", fontsize=16)
    plt.xlabel("Edad (años)", fontsize=13)
    plt.ylabel("IMC", fontsize=13)
    plt.xticks(fontsize=11)
    plt.yticks(fontsize=11)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(fontsize=11)
    plt.tight_layout()

    os.makedirs("data", exist_ok=True)
    plt.savefig("ultima_grafica.png")
    plt.close()
