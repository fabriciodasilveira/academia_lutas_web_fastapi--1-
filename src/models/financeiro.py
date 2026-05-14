# src/models/financeiro.py
# -*- coding: utf-8 -*-
"""
Modelo SQLAlchemy para a entidade Financeiro.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from src.database import Base
from datetime import datetime

class Financeiro(Base):
    __tablename__ = 'financeiro'
    
    # --- CORREÇÃO PARA SQLALCHEMY 2.0 ---
    # Essa linha evita o erro "MappedAnnotationError" em modelos estilo legado
    __allow_unmapped__ = True
    # ------------------------------------

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(20), nullable=False) # 'receita' ou 'despesa'
    categoria = Column(String(50), nullable=False)
    valor = Column(Float, nullable=False)
    descricao = Column(String(255), nullable=False)
    
    observacoes = Column(Text, nullable=True) 
    
    status = Column(String(50), default='confirmado')
    data = Column(DateTime, default=datetime.utcnow)
    forma_pagamento = Column(String(50), nullable=True)
    
    # Certifique-se que aqui está usando '=' e não ':'
    comprovante_url = Column(String(500), nullable=True)
    
    # --- COLUNAS DE RELACIONAMENTO ---
    responsavel_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    beneficiario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    
    valor_abatido_caixa = Column(Float, default=0.0)

    # --- RELACIONAMENTOS ---
    responsavel = relationship("Usuario", foreign_keys=[responsavel_id])
    beneficiario = relationship("Usuario", foreign_keys=[beneficiario_id])