# src/models/evento.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum # Adicione Enum
from sqlalchemy.orm import relationship # Adicione relationship
from src.database import Base

class Evento(Base):
    __tablename__ = "eventos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    tipo = Column(String(50)) # campeonato, seminário, etc.
    descricao = Column(String(255), nullable=True)
    local = Column(String(150))
    data_evento = Column(DateTime, nullable=False)
    data_fim = Column(DateTime, nullable=True)
    valor_inscricao = Column(Float, nullable=False, default=0.0)
    capacidade = Column(Integer, nullable=False, default=0)
    status = Column(String(50), default="Planejado") # Planejado, Ativo, Encerrado, Cancelado

    # Adicionar relacionamento com inscrições
    inscricoes = relationship("Inscricao", back_populates="evento", cascade="all, delete-orphan")