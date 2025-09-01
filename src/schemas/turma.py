# -*- coding: utf-8 -*-
"""
Schemas Pydantic para a entidade Turma.
"""

from pydantic import BaseModel, Field
from typing import Optional, List

# Schema base para Turma
class TurmaBase(BaseModel):
    # Campos que estavam no frontend, mas não no schema da API
    nome: Optional[str] = Field(None, max_length=100)
    descricao: Optional[str] = Field(None, max_length=255)
    observacoes: Optional[str] = Field(None, max_length=255)
    valor_mensalidade: Optional[float] = None
    idade_minima: Optional[int] = None
    ativa: Optional[bool] = True

    modalidade: str = Field(..., max_length=50)
    horario: str = Field(..., max_length=50)
    dias_semana: str = Field(..., max_length=100)
    professor_id: Optional[int] = None # ID do professor associado
    nivel: Optional[str] = Field(None, max_length=50)
    capacidade_maxima: Optional[int] = None
    total_alunos: Optional[int] = 0 # Adicione esta linha

# Schema para criação de Turma
class TurmaCreate(TurmaBase):
    pass

# Schema para atualização de Turma
class TurmaUpdate(BaseModel):
    # Todos os campos são opcionais para permitir atualizações parciais
    nome: Optional[str] = Field(None, max_length=100)
    descricao: Optional[str] = Field(None, max_length=255)
    observacoes: Optional[str] = Field(None, max_length=255)
    valor_mensalidade: Optional[float] = None
    idade_minima: Optional[int] = None
    ativa: Optional[bool] = None

    modalidade: Optional[str] = Field(None, max_length=50)
    horario: Optional[str] = Field(None, max_length=50)
    dias_semana: Optional[str] = Field(None, max_length=100)
    professor_id: Optional[int] = None
    nivel: Optional[str] = Field(None, max_length=50)
    capacidade_maxima: Optional[int] = None
    total_alunos: Optional[int] = 0 # Adicione esta linha

# Schema para leitura/retorno de Turma
class TurmaRead(TurmaBase):
    id: int
    
    class Config:
        orm_mode = True

