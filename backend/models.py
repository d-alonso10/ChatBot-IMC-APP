from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Calculo(Base):
    __tablename__ = "calculos"

    # ID de conversación único
    id = Column(String, primary_key=True, default=generate_uuid)
    nombre = Column(String, nullable=True)
    edad = Column(Integer, nullable=True)
    sexo = Column(String, nullable=True)
    peso = Column(Float, nullable=True)
    talla = Column(Float, nullable=True)

    # Resultados
    imc = Column(Float, nullable=True)
    clasificacion = Column(String, nullable=True)
    graph_id = Column(String, nullable=True) # Guardamos solo el ID
    timestamp = Column(DateTime, default=datetime.utcnow)

class Percentil(Base):
    __tablename__ = "percentiles"

    id = Column(Integer, primary_key=True, index=True)
    sexo = Column(String) # 'niño' or 'niña'
    edad = Column(Integer)
    p5 = Column(Float)
    p85 = Column(Float)
    p95 = Column(Float)

# (Opcional) Puedes añadir una tabla de Usuario si quieres login