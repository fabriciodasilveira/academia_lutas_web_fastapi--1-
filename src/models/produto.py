# -*- coding: utf-8 -*-
"""
Modelo SQLAlchemy para a entidade Produto.
"""
from sqlalchemy import Column, Integer, String, Float
from src.database import Base

class Produto(Base):
    __tablename__ = 'produtos'

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), unique=True, index=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(String(255), nullable=True)
    preco_custo = Column(Float, nullable=False)
    preco_venda = Column(Float, nullable=False)
    quantidade_estoque = Column(Integer, default=0)