# backend/schemas.py
from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional, List

# --- Schemas de Paciente ---
class PacienteBase(BaseModel):
    nombre: str
    fecha_nacimiento: date
    sexo: str # 'niño' o 'niña'

class PacienteCreate(PacienteBase):
    pass

class Paciente(PacienteBase):
    id: int
    tutor_id: int

    class Config:
        from_attributes = True # <-- CORREGIDO (antes orm_mode)

class Calculo(BaseModel):
    id: str
    peso: Optional[float] = None
    talla: Optional[float] = None
    imc: Optional[float] = None
    clasificacion: Optional[str] = None
    graph_id: Optional[str] = None
    timestamp: datetime
    paciente_id: int

    class Config:
        from_attributes = True



# --- Schemas de User (Tutor) ---
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    pacientes: List[Paciente] = []

    class Config:
        from_attributes = True # <-- CORREGIDO (antes orm_mode)

# --- Schemas de Autenticación (Token) ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# --- Schemas del Chat (Modificados) ---
class Mensaje(BaseModel):
    texto: str
    paciente_id: int  # <-- AHORA ES REQUERIDO
    conversation_id: str | None = None # Sigue siendo opcional para iniciar

class RespuestaChat(BaseModel):
    respuesta: str
    grafico: bool
    graph_id: str | None = None
    conversation_id: str | None = None