# -*- coding: utf-8 -*-
"""
Modelo SQLAlchemy para a entidade Categoria Financeira.
"""
from sqlalchemy import Column, Integer, String, Boolean
from src.database import Base

class Categoria(Base):
    __tablename__ = 'categorias'

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(50), unique=True, index=True, nullable=False)
    tipo = Column(String(20), nullable=False)  # 'receita' ou 'despesa'
    ativa = Column(Boolean, default=True)