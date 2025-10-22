# src/models/aluno.py
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey # Adicione ForeignKey
from sqlalchemy.orm import relationship # Adicione relationship
from datetime import datetime
from src.database import Base
# Importe Inscricao para a relação (se já não estiver)
from src.models.inscricao import Inscricao
# Importe Mensalidade para a relação (se já não estiver)
from src.models.mensalidade import Mensalidade


class Aluno(Base):
    __tablename__ = "alunos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), unique=True, index=True, nullable=True) # Pode ser nulo para dependentes
    nome = Column(String(100), nullable=False)
    data_nascimento = Column(Date, nullable=True)
    cpf = Column(String(14), unique=True, index=True, nullable=True)
    telefone = Column(String(20), nullable=True)
    email = Column(String(100), unique=True, index=True, nullable=True) # Pode ser nulo para dependentes sem login
    endereco = Column(String(255), nullable=True)
    observacoes = Column(String(255), nullable=True)
    foto = Column(String(255), nullable=True)
    data_cadastro = Column(DateTime, default=datetime.utcnow)

    nome_responsavel = Column(String(100), nullable=True) # Responsável legal (menor)
    cpf_responsavel = Column(String(14), nullable=True)
    parentesco_responsavel = Column(String(50), nullable=True)
    telefone_responsavel = Column(String(20), nullable=True)
    email_responsavel = Column(String(100), nullable=True)

    # --- NOVOS CAMPOS E RELAÇÕES PARA CONTA FAMÍLIA ---
    responsavel_aluno_id = Column(Integer, ForeignKey("alunos.id"), nullable=True, index=True)

    # Relacionamento para buscar quem é o responsável por este aluno
    responsavel = relationship("Aluno", remote_side=[id], back_populates="dependentes")

    # Relacionamento para buscar quem são os dependentes deste aluno (se ele for o responsável)
    dependentes = relationship("Aluno", back_populates="responsavel", lazy="dynamic") # lazy='dynamic' para poder filtrar depois
    # --- FIM DAS NOVAS RELAÇÕES ---

    # Relações existentes
    usuario = relationship("Usuario", back_populates="aluno", cascade="all, delete-orphan", single_parent=True)
    matriculas = relationship("Matricula", back_populates="aluno", cascade="all, delete-orphan")
    inscricoes = relationship("Inscricao", back_populates="aluno") # Adicionado back_populates
    mensalidades = relationship("Mensalidade", back_populates="aluno") # Adicionado back_populates

# Adiciona o back_populates correspondente em Usuario, Inscricao, Mensalidade, Matricula se não existir
# Exemplo em src/models/usuario.py:
# aluno = relationship("Aluno", back_populates="usuario", uselist=False)