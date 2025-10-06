
# -*- coding: utf-8 -*-
"""
Arquivo principal da aplicação FastAPI para o sistema de gerenciamento da academia.
"""

import os
from pathlib import Path
from fastapi import FastAPI, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Any, Dict, List
from src.routes import pagamentos_fastapi
from src.routes import dashboard_fastapi # Adicione dashboard_fastapi
from src.models import usuario
from src.routes import auth_fastapi,usuarios_fastapi



# Importação dos modelos para que o SQLAlchemy os reconheça
# Linhas CORRIGIDAS
from src.models import aluno, professor, turma, evento, financeiro, matricula, plano, mensalidade, produto, categoria, historico_matricula, inscricao

from src.routes import alunos_fastapi, professores_fastapi, turmas_fastapi, eventos_fastapi, financeiro_fastapi, matriculas_fastapi, planos_fastapi, mensalidades_fastapi, produtos_fastapi, categorias_fastapi, dashboard_fastapi, inscricoes_fastapi
from src.database import engine, Base


import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log'
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
app.include_router(alunos_fastapi.router, prefix="/api/v1/alunos")
app.include_router(professores_fastapi.router, prefix="/api/v1/professores")
app.include_router(turmas_fastapi.router, prefix="/api/v1/turmas")
app.include_router(eventos_fastapi.router, prefix="/api/v1/eventos")
app.include_router(financeiro_fastapi.router, prefix="/api/v1/financeiro")
app.include_router(matriculas_fastapi.router, prefix="/api/v1/matriculas")
app.include_router(planos_fastapi.router, prefix="/api/v1/planos")
app.include_router(mensalidades_fastapi.router, prefix="/api/v1/mensalidades")
app.include_router(produtos_fastapi.router, prefix="/api/v1/produtos")
app.include_router(categorias_fastapi.router, prefix="/api/v1/categorias")
app.include_router(pagamentos_fastapi.router, prefix="/api/v1")
app.include_router(dashboard_fastapi.router, prefix="/api/v1/dashboard")
app.include_router(dashboard_fastapi.router, prefix="/api/v1/dashboard")
app.include_router(inscricoes_fastapi.router, prefix="/api/v1/inscricoes")
app.include_router(auth_fastapi.router)
app.include_router(usuarios_fastapi.router)






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
            {"financeiro": "/api/v1/financeiro/transacoes"},
            {"matriculas": "/api/v1/matriculas"},
            {"planos": "/api/v1/planos"},
            {"mensalidades": "/api/v1/mensalidades"},
            {"produtos": "/api/v1/produtos"},
            {"categorias": "/api/v1/categorias"}
        ]
    }

