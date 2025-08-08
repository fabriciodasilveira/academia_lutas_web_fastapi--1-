# -*- coding: utf-8 -*-
"""
Schemas Pydantic para a entidade Aluno.
Define a estrutura dos dados para validação e serialização.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import date, datetime

# Schema base para Aluno (campos comuns)
class AlunoBase(BaseModel):
    nome: str = Field(..., max_length=100)
    data_nascimento: Optional[date] = None
    cpf: Optional[str] = Field(None, max_length=14) # Considerar validação de formato
    telefone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = Field(None, max_length=100)
    endereco: Optional[str] = Field(None, max_length=200)
    observacoes: Optional[str] = None
    foto: Optional[str] = Field(None, max_length=255) # Armazena o caminho/URL da foto

# Schema para criação de Aluno (herda de AlunoBase)
# Não inclui ID ou data_cadastro, que são gerados automaticamente
class AlunoCreate(AlunoBase):
    pass

# Schema para atualização de Aluno (herda de AlunoBase)
# Todos os campos são opcionais na atualização
class AlunoUpdate(BaseModel):
    nome: Optional[str] = Field(None, max_length=100)
    data_nascimento: Optional[date] = None
    cpf: Optional[str] = Field(None, max_length=14)
    telefone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = Field(None, max_length=100)
    endereco: Optional[str] = Field(None, max_length=200)
    observacoes: Optional[str] = None
    # A atualização da foto pode precisar de um endpoint/lógica separada
    # foto: Optional[str] = Field(None, max_length=255)

# Schema para leitura/retorno de Aluno (herda de AlunoBase)
# Inclui campos gerados automaticamente como ID e data_cadastro
class AlunoRead(AlunoBase):
    id: int
    data_cadastro: datetime

    class Config:
        orm_mode = True # Permite que o Pydantic leia dados de objetos ORM

