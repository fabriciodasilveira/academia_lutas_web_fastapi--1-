# -*- coding: utf-8 -*-
"""
Modelo SQLAlchemy para a entidade Professor.
"""

from sqlalchemy import Column, Integer, String, Date, Text
from sqlalchemy.orm import relationship # Importar se houver relacionamentos (ex: com Turmas)
from src.database import Base # Importa a Base do novo arquivo database.py

class Professor(Base):
    __tablename__ = 'professores'

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    cpf = Column(String(14), unique=True, index=True, nullable=True)
    data_nascimento = Column(Date, nullable=True)
    telefone = Column(String(20), nullable=True)
    email = Column(String(100), unique=True, index=True, nullable=True)
    endereco = Column(String(200), nullable=True)
    especialidade = Column(String(100), nullable=True)  # Especialidade do professor
    formacao = Column(String(200), nullable=True)       # Formação acadêmica ou técnica
    data_contratacao = Column(Date, nullable=True)      # Data de contratação
    observacoes = Column(Text, nullable=True)
    foto = Column(String(255), nullable=True)       # Caminho para a foto do professor (alterado de foto_url)

    # Relacionamentos (Exemplo: se Professor pode lecionar várias Turmas)
    # turmas = relationship("Turma", back_populates="professor") # Ajustar nome da classe Turma e back_populates

    # __init__ e to_dict() removidos, Pydantic/SQLAlchemy cuidam disso.

