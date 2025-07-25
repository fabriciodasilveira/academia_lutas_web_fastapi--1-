# -*- coding: utf-8 -*-
"""
Modelo SQLAlchemy para a entidade Aluno.
"""

from sqlalchemy import Column, Integer, String, Date, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database import Base # Importa a Base do novo arquivo database.py

class Aluno(Base):
    __tablename__ = 'alunos'

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    data_nascimento = Column(Date, nullable=True)
    cpf = Column(String(14), unique=True, index=True, nullable=True)
    telefone = Column(String(20), nullable=True)
    email = Column(String(100), unique=True, index=True, nullable=True)
    endereco = Column(String(200), nullable=True)
    data_cadastro = Column(DateTime, default=datetime.utcnow)
    observacoes = Column(Text, nullable=True)
    foto = Column(String(255), nullable=True)  # Caminho para a foto do aluno

    # Relacionamentos (manter se Matricula for adaptada também)
    # A definição de Matricula precisa ser adaptada para SQLAlchemy puro também
    # matriculas = relationship('Matricula', back_populates='aluno')

    # O __init__ não é estritamente necessário com SQLAlchemy Base,
    # mas pode ser mantido se houver lógica específica na inicialização.
    # SQLAlchemy cuida da atribuição dos campos.

    # O método to_dict() será substituído pelo uso de schemas Pydantic para serialização.

