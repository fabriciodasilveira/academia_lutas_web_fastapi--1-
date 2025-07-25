# -*- coding: utf-8 -*-
"""
Schemas Pydantic para as entidades Evento e Foto.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Schema base para Foto
class FotoBase(BaseModel):
    caminho_arquivo: str = Field(..., max_length=255)
    legenda: Optional[str] = Field(None, max_length=200)
    destaque: bool = False

# Schema para criação de Foto
class FotoCreate(FotoBase):
    evento_id: int

# Schema para leitura/retorno de Foto
class FotoRead(FotoBase):
    id: int
    evento_id: int
    data_upload: datetime

    class Config:
        orm_mode = True

# Schema para atualização de Foto
class FotoUpdate(BaseModel):
    legenda: Optional[str] = Field(None, max_length=200)
    destaque: Optional[bool] = None

# Schema base para Evento
class EventoBase(BaseModel):
    titulo: str = Field(..., max_length=100)
    descricao: Optional[str] = None
    data_evento: datetime
    local: Optional[str] = Field(None, max_length=100)
    modalidades: Optional[str] = Field(None, max_length=100)
    status: str = Field(default="agendado", max_length=20)

# Schema para criação de Evento
class EventoCreate(EventoBase):
    pass

# Schema para atualização de Evento
class EventoUpdate(BaseModel):
    titulo: Optional[str] = Field(None, max_length=100)
    descricao: Optional[str] = None
    data_evento: Optional[datetime] = None
    local: Optional[str] = Field(None, max_length=100)
    modalidades: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, max_length=20)

# Schema para leitura/retorno de Evento (com fotos)
class EventoRead(EventoBase):
    id: int
    data_criacao: datetime
    fotos: List[FotoRead] = []

    class Config:
        orm_mode = True
