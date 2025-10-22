# src/models/aluno.py
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database import Base

# REMOVE os imports diretos das classes Inscricao, Mensalidade daqui

class Aluno(Base):
    __tablename__ = "alunos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), unique=True, index=True, nullable=True)
    nome = Column(String(100), nullable=False)
    data_nascimento = Column(Date, nullable=True)
    cpf = Column(String(14), unique=True, index=True, nullable=True)
    telefone = Column(String(20), nullable=True)
    email = Column(String(100), unique=True, index=True, nullable=True)
    endereco = Column(String(255), nullable=True)
    observacoes = Column(String(255), nullable=True)
    foto = Column(String(255), nullable=True)
    data_cadastro = Column(DateTime, default=datetime.utcnow)

    nome_responsavel = Column(String(100), nullable=True)
    cpf_responsavel = Column(String(14), nullable=True)
    parentesco_responsavel = Column(String(50), nullable=True)
    telefone_responsavel = Column(String(20), nullable=True)
    email_responsavel = Column(String(100), nullable=True)

    responsavel_aluno_id = Column(Integer, ForeignKey("alunos.id"), nullable=True, index=True)

    # --- RELACIONAMENTOS USANDO STRINGS ---
    responsavel = relationship("Aluno", remote_side=[id], back_populates="dependentes") # Auto-referência usa string
    dependentes = relationship("Aluno", back_populates="responsavel", lazy="dynamic") # Auto-referência usa string

    usuario = relationship("Usuario", back_populates="aluno", cascade="all, delete-orphan", single_parent=True) # Usa string "Usuario"
    matriculas = relationship("Matricula", back_populates="aluno", cascade="all, delete-orphan") # Usa string "Matricula"
    inscricoes = relationship("Inscricao", back_populates="aluno") # Usa string "Inscricao"
    mensalidades = relationship("Mensalidade", back_populates="aluno") # Usa string "Mensalidade"
    # ------------------------------------

# Não se esqueça de garantir que os back_populates correspondentes nos outros modelos
# também usem strings (ex: em Usuario: aluno = relationship("Aluno", ...))