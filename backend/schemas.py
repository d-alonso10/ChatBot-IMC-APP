# backend/schemas.py
from pydantic import BaseModel, EmailStr
from datetime import date, datetime
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
        orm_mode = True # <-- CORREGIDO (compatible con Pydantic v1)

# --- Schema de Cálculo ---
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
        orm_mode = True # <-- CORREGIDO (compatible con Pydantic v1)

# --- Schemas de User (Tutor) ---
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    pacientes: List[Paciente] = []

    class Config:
        orm_mode = True # <-- CORREGIDO (compatible con Pydantic v1)

# --- Schemas de Autenticación (Token) ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# --- Schemas del Chat (Modificados) ---
class Mensaje(BaseModel):
    texto: str
    paciente_id: int
    conversation_id: str | None = None

class RespuestaChat(BaseModel):
    respuesta: str
    grafico: bool
    graph_id: str | None = None
    conversation_id: str | None = None