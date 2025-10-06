# Em src/models/historico_matricula.py

from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Boolean
from sqlalchemy.orm import relationship
from src.database import Base
from datetime import datetime

class HistoricoMatricula(Base):
    __tablename__ = 'historico_matriculas'

    id = Column(Integer, primary_key=True, index=True)
    matricula_id = Column(Integer, ForeignKey('matriculas.id'), nullable=False)
    data_alteracao = Column(DateTime, default=datetime.utcnow)
    descricao = Column(String(255)) # Ex: "Matrícula trancada" ou "Matrícula ativada"

    matricula = relationship("Matricula", back_populates="historico")