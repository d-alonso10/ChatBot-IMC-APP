# backend/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date, Text, UniqueConstraint
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from database import Base
from auth import hashear_password # Importamos la función de hashing

def generate_uuid():
    return str(uuid.uuid4())

# --- MODELO USER (MODIFICADO) ---
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # Relación: Un usuario (tutor) puede tener muchos pacientes
    pacientes = relationship("Paciente", back_populates="tutor")
    
    # --- NUEVA RELACIÓN ---
    # Un usuario puede tener múltiples dispositivos (teléfono, tablet, etc.)
    devices = relationship("UserDevice", back_populates="user")

    def __init__(self, email, password):
        self.email = email
        self.hashed_password = hashear_password(password) # Hashea la contraseña al crear

# --- ¡NUEVO MODELO PARA FCM! ---
class UserDevice(Base):
    """
    Almacena los tokens de Firebase Cloud Messaging (FCM) 
    para cada dispositivo de un usuario.
    """
    __tablename__ = "user_devices"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # El token de registro de FCM. Puede ser muy largo.
    fcm_token = Column(Text, nullable=False, unique=True) 
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación
    user = relationship("User", back_populates="devices")
    
    # Evitar que el mismo token se registre dos veces (aunque 'unique=True' ya ayuda)
    __table_args__ = (UniqueConstraint('user_id', 'fcm_token', name='_user_device_uc'),)


# --- MODELO PACIENTE (Sin cambios) ---
class Paciente(Base):
    __tablename__ = "pacientes"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    sexo = Column(String, nullable=False) # 'niño' o 'niña'
    tutor_id = Column(Integer, ForeignKey("users.id"))
    
    tutor = relationship("User", back_populates="pacientes")
    calculos = relationship("Calculo", back_populates="calculos")

# --- MODELO CALCULO (Sin cambios) ---
class Calculo(Base):
    __tablename__ = "calculos"

    id = Column(String, primary_key=True, default=generate_uuid)
    peso = Column(Float, nullable=True)
    talla = Column(Float, nullable=True)
    imc = Column(Float, nullable=True)
    clasificacion = Column(String, nullable=True)
    graph_id = Column(String, nullable=True) 
    timestamp = Column(DateTime, default=datetime.utcnow)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"))
    
    paciente = relationship("Paciente", back_populates="calculos")

# --- MODELO PERCENTIL (Sin cambios) ---
class Percentil(Base):
    __tablename__ = "percentiles"

    id = Column(Integer, primary_key=True, index=True)
    sexo = Column(String) # 'niño' or 'niña'
    edad = Column(Integer)
    p5 = Column(Float)
    p85 = Column(Float)
    p95 = Column(Float)