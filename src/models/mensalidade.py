# -*- coding: utf-8 -*-
"""
Modelo SQLAlchemy para a entidade Mensalidade.
"""
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base
from datetime import date

class Mensalidade(Base):
    __tablename__ = 'mensalidades'

    id = Column(Integer, primary_key=True, index=True)
    aluno_id = Column(Integer, ForeignKey('alunos.id'), nullable=False)
    plano_id = Column(Integer, ForeignKey('planos.id'), nullable=False)
    valor = Column(Float, nullable=False)
    data_vencimento = Column(Date, nullable=False)
    data_pagamento = Column(Date, nullable=True)
    status = Column(String(50), default="pendente") # 'pago', 'pendente', 'atrasado'
    
    # Relacionamentos
    aluno = relationship("Aluno", back_populates="mensalidades")
    plano = relationship("Plano", back_populates="mensalidades")