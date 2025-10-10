# src/schemas/evento.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from .inscricao import InscricaoRead # Import para aninhar inscrições

class EventoBase(BaseModel):
    nome: str = Field(..., max_length=100)
    tipo: Optional[str] = Field(None, max_length=50)
    descricao: Optional[str] = Field(None, max_length=255)
    local: Optional[str] = Field(None, max_length=150)
    data_evento: datetime
    data_fim: Optional[datetime] = None
    valor_inscricao: float = Field(0.0, ge=0)
    capacidade: int = Field(0, ge=0)
    status: Optional[str] = Field("Planejado", max_length=50)
    
class EventoCreate(EventoBase):
    pass

class EventoUpdate(BaseModel):
    nome: Optional[str] = Field(None, max_length=100)
    tipo: Optional[str] = Field(None, max_length=50)
    descricao: Optional[str] = Field(None, max_length=255)
    local: Optional[str] = Field(None, max_length=150)
    data_evento: Optional[datetime] = None
    data_fim: Optional[datetime] = None
    valor_inscricao: Optional[float] = Field(None, ge=0)
    capacidade: Optional[int] = Field(None, ge=0)
    status: Optional[str] = Field(None, max_length=50)

class EventoRead(EventoBase):
    id: int
    inscricoes: List[InscricaoRead] = []
    is_inscrito: bool = False

    class Config:
        from_attributes = True