# src/models/matricula.py
from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database import Base

# Importa as classes relacionadas
from src.models.aluno import Aluno
from src.models.turma import Turma
from src.models.plano import Plano
# Evita importação circular, Mensalidade e Historico importam Matricula
# Usaremos strings nesses casos específicos ou ajustaremos depois se necessário
# from src.models.mensalidade import Mensalidade -> Removido por enquanto
# from src.models.historico_matricula import HistoricoMatricula -> Removido por enquanto

class Matricula(Base):
    __tablename__ = "matriculas"

    id = Column(Integer, primary_key=True, index=True)
    aluno_id = Column(Integer, ForeignKey("alunos.id"), nullable=False)
    turma_id = Column(Integer, ForeignKey("turmas.id"), nullable=False)
    plano_id = Column(Integer, ForeignKey("planos.id"), nullable=False)
    data_matricula = Column(DateTime, default=datetime.utcnow)
    ativa = Column(Boolean, default=True)

    # --- RELACIONAMENTOS USANDO NOMES DAS CLASSES (onde possível) ---
    aluno = relationship(Aluno, back_populates="matriculas")
    turma = relationship(Turma, back_populates="matriculas")
    plano = relationship(Plano) # Plano não tem back_populates para matriculas

    # Para evitar importação circular, mantemos strings aqui por enquanto
    mensalidades = relationship("Mensalidade", back_populates="matricula", cascade="all, delete-orphan")
    historico = relationship("HistoricoMatricula", back_populates="matricula", cascade="all, delete-orphan")
    # ---------------------------------------------------------------

# # Em src/models/matricula.py
# from sqlalchemy import Column, Integer, ForeignKey, Date, Boolean
# from sqlalchemy.orm import relationship
# from src.database import Base
# from datetime import date

# class Matricula(Base):
#     __tablename__ = 'matriculas'

#     id = Column(Integer, primary_key=True, index=True)
#     aluno_id = Column(Integer, ForeignKey('alunos.id'), nullable=False)
#     turma_id = Column(Integer, ForeignKey('turmas.id'), nullable=False)
#     plano_id = Column(Integer, ForeignKey('planos.id'), nullable=False)
#     data_matricula = Column(Date, default=date.today)
#     ativa = Column(Boolean, default=True)

#     # Relacionamentos
#     aluno = relationship("Aluno", back_populates="matriculas")
#     turma = relationship("Turma", back_populates="matriculas")
#     plano = relationship("Plano") 
    
#     historico = relationship("HistoricoMatricula", back_populates="matricula", cascade="all, delete-orphan")