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
    
    # --- CORREÇÃO AQUI ---
    # Alterado de gt=0 (maior que 0) para ge=0 (maior ou igual a 0)
    # Isso permite registrar transações de valor R$ 0,00 (ex: eventos gratuitos)
    valor: float = Field(..., ge=0) 
    # ---------------------
    
    descricao: str = Field(..., max_length=255)
    observacoes: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, max_length=50)
    data: Optional[datetime] = None

# Schema para criação de transação financeira
class FinanceiroCreate(FinanceiroBase):
    pass

# Schema para atualização de transação financeira
class FinanceiroUpdate(BaseModel):
    tipo: Optional[str] = Field(None, max_length=20)
    categoria: Optional[str] = Field(None, max_length=50)
    
    # --- CORREÇÃO AQUI TAMBÉM ---
    valor: Optional[float] = Field(None, ge=0)
    # ----------------------------
    
    descricao: Optional[str] = Field(None, max_length=255)
    observacoes: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, max_length=50)
    data: Optional[datetime] = None

# Schema para leitura/retorno de transação financeira
class FinanceiroRead(FinanceiroBase):
    id: int
    responsavel_id: Optional[int] = None
    data: datetime

    class Config:
        from_attributes = True # Atualizado para Pydantic v2 (era orm_mode)