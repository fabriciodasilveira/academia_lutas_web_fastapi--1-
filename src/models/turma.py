# -*- coding: utf-8 -*-
"""
Modelo SQLAlchemy para a entidade Turma.
"""

from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base # Importa a Base do novo arquivo database.py

# É importante garantir que os modelos relacionados (Usuario, Matricula) também
# sejam adaptados para SQLAlchemy puro se os relacionamentos forem mantidos.
# Se não forem adaptados agora, os relacionamentos devem ser comentados.

class Turma(Base):
    __tablename__ = 'turmas'
    __table_args__ = {'extend_existing': True} # Adicionado para evitar erro de tabela já definida

    id = Column(Integer, primary_key=True, index=True)
    modalidade = Column(String(50), nullable=False)
    horario = Column(String(50), nullable=False)
    dias_semana = Column(String(100), nullable=False)
    professor_id = Column(Integer, ForeignKey('professores.id'), nullable=True)
    nivel = Column(String(50), nullable=True)
    capacidade_maxima = Column(Integer, nullable=True)
    
    # NOVOS CAMPOS ADICIONADOS PARA SINCRONIZAR COM O FRONTEND E O SCHEMA
    nome = Column(String(100), nullable=False)
    descricao = Column(String(255), nullable=True)
    observacoes = Column(String(255), nullable=True)
    valor_mensalidade = Column(Float, nullable=True)
    idade_minima = Column(Integer, nullable=True)
    ativa = Column(Boolean, default=True)

    # Relacionamentos (Ajustar ou comentar se modelos relacionados não foram adaptados)
    # Assumindo que o modelo Professor foi adaptado e tem back_populates="turmas"
    professor = relationship("Professor")
    
    matriculas = relationship("Matricula", back_populates="turma")

    
    
    # Assumindo que o modelo Matricula será adaptado
    # matriculas = relationship("Matricula", back_populates="turma")