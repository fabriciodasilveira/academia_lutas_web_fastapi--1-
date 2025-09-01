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

# Schema base para Matrícula
class MatriculaBase(BaseModel):
    aluno_id: int
    turma_id: int
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

# Schema para leitura/retorno de Matrícula
class MatriculaRead(MatriculaBase):
    id: int
    aluno: AlunoRead
    turma: TurmaRead

    class Config:
        orm_mode = True