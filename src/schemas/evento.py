# -*- coding: utf-8 -*-
"""
Schemas Pydantic para a entidade Evento.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Schema base para Evento
class EventoBase(BaseModel):
    nome: str = Field(..., max_length=100)
    descricao: Optional[str] = Field(None, max_length=255)
    data_evento: datetime
    valor_inscricao: float = Field(0.0, ge=0)
    capacidade: int = Field(..., ge=0)

# Schema para criação de Evento
class EventoCreate(EventoBase):
    pass

# Schema para atualização de Evento
class EventoUpdate(BaseModel):
    nome: Optional[str] = Field(None, max_length=100)
    descricao: Optional[str] = Field(None, max_length=255)
    data_evento: Optional[datetime] = None
    valor_inscricao: Optional[float] = Field(None, ge=0)
    capacidade: Optional[int] = Field(None, ge=0)

# Schema para leitura/retorno de Evento
class EventoRead(EventoBase):
    id: int

    class Config:
        orm_mode = True