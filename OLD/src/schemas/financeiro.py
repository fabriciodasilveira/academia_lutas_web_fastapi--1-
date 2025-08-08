# -*- coding: utf-8 -*-
"""
Schemas Pydantic para a entidade Financeiro (Despesas e Receitas).
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Schema base para Financeiro
class FinanceiroBase(BaseModel):
    tipo: str = Field(..., max_length=20)  # 'receita' ou 'despesa'
    categoria: str = Field(..., max_length=50)
    valor: float = Field(..., gt=0)  # Valor deve ser maior que zero
    descricao: Optional[str] = None
    data: Optional[datetime] = None

# Schema para criação de transação financeira
class FinanceiroCreate(FinanceiroBase):
    pass

# Schema para atualização de transação financeira
class FinanceiroUpdate(BaseModel):
    tipo: Optional[str] = Field(None, max_length=20)
    categoria: Optional[str] = Field(None, max_length=50)
    valor: Optional[float] = Field(None, gt=0)
    descricao: Optional[str] = None
    data: Optional[datetime] = None

# Schema para leitura/retorno de transação financeira
class FinanceiroRead(FinanceiroBase):
    id: int
    responsavel_id: Optional[int] = None
    data: datetime

    class Config:
        orm_mode = True
