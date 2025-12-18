# -*- coding: utf-8 -*-
"""
Modelo SQLAlchemy para a entidade Financeiro.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base
from datetime import datetime
from src.models.usuario import Usuario # Garanta que importou Usuario

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
    
    beneficiario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True) # Quem recebeu o pagamento (Professor)
    valor_abatido_caixa = Column(Float, default=0.0) # Quanto foi usado do caixa virtual
    
    responsavel = relationship("Usuario", foreign_keys=[responsavel_id]) # Quem lançou (já existia, verifique o nome da FK no seu arquivo original)
    beneficiario = relationship("Usuario", foreign_keys=[beneficiario_id]) # Novo relacionamento