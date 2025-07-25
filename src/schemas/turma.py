# -*- coding: utf-8 -*-
"""
Schemas Pydantic para a entidade Turma.
"""

from pydantic import BaseModel, Field
from typing import Optional, List

# Schema base para Turma
class TurmaBase(BaseModel):
    modalidade: str = Field(..., max_length=50)
    horario: str = Field(..., max_length=50)
    dias_semana: str = Field(..., max_length=100)
    professor_id: Optional[int] = None # ID do professor associado
    nivel: Optional[str] = Field(None, max_length=50)
    capacidade_maxima: Optional[int] = None

# Schema para criação de Turma
class TurmaCreate(TurmaBase):
    pass

# Schema para atualização de Turma
class TurmaUpdate(BaseModel):
    modalidade: Optional[str] = Field(None, max_length=50)
    horario: Optional[str] = Field(None, max_length=50)
    dias_semana: Optional[str] = Field(None, max_length=100)
    professor_id: Optional[int] = None
    nivel: Optional[str] = Field(None, max_length=50)
    capacidade_maxima: Optional[int] = None

# Schema para leitura/retorno de Turma
# Pode incluir dados do professor relacionado se desejado
class TurmaRead(TurmaBase):
    id: int
    # Para incluir dados do professor, precisaria de um schema ProfessorRead nested
    # professor: Optional[ProfessorRead] = None # Exemplo

    class Config:
        orm_mode = True

