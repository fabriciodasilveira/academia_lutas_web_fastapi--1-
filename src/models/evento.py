# -*- coding: utf-8 -*-
"""
Modelos SQLAlchemy para as entidades Evento e Foto.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database import Base # Importa a Base do novo arquivo database.py

# É importante garantir que o modelo Usuario seja adaptado se o relacionamento
# criado_por/criador for mantido.

class Evento(Base):
    __tablename__ = 'eventos'

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(100), nullable=False)
    descricao = Column(Text, nullable=True)
    data_evento = Column(DateTime, nullable=False)
    local = Column(String(100), nullable=True)
    modalidades = Column(String(100), nullable=True)  # Ex: 'Jiu-Jitsu,Judô,Muay Thai'
    status = Column(String(20), default='agendado', nullable=False) # 'agendado', 'concluido', 'cancelado'
    # criado_por = Column(Integer, ForeignKey('usuarios.id'), nullable=True) # Comentar se Usuario não for adaptado
    data_criacao = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    # criador = relationship("Usuario", back_populates="eventos_criados") # Comentar se Usuario não for adaptado
    fotos = relationship("Foto", back_populates="evento", cascade="all, delete-orphan", lazy="select") # Usar lazy='select' ou 'joined'

    # __init__ e to_dict() removidos.

class Foto(Base):
    __tablename__ = 'fotos'

    id = Column(Integer, primary_key=True, index=True)
    evento_id = Column(Integer, ForeignKey('eventos.id'), nullable=False)
    caminho_arquivo = Column(String(255), nullable=False)
    legenda = Column(String(200), nullable=True)
    data_upload = Column(DateTime, default=datetime.utcnow)
    destaque = Column(Boolean, default=False)

    # Relacionamento
    evento = relationship("Evento", back_populates="fotos")

    # __init__ e to_dict() removidos.

