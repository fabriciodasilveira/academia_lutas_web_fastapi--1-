# src/models/presenca.py
from sqlalchemy import Column, Integer, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base
from datetime import datetime

class Presenca(Base):
    __tablename__ = 'presencas'

    id = Column(Integer, primary_key=True, index=True)
    aluno_id = Column(Integer, ForeignKey("alunos.id"), nullable=False)
    turma_id = Column(Integer, ForeignKey("turmas.id"), nullable=False)
    data = Column(Date, default=datetime.utcnow().date, nullable=False)
    presente = Column(Boolean, default=True)

    # Relacionamentos
    aluno = relationship("Aluno")
    turma = relationship("Turma")