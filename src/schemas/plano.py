# -*- coding: utf-8 -*-
"""
Schemas Pydantic para a entidade Plano de Mensalidade.
"""

from pydantic import BaseModel, Field
from typing import Optional

# Schema base para Plano
class PlanoBase(BaseModel):
    nome: str = Field(..., max_length=100)
    descricao: Optional[str] = Field(None, max_length=255)
    valor: float = Field(..., gt=0)
    periodo_meses: int = Field(..., gt=0)

# Schema para criação de Plano
class PlanoCreate(PlanoBase):
    pass

# Schema para atualização de Plano
class PlanoUpdate(BaseModel):
    nome: Optional[str] = Field(None, max_length=100)
    descricao: Optional[str] = Field(None, max_length=255)
    valor: Optional[float] = Field(None, gt=0)
    periodo_meses: Optional[int] = Field(None, gt=0)

# Schema para leitura/retorno de Plano
class PlanoRead(PlanoBase):
    id: int

    class Config:
        orm_mode = True