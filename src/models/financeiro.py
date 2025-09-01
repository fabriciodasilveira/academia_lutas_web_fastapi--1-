# -*- coding: utf-8 -*-
"""
Modelo SQLAlchemy para a entidade Financeiro.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime
from src.database import Base
from datetime import datetime

class Financeiro(Base):
    __tablename__ = 'financeiro'

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(20), nullable=False) # 'receita' ou 'despesa'
    categoria = Column(String(50), nullable=False)
    valor = Column(Float, nullable=False)
    descricao = Column(String(255), nullable=False)
    observacoes = Column(String(255), nullable=True)
    status = Column(String(50), nullable=True) # Ex: 'confirmado', 'pendente', 'cancelado'
    data = Column(DateTime, default=datetime.utcnow)
    forma_pagamento = Column(String(50), nullable=True) # Adicionado para os requisitos
    responsavel_id = Column(Integer, nullable=True)