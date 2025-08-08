# -*- coding: utf-8 -*-
"""
Schemas Pydantic para a entidade Professor.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import date

# Schema base para Professor
class ProfessorBase(BaseModel):
    nome: str = Field(..., max_length=100)
    cpf: Optional[str] = Field(None, max_length=14)
    data_nascimento: Optional[date] = None
    telefone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = Field(None, max_length=100)
    endereco: Optional[str] = Field(None, max_length=200)
    especialidade: Optional[str] = Field(None, max_length=100)
    formacao: Optional[str] = Field(None, max_length=200)
    data_contratacao: Optional[date] = None
    observacoes: Optional[str] = None
    foto: Optional[str] = Field(None, max_length=255) # Caminho/URL da foto

# Schema para criação de Professor
class ProfessorCreate(ProfessorBase):
    pass

# Schema para atualização de Professor
class ProfessorUpdate(BaseModel):
    nome: Optional[str] = Field(None, max_length=100)
    cpf: Optional[str] = Field(None, max_length=14)
    data_nascimento: Optional[date] = None
    telefone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = Field(None, max_length=100)
    endereco: Optional[str] = Field(None, max_length=200)
    especialidade: Optional[str] = Field(None, max_length=100)
    formacao: Optional[str] = Field(None, max_length=200)
    data_contratacao: Optional[date] = None
    observacoes: Optional[str] = None
    # Atualização de foto via endpoint específico

# Schema para leitura/retorno de Professor
class ProfessorRead(ProfessorBase):
    id: int

    class Config:
        orm_mode = True

