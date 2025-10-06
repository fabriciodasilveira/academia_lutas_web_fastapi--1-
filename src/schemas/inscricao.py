# src/schemas/inscricao.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .aluno import AlunoRead

class InscricaoBase(BaseModel):
    aluno_id: int
    evento_id: int

class InscricaoCreate(InscricaoBase):
    pass

class InscricaoRead(InscricaoBase):
    id: int
    data_inscricao: datetime
    status: str
    metodo_pagamento: Optional[str] = None
    valor_pago: Optional[float] = None
    aluno: AlunoRead

    class Config:
        from_attributes = True