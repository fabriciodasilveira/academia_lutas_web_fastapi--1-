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

# Se for PostgreSQL no Render, ajusta o prefixo se necessário
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configuração de argumentos de conexão
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Cria a engine SQLAlchemy com configurações de robustez (Pool Pre-Ping)
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    # pool_pre_ping=True: Verifica se a conexão está viva antes de usar (Evita o erro SSL connection closed)
    pool_pre_ping=True,
    # pool_recycle: Recicla conexões a cada hora para evitar timeouts do banco
    pool_recycle=3600
)

# Cria uma SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Cria uma Base class
Base = declarative_base()

# Função para obter uma sessão do banco de dados (usada com Depends)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()