# src/models/conteudo.py
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base
from datetime import datetime

class Conteudo(Base):
    __tablename__ = 'conteudos'

    id = Column(Integer, primary_key=True, index=True)
    
    # Organização do Método
    modulo = Column(String(50), default="Jiu-Jitsu Básico") # Ex: Básico, Avançado, Nogi
    semana = Column(Integer, nullable=False) # 1, 2, 3...
    ordem = Column(Integer, nullable=False, default=1) # 1º vídeo da semana, 2º vídeo...
    
    # O Conteúdo
    titulo = Column(String(100), nullable=False)
    descricao = Column(Text, nullable=True)
    video_url = Column(String(500), nullable=False) # Link do YouTube
    thumbnail_url = Column(String(500), nullable=True) # Capa (Opcional)
    
    # Controle
    ativo = Column(Boolean, default=True)
    data_criacao = Column(DateTime, default=datetime.utcnow)
    
    # Quem postou
    autor_id = Column(Integer, ForeignKey("usuarios.id"))

    # Relacionamentos
    autor = relationship("Usuario")