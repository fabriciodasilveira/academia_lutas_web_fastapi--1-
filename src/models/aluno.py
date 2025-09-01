# -*- coding: utf-8 -*-
"""
Modelo SQLAlchemy para a entidade Aluno.
"""
from sqlalchemy import Column, Integer, String, Date, DateTime
from sqlalchemy.orm import relationship
from src.database import Base
from datetime import datetime

class Aluno(Base):
    __tablename__ = "alunos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), index=True)
    data_nascimento = Column(Date)
    cpf = Column(String(14), unique=True, index=True)
    telefone = Column(String(20))
    email = Column(String(100), unique=True, index=True)
    endereco = Column(String(255))
    observacoes = Column(String(255))
    foto = Column(String(255))
    # Campo `data_cadastro` adicionado
    data_cadastro = Column(DateTime, default=datetime.utcnow)

    # Relacionamento com matrículas
    matriculas = relationship("Matricula", back_populates="aluno")

    # Relacionamento com mensalidades
    mensalidades = relationship("Mensalidade", back_populates="aluno")