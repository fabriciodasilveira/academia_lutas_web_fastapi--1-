# -*- coding: utf-8 -*-
"""
Modelo SQLAlchemy para a entidade Turma.
"""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base # Importa a Base do novo arquivo database.py

# É importante garantir que os modelos relacionados (Usuario, Matricula) também
# sejam adaptados para SQLAlchemy puro se os relacionamentos forem mantidos.
# Se não forem adaptados agora, os relacionamentos devem ser comentados.

class Turma(Base):
    __tablename__ = 'turmas'

    id = Column(Integer, primary_key=True, index=True)
    modalidade = Column(String(50), nullable=False)  # Ex: 'Jiu-Jitsu', 'Judô', 'Muay Thai'
    horario = Column(String(50), nullable=False) # Ajustado tamanho para flexibilidade (ex: "19:00 - 20:30")
    dias_semana = Column(String(100), nullable=False) # Ajustado tamanho (ex: 'Segunda, Quarta, Sexta')
    professor_id = Column(Integer, ForeignKey('professores.id'), nullable=True) # Alterado para referenciar 'professores.id'
    nivel = Column(String(50), nullable=True)  # Ex: 'iniciante', 'intermediário', 'avançado'
    capacidade_maxima = Column(Integer, nullable=True)

    # Relacionamentos (Ajustar ou comentar se modelos relacionados não foram adaptados)
    # Assumindo que o modelo Professor foi adaptado e tem back_populates="turmas"
    professor = relationship("Professor") # , back_populates="turmas") # Adicionar back_populates se definido em Professor
    
    # Assumindo que o modelo Matricula será adaptado
    # matriculas = relationship("Matricula", back_populates="turma")

    # __init__ e to_dict() removidos.

