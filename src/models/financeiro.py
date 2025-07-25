# -*- coding: utf-8 -*-
"""
Modelo SQLAlchemy para a entidade Financeiro (Despesas e Receitas).
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database import Base

class Financeiro(Base):
    __tablename__ = 'financeiro'

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(20), nullable=False)  # 'receita' ou 'despesa'
    categoria = Column(String(50), nullable=False)
    valor = Column(Float, nullable=False)
    descricao = Column(Text, nullable=True)
    data = Column(DateTime, default=datetime.utcnow)
    responsavel_id = Column(Integer, nullable=True)  # Referência ao usuário responsável

    # Relacionamentos podem ser adicionados se necessário
    # responsavel = relationship("Usuario", back_populates="transacoes")
