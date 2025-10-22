# src/models/matricula.py
from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database import Base

# REMOVE os imports diretos das classes Aluno, Turma, Plano daqui

class Matricula(Base):
    __tablename__ = "matriculas"

    id = Column(Integer, primary_key=True, index=True)
    aluno_id = Column(Integer, ForeignKey("alunos.id"), nullable=False)
    turma_id = Column(Integer, ForeignKey("turmas.id"), nullable=False)
    plano_id = Column(Integer, ForeignKey("planos.id"), nullable=False)
    data_matricula = Column(DateTime, default=datetime.utcnow)
    ativa = Column(Boolean, default=True)

    # --- RELACIONAMENTOS USANDO STRINGS ---
    aluno = relationship("Aluno", back_populates="matriculas")
    turma = relationship("Turma", back_populates="matriculas")
    plano = relationship("Plano")

    mensalidades = relationship("Mensalidade", back_populates="matricula", cascade="all, delete-orphan")
    historico = relationship("HistoricoMatricula", back_populates="matricula", cascade="all, delete-orphan")
    # ------------------------------------