# -*- coding: utf-8 -*-
"""
Configuração do banco de dados SQLAlchemy para a aplicação FastAPI.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Usa variável de ambiente ou default para SQLite
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./database/academia.db")

# connect_args só é necessário para SQLite
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# Cria a engine SQLAlchemy
engine = create_engine(
    DATABASE_URL, connect_args=connect_args
)

# Cria uma SessionLocal class
# Cada instância de SessionLocal será uma sessão de banco de dados.
# A classe em si ainda não é uma sessão de banco de dados.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Cria uma Base class
# Usaremos isso depois para criar cada um dos modelos ou classes do banco de dados (os modelos ORM).
Base = declarative_base()

# Função para obter uma sessão do banco de dados (usada com Depends)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

