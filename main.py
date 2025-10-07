# main.py

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

# Importação de TODOS os modelos para que o SQLAlchemy os reconheça
from src.models import (
    aluno, professor, turma, evento, financeiro, matricula, 
    plano, mensalidade, produto, categoria, usuario, historico_matricula, inscricao
)

# Importação de TODOS os routers, incluindo os que faltavam
from src.routes import (
    alunos_fastapi, professores_fastapi, turmas_fastapi, 
    eventos_fastapi, financeiro_fastapi, matriculas_fastapi, 
    planos_fastapi, mensalidades_fastapi, produtos_fastapi, 
    categorias_fastapi, dashboard_fastapi, inscricoes_fastapi,
    auth_fastapi, usuarios_fastapi
)
from src.database import engine, Base
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename='app.log')

# Cria as tabelas no banco de dados
try:
    Base.metadata.create_all(bind=engine)
    print("Tabelas criadas com sucesso!")
except Exception as e:
    print(f"Erro ao criar tabelas: {e}")

app = FastAPI(
    title="API Academia de Lutas",
    description="API para gerenciamento de academia de lutas",
    version="1.0.0",
)

# Adiciona o middleware de sessão (CRUCIAL para o login com Google)
secret_key = os.environ.get("SECRET_KEY", "uma_chave_secreta_muito_forte_deve_ser_usada_aqui")
app.add_middleware(SessionMiddleware, secret_key=secret_key)

# Configuração de CORS
origins = ["http://localhost:5700"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montagem de TODOS os routers
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
app.include_router(dashboard_fastapi.router, prefix="/api/v1/dashboard")
app.include_router(inscricoes_fastapi.router, prefix="/api/v1/inscricoes")

# --- CORREÇÃO PRINCIPAL: REGISTAR AS ROTAS QUE FALTAVAM ---
app.include_router(auth_fastapi.router, prefix="/api/v1") 
app.include_router(usuarios_fastapi.router, prefix="/api/v1/usuarios")
# --- FIM DA CORREÇÃO ---

# Servir arquivos estáticos
static_dir = Path(__file__).parent / "src" / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def root():
    return {"mensagem": "API da Academia de Lutas está online"}