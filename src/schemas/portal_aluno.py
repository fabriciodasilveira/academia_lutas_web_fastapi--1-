from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date

class AlunoRegistration(BaseModel):
    nome: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    telefone: Optional[str] = None
    data_nascimento: Optional[date] = None