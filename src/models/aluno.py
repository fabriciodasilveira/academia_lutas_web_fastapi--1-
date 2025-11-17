from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base
from datetime import datetime

class Aluno(Base):
    __tablename__ = "alunos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True, unique=True)    
    
    nome = Column(String(100), index=True)
    data_nascimento = Column(Date)
    cpf = Column(String(14), unique=True, index=True)
    telefone = Column(String(20))
    email = Column(String(100), unique=True, index=True, nullable=True)
    endereco = Column(String(255))
    observacoes = Column(String(255))
    foto = Column(String(255))
    data_cadastro = Column(DateTime, default=datetime.utcnow)
    
    nome_responsavel = Column(String(100), nullable=True)
    cpf_responsavel = Column(String(14), nullable=True)
    parentesco_responsavel = Column(String(50), nullable=True)
    telefone_responsavel = Column(String(20), nullable=True)
    email_responsavel = Column(String(100), nullable=True)

    # Relacionamentos existentes
    matriculas = relationship("Matricula", back_populates="aluno")
    mensalidades = relationship("Mensalidade", back_populates="aluno")
    inscricoes = relationship("Inscricao", back_populates="aluno")
    
    # Novo relacionamento
    usuario = relationship("Usuario", back_populates="aluno")