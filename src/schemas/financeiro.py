# src/schemas/financeiro.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FinanceiroBase(BaseModel):
    tipo: str
    categoria: str
    descricao: str
    valor: float
    data: Optional[datetime] = None
    status: Optional[str] = "confirmado"
    observacoes: Optional[str] = None
    forma_pagamento: Optional[str] = None
    
    # NOVOS CAMPOS PARA O PAGAMENTO DE SALÁRIO
    beneficiario_id: Optional[int] = None
    valor_abatido_caixa: Optional[float] = 0.0

class FinanceiroCreate(FinanceiroBase):
    pass

class FinanceiroUpdate(FinanceiroBase):
    tipo: Optional[str] = None
    categoria: Optional[str] = None
    descricao: Optional[str] = None
    valor: Optional[float] = None
    beneficiario_id: Optional[int] = None
    valor_abatido_caixa: Optional[float] = None

class FinanceiroRead(FinanceiroBase):
    id: int
    responsavel_id: Optional[int] = None

    class Config:
        orm_mode = True