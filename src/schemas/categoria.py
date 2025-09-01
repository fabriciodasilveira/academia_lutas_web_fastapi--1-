# -*- coding: utf-8 -*-
"""
Schemas Pydantic para a entidade Categoria Financeira.
"""
from pydantic import BaseModel, Field
from typing import Optional

class CategoriaBase(BaseModel):
    nome: str = Field(..., max_length=50)
    tipo: str = Field(..., max_length=20)  # 'receita' ou 'despesa'
    ativa: Optional[bool] = True

class CategoriaCreate(CategoriaBase):
    pass

class CategoriaRead(CategoriaBase):
    id: int

    class Config:
        orm_mode = True