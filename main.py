
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
from src.routes import dashboard_fastapi 
from src.models import usuario
from src.routes import auth_fastapi,usuarios_fastapi
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware 
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import create_first_user
from fastapi.responses import RedirectResponse # Adicione este import

from src.models import aluno, professor, turma, evento, financeiro, matricula, plano, mensalidade, produto, categoria, historico_matricula, inscricao

from src.routes import (alunos_fastapi, professores_fastapi, turmas_fastapi, eventos_fastapi, 
                        financeiro_fastapi, matriculas_fastapi, planos_fastapi, mensalidades_fastapi, 
                        produtos_fastapi, categorias_fastapi, 
                        dashboard_fastapi, inscricoes_fastapi,portal_aluno_fastapi,portal_professor_fastapi
)

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
    

env = os.getenv("ENVIRONMENT", "development")

docs_url = "/docs" if env != "production" else None
redoc_url = "/redoc" if env != "production" else None

# Inicializa a aplicação FastAPI
app = FastAPI(
    title="API Academia de Lutas",
    description="API para gerenciamento de academia de lutas",
    version="1.0.0",
    docs_url=docs_url,   # Será None em produção (desativa /docs)
    redoc_url=redoc_url, # Será None em produção (desativa /redoc)
    openapi_url="/openapi.json" if env != "production" else None # Desativa o JSON do schema
)

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5700")


# Configuração de CORS mais segura
origins = [
    frontend_url,
    "http://localhost:5700",
    "http://localhost",
    "http://localhost:8080",
    "http://127.0.0.1",
    "http://127.0.0.1:8080",
]

pwa_dir = Path(__file__).parent / "portal_aluno_pwa"
app.mount("/portal", StaticFiles(directory=pwa_dir), name="portal")

@app.get("/", tags=["Root"], include_in_schema=False)
async def root():
    # Se alguém acessar a raiz da API, joga para o portal do aluno
    return RedirectResponse(url="/portal")

# Rota principal para servir o index.html do PWA
@app.get("/portal/{rest_of_path:path}")
async def serve_pwa(rest_of_path: str):
    return FileResponse(pwa_dir / "index.html")

# Rota raiz do PWA
@app.get("/portal")
async def serve_pwa_root():
    return FileResponse(pwa_dir / "index.html")


app.add_middleware(SessionMiddleware, secret_key="SUA_SECRET_KEY_AQUI_DEVE_SER_A_MESMA_DO_AUTH.PY")

# Configuração de CORS (já existente)
app.add_middleware(
    CORSMiddleware,
    # ... (configurações do CORS)
)

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
app.include_router(pagamentos_fastapi.router, prefix="/api/v1/pagamentos")
app.include_router(dashboard_fastapi.router, prefix="/api/v1/dashboard")
app.include_router(dashboard_fastapi.router, prefix="/api/v1/dashboard")
app.include_router(inscricoes_fastapi.router, prefix="/api/v1/inscricoes")
app.include_router(auth_fastapi.router)
app.include_router(usuarios_fastapi.router)
app.include_router(portal_aluno_fastapi.router)
app.include_router(portal_professor_fastapi.router)



create_first_user.create_first_user()




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

