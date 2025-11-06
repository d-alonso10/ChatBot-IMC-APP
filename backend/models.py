# backend/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from database import Base
from auth import hashear_password # Importamos la función de hashing

def generate_uuid():
    return str(uuid.uuid4())

# --- NUEVO MODELO ---
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # Relación: Un usuario (tutor) puede tener muchos pacientes
    pacientes = relationship("Paciente", back_populates="tutor")

    def __init__(self, email, password):
        self.email = email
        self.hashed_password = hashear_password(password) # Hashea la contraseña al crear

# --- NUEVO MODELO ---
class Paciente(Base):
    __tablename__ = "pacientes"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    sexo = Column(String, nullable=False) # 'niño' o 'niña'
    
    # Clave foránea para vincular al usuario/tutor
    tutor_id = Column(Integer, ForeignKey("users.id"))
    
    # Relaciones
    tutor = relationship("User", back_populates="pacientes")
    calculos = relationship("Calculo", back_populates="paciente")

# --- MODELO MODIFICADO ---
class Calculo(Base):
    __tablename__ = "calculos"

    # ID de conversación único, sigue siendo útil
    id = Column(String, primary_key=True, default=generate_uuid)
    
    # --- Campos eliminados ---
    # nombre = Column(String, nullable=True)  <- ELIMINADO
    # edad = Column(Integer, nullable=True)   <- ELIMINADO
    # sexo = Column(String, nullable=True)    <- ELIMINADO
    
    # --- Campos mantenidos/nuevos ---
    peso = Column(Float, nullable=True)
    talla = Column(Float, nullable=True)
    
    # Resultados
    imc = Column(Float, nullable=True)
    clasificacion = Column(String, nullable=True)
    graph_id = Column(String, nullable=True) 
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Clave foránea para vincular al paciente
    paciente_id = Column(Integer, ForeignKey("pacientes.id"))
    
    # Relación
    paciente = relationship("Paciente", back_populates="calculos")


class Percentil(Base):
    __tablename__ = "percentiles"

    id = Column(Integer, primary_key=True, index=True)
    sexo = Column(String) # 'niño' or 'niña'
    edad = Column(Integer)
    p5 = Column(Float)
    p85 = Column(Float)
    p95 = Column(Float)