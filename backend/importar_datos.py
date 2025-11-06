# backend/importar_datos.py
import json
from database import SessionLocal, engine
import models

# Asegúrate que las tablas existan
models.Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Revisar si ya hay datos para no duplicar
if db.query(models.Percentil).count() > 0:
    print("Los datos de percentiles ya existen en la base de datos.")
    db.close()
    exit()

print("Cargando datos desde tablas_percentiles.json...")

try:
    with open("data/tablas_percentiles.json", "r", encoding="utf-8") as f:
        tablas_json = json.load(f)

    nuevos_percentiles = []

    for sexo, edades in tablas_json.items():
        for edad_str, valores in edades.items():
            nuevo_registro = models.Percentil(
                sexo=sexo,
                edad=int(edad_str),
                p5=valores['p5'],
                p85=valores['p85'],
                p95=valores['p95']
            )
            nuevos_percentiles.append(nuevo_registro)

    db.add_all(nuevos_percentiles)
    db.commit()
    print(f"¡Éxito! Se importaron {len(nuevos_percentiles)} registros de percentiles a la BD.")

except Exception as e:
    db.rollback()
    print(f"Error al importar datos: {e}")
finally:
    db.close()