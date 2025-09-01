# -*- coding: utf-8 -*-
"""
Modelo SQLAlchemy para a entidade Evento.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime
from src.database import Base
from datetime import datetime

class Evento(Base):
    __tablename__ = "eventos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(String(255), nullable=True)
    data_evento = Column(DateTime, nullable=False)
    valor_inscricao = Column(Float, nullable=False, default=0.0)
    capacidade = Column(Integer, nullable=False, default=0)