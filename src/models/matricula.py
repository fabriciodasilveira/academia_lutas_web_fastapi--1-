# -*- coding: utf-8 -*-
"""
Modelo SQLAlchemy para a entidade Matrícula.
"""

from sqlalchemy import Column, Integer, ForeignKey, Date, Boolean
from sqlalchemy.orm import relationship
from src.database import Base
from datetime import date

class Matricula(Base):
    __tablename__ = 'matriculas'

    id = Column(Integer, primary_key=True, index=True)
    aluno_id = Column(Integer, ForeignKey('alunos.id'), nullable=False)
    turma_id = Column(Integer, ForeignKey('turmas.id'), nullable=False)
    data_matricula = Column(Date, default=date.today)
    ativa = Column(Boolean, default=True)

    # Relacionamentos
    aluno = relationship("Aluno", back_populates="matriculas")
    turma = relationship("Turma", back_populates="matriculas")