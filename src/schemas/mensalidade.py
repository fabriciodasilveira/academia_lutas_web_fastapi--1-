# -*- coding: utf-8 -*-
"""
Schemas Pydantic para a entidade Mensalidade.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

from src.schemas.aluno import AlunoRead
from src.schemas.plano import PlanoRead
from typing import List
from .matricula import MatriculaRead # Importe MatriculaRead

# Schema base para Mensalidade
class MensalidadeBase(BaseModel):
    aluno_id: int
    plano_id: int
    valor: float
    data_vencimento: date
    data_pagamento: Optional[date] = None
    status: str = Field("pendente", max_length=50)

# Schema para criação de Mensalidade
class MensalidadeCreate(MensalidadeBase):
    pass

# Schema para atualização de Mensalidade
class MensalidadeUpdate(BaseModel):
    plano_id: Optional[int] = None
    valor: Optional[float] = None
    data_vencimento: Optional[date] = None
    data_pagamento: Optional[date] = None
    status: Optional[str] = Field(None, max_length=50)

# Schema para leitura/retorno de Mensalidade
class MensalidadeRead(MensalidadeBase):
    id: int
    valor: float
    data_vencimento: date
    data_pagamento: Optional[date] = None
    status: str
    aluno: Optional[AlunoRead] = None
    plano: Optional[PlanoRead] = None
    matricula: Optional[MatriculaRead] = None # Adiciona a matrícula (que contém a turma)

    class Config:
        from_attributes = True

class MensalidadePaginated(BaseModel):
    total: int
    mensalidades: List[MensalidadeRead]

    class Config:
        from_attributes = True # Necessário para Pydantic V2+