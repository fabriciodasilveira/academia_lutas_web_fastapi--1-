# -*- coding: utf-8 -*-
"""
Arquivo principal da aplicação FastAPI para o sistema de gerenciamento da academia.
"""

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Importação dos routers
from src.routes import alunos_fastapi, professores_fastapi, turmas_fastapi, eventos_fastapi, financeiro_fastapi
from src.database import engine, Base


import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log'  # Nome do arquivo de log
)

# Cria as tabelas no banco de dados com tratamento de erros
try:
    Base.metadata.create_all(bind=engine)
    print("Tabelas criadas com sucesso!")
except Exception as e:
    print(f"Erro ao criar tabelas: {e}")

# Inicializa a aplicação FastAPI
app = FastAPI(
    title="API Academia de Lutas",
    description="API para gerenciamento de academia de lutas",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuração de CORS mais segura
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://127.0.0.1",
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montagem dos routers
app.include_router(alunos_fastapi.router, prefix="/api/v1")
app.include_router(professores_fastapi.router, prefix="/api/v1")
app.include_router(turmas_fastapi.router, prefix="/api/v1")
app.include_router(eventos_fastapi.router, prefix="/api/v1")
app.include_router(financeiro_fastapi.router, prefix="/api/v1")

# Servir arquivos estáticos
static_dir = Path(__file__).parent / "src" / "static"
try:
    static_dir.mkdir(exist_ok=True)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
except Exception as e:
    print(f"Erro ao configurar arquivos estáticos: {e}")

@app.get("/", tags=["Root"])
async def root():
    return {
        "mensagem": "API Academia de Lutas - Sistema de Gerenciamento",
        "documentacao": "/docs",
        "endpoints": [
            {"alunos": "/api/v1/alunos"},
            {"professores": "/api/v1/professores"},
            {"turmas": "/api/v1/turmas"},
            {"eventos": "/api/v1/eventos"},
            {"financeiro": "/api/v1/financeiro/transacoes"}
        ]
    }