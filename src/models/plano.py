# -*- coding: utf-8 -*-
"""
Modelo SQLAlchemy para a entidade Plano de Mensalidade.
"""
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from src.database import Base

class Plano(Base):
    __tablename__ = 'planos'

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False, unique=True)
    descricao = Column(String(255), nullable=True)
    valor = Column(Float, nullable=False)
    periodo_meses = Column(Integer, nullable=False)
    
    # Adicione esta linha para o relacionamento com Mensalidades
    mensalidades = relationship("Mensalidade", back_populates="plano")