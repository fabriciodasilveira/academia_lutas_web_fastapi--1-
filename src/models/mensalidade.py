# src/models/mensalidade.py
from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base
from datetime import date

# Importa as classes relacionadas para usar nos relacionamentos
from src.models.aluno import Aluno
from src.models.plano import Plano
from src.models.matricula import Matricula

class Mensalidade(Base):
    __tablename__ = "mensalidades"

    id = Column(Integer, primary_key=True, index=True)
    aluno_id = Column(Integer, ForeignKey("alunos.id"), nullable=False)
    plano_id = Column(Integer, ForeignKey("planos.id"), nullable=False)
    valor = Column(Float, nullable=False)
    data_vencimento = Column(Date, nullable=False)
    data_pagamento = Column(Date, nullable=True)
    status = Column(String(50), default='pendente') # Ex: pendente, pago, atrasado
    matricula_id = Column(Integer, ForeignKey("matriculas.id"), nullable=True) # Coluna existe

    # --- RELACIONAMENTOS USANDO NOMES DAS CLASSES ---
    aluno = relationship(Aluno, back_populates="mensalidades")
    plano = relationship(Plano) # Plano não tem back_populates para mensalidades
    matricula = relationship(Matricula, back_populates="mensalidades", lazy="joined")
    # ------------------------------------------------

# # -*- coding: utf-8 -*-
# """
# Modelo SQLAlchemy para a entidade Mensalidade.
# """
# from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
# from sqlalchemy.orm import relationship
# from src.database import Base
# from datetime import date

# class Mensalidade(Base):
#     __tablename__ = 'mensalidades'

#     id = Column(Integer, primary_key=True, index=True)
#     aluno_id = Column(Integer, ForeignKey('alunos.id'), nullable=False)
#     plano_id = Column(Integer, ForeignKey('planos.id'), nullable=False)
#     valor = Column(Float, nullable=False)
#     data_vencimento = Column(Date, nullable=False)
#     data_pagamento = Column(Date, nullable=True)
#     status = Column(String(50), default="pendente") # 'pago', 'pendente', 'atrasado'
    
#     # Relacionamentos
#     aluno = relationship("Aluno", back_populates="mensalidades")
#     plano = relationship("Plano", back_populates="mensalidades")