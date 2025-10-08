# REMOVA as linhas de update_forward_refs daqui

# -*- coding: utf-8 -*-
"""
Schemas Pydantic para a entidade Aluno.
"""

import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl

class AlunoBase(BaseModel):
    nome: str = Field(..., example="João da Silva")
    data_nascimento: Optional[datetime.date] = Field(None, example="2000-01-01")
    cpf: Optional[str] = Field(None, example="123.456.789-00", max_length=14)
    telefone: Optional[str] = Field(None, example="(21) 98765-4321", max_length=20)
    email: Optional[str] = Field(None, example="joao.silva@email.com")
    endereco: Optional[str] = Field(None, example="Rua Principal, 123, Rio de Janeiro")
    observacoes: Optional[str] = Field(None, example="Aluno iniciante com experiência em boxe.")
    
# Schema para criação de Aluno
class AlunoCreate(AlunoBase):
    pass

# Em src/schemas/aluno.py

class AlunoRead(AlunoBase):
    id: int
    foto: Optional[str] = None # Garante que o campo 'foto' está aqui
    data_cadastro: datetime.datetime
    status_geral: str = "Inativo"

    class Config:
        from_attributes = True 

# Schema para atualização de Aluno
class AlunoUpdate(BaseModel):
    nome: Optional[str] = Field(None, example="João da Silva")
    data_nascimento: Optional[datetime.date] = Field(None, example="2000-01-01")
    cpf: Optional[str] = Field(None, example="123.456.789-00", max_length=14)
    telefone: Optional[str] = Field(None, example="(21) 98765-4321", max_length=20)
    email: Optional[str] = Field(None, example="joao.silva@email.com")
    endereco: Optional[str] = Field(None, example="Rua Principal, 123, Rio de Janeiro")
    observacoes: Optional[str] = Field(None, example="Aluno iniciante com experiência em boxe.")


class AlunoPaginated(BaseModel):
    total: int
    alunos: List[AlunoRead]