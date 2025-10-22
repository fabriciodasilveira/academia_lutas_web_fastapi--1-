# src/models/mensalidade.py
from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base
from datetime import date

# REMOVE os imports diretos das classes Aluno, Plano, Matricula daqui

class Mensalidade(Base):
    __tablename__ = "mensalidades"

    id = Column(Integer, primary_key=True, index=True)
    aluno_id = Column(Integer, ForeignKey("alunos.id"), nullable=False)
    plano_id = Column(Integer, ForeignKey("planos.id"), nullable=False)
    valor = Column(Float, nullable=False)
    data_vencimento = Column(Date, nullable=False)
    data_pagamento = Column(Date, nullable=True)
    status = Column(String(50), default='pendente')
    matricula_id = Column(Integer, ForeignKey("matriculas.id"), nullable=True, index=True)

    # --- RELACIONAMENTOS USANDO STRINGS ---
    aluno = relationship("Aluno", back_populates="mensalidades") # Usa string "Aluno"
    plano = relationship("Plano") # Usa string "Plano" (já estava assim)
    matricula = relationship("Matricula", back_populates="mensalidades") # Usa string "Matricula"
    # ------------------------------------
    # ------------------------------------------------