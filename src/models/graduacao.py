# src/models/graduacao.py
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from src.database import Base
from datetime import datetime

class Graduacao(Base):
    __tablename__ = 'graduacoes'

    id = Column(Integer, primary_key=True, index=True)
    aluno_id = Column(Integer, ForeignKey("alunos.id"), nullable=False)
    
    # Ex: "Faixa Branca", "Faixa Azul - 1º Grau", "Muay Thai - Ponta Vermelha"
    faixa = Column(String(100), nullable=False) 
    
    data_graduacao = Column(Date, default=datetime.utcnow().date)
    
    # Snapshot: Quantas aulas ele tinha no momento dessa graduação?
    aulas_acumuladas = Column(Integer, default=0) 
    
    observacao = Column(Text, nullable=True)

    # Relacionamento
    aluno = relationship("Aluno", back_populates="historico_graduacoes")