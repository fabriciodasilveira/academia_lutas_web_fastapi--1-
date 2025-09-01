# -*- coding: utf-8 -*-
"""
Schemas Pydantic para a entidade Produto.
"""

from pydantic import BaseModel, Field
from typing import Optional

# Schema base para Produto
class ProdutoBase(BaseModel):
    codigo: str = Field(..., max_length=50)
    nome: str = Field(..., max_length=100)
    descricao: Optional[str] = Field(None, max_length=255)
    preco_custo: float = Field(..., gt=0)
    preco_venda: float = Field(..., gt=0)
    quantidade_estoque: int = Field(..., ge=0)

# Schema para criação de Produto
class ProdutoCreate(ProdutoBase):
    pass

# Schema para atualização de Produto
class ProdutoUpdate(BaseModel):
    codigo: Optional[str] = Field(None, max_length=50)
    nome: Optional[str] = Field(None, max_length=100)
    descricao: Optional[str] = Field(None, max_length=255)
    preco_custo: Optional[float] = Field(None, gt=0)
    preco_venda: Optional[float] = Field(None, gt=0)
    quantidade_estoque: Optional[int] = Field(None, ge=0)

# Schema para leitura/retorno de Produto
class ProdutoRead(ProdutoBase):
    id: int

    class Config:
        orm_mode = True