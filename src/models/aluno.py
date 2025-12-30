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
    email = Column(String(100), unique=False, index=True, nullable=True)
    endereco = Column(String(255))
    observacoes = Column(String(255))
    foto = Column(String(255))
    data_cadastro = Column(DateTime, default=datetime.utcnow)
    
    nome_responsavel = Column(String(100), nullable=True)
    cpf_responsavel = Column(String(14), nullable=True)
    parentesco_responsavel = Column(String(50), nullable=True)
    telefone_responsavel = Column(String(20), nullable=True)
    email_responsavel = Column(String(100), nullable=True)
    
    # Novos Campos de Graduação
    faixa_atual = Column(String(100), default="Faixa Branca")
    data_ultima_graduacao = Column(Date, default=datetime.utcnow().date)

    # Relacionamentos existentes
    matriculas = relationship("Matricula", back_populates="aluno")
    mensalidades = relationship("Mensalidade", back_populates="aluno")
    inscricoes = relationship("Inscricao", back_populates="aluno")
    historico_graduacoes = relationship("Graduacao", back_populates="aluno")    
    
    # Novo relacionamento
    usuario = relationship("Usuario", back_populates="aluno")