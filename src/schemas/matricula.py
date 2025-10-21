# REMOVA as linhas de update_forward_refs daqui

# # -*- coding: utf-8 -*-
# """
# Schemas Pydantic para a entidade Matrícula.
# """

from pydantic import BaseModel
from typing import Optional
from datetime import date

from src.schemas.aluno import AlunoRead
from src.schemas.turma import TurmaRead

from src.schemas.plano import PlanoRead # ADICIONAR ESTE IMPORT

# Schema base para Matrícula
class MatriculaBase(BaseModel):
    aluno_id: int
    turma_id: int
    plano_id: int # ADICIONAR ESTA LINHA
    data_matricula: Optional[date] = None
    ativa: Optional[bool] = True

# Schema para criação de Matrícula
class MatriculaCreate(MatriculaBase):
    pass

# Schema para atualização de Matrícula
class MatriculaUpdate(BaseModel):
    aluno_id: Optional[int] = None
    turma_id: Optional[int] = None
    ativa: Optional[bool] = None

class MatriculaRead(MatriculaBase):
    id: int
    data_matricula: Optional[date] = None
    ativa: bool
    aluno: Optional[AlunoRead] = None # Inclui dados do aluno
    turma: Optional[TurmaRead] = None # Inclui dados da turma
    plano: Optional[PlanoRead] = None # Inclui dados do plano

    class Config:
        from_attributes = True