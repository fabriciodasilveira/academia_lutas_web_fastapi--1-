# src/models/inscricao.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from src.database import Base
from datetime import datetime

class Inscricao(Base):
    __tablename__ = 'inscricoes'

    id = Column(Integer, primary_key=True, index=True)
    aluno_id = Column(Integer, ForeignKey('alunos.id'), nullable=False)
    evento_id = Column(Integer, ForeignKey('eventos.id'), nullable=False)
    data_inscricao = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="pendente") # pendente, pago, cancelado
    metodo_pagamento = Column(String(50), nullable=True)
    valor_pago = Column(Float, nullable=True)

    aluno = relationship("Aluno", back_populates="inscricoes")
    evento = relationship("Evento", back_populates="inscricoes")