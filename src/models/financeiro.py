# src/models/financeiro.py
# -*- coding: utf-8 -*-
"""
Modelo SQLAlchemy para a entidade Financeiro.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from src.database import Base
from datetime import datetime

# Importante: Importar o modelo Usuario para o relacionamento funcionar, 
# mas usando string "Usuario" no relationship evitamos import circular
# (o SQLAlchemy resolve pelo nome da classe se todos herdarem da mesma Base)

class Financeiro(Base):
    __tablename__ = 'financeiro'

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(20), nullable=False) # 'receita' ou 'despesa'
    categoria = Column(String(50), nullable=False)
    valor = Column(Float, nullable=False)
    descricao = Column(String(255), nullable=False)
    
    # Alterei para Text para caber observações longas, mas String(255) também funciona
    observacoes = Column(Text, nullable=True) 
    
    status = Column(String(50), default='confirmado') # Ex: 'confirmado', 'pendente', 'cancelado'
    data = Column(DateTime, default=datetime.utcnow)
    forma_pagamento = Column(String(50), nullable=True)
    
    # --- COLUNAS DE RELACIONAMENTO (Chaves Estrangeiras) ---
    # Adicionamos ForeignKey para dizer ao banco que esse ID pertence a um Usuario
    responsavel_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    beneficiario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True) # Novo campo
    
    # Novo campo para o "Encontro de Contas"
    valor_abatido_caixa = Column(Float, default=0.0)

    # --- RELACIONAMENTOS ---
    # foreign_keys explica ao SQLAlchemy qual coluna usar para cada relação
    responsavel = relationship("Usuario", foreign_keys=[responsavel_id])
    beneficiario = relationship("Usuario", foreign_keys=[beneficiario_id])