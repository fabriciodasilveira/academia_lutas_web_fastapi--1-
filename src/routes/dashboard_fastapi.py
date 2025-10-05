# Em src/routes/dashboard_fastapi.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from collections import defaultdict

from src.database import get_db
from src.models.aluno import Aluno
from src.models.evento import Evento

router = APIRouter(
    tags=["Dashboard"],
    prefix="/dashboard"
)

@router.get("/atividades-recentes")
def get_atividades_recentes(db: Session = Depends(get_db)):
    """
    Retorna o número de novos alunos e eventos nos últimos 6 meses.
    """
    hoje = datetime.utcnow()
    seis_meses_atras = hoje - timedelta(days=180)

    # Dicionários para armazenar contagens por mês
    alunos_por_mes = defaultdict(int)
    eventos_por_mes = defaultdict(int)

    # Busca novos alunos nos últimos 6 meses
    alunos = db.query(Aluno.data_cadastro).filter(Aluno.data_cadastro >= seis_meses_atras).all()
    for aluno in alunos:
        # Extrai o ano e mês e formata como "Mês/Ano" (ex: "Jan/24")
        chave_mes = aluno.data_cadastro.strftime("%b/%y")
        alunos_por_mes[chave_mes] += 1

    # Busca novos eventos nos últimos 6 meses
    eventos = db.query(Evento.data_evento).filter(Evento.data_evento >= seis_meses_atras).all()
    for evento in eventos:
        chave_mes = evento.data_evento.strftime("%b/%y")
        eventos_por_mes[chave_mes] += 1
        
    # Gera os rótulos dos últimos 6 meses em ordem
    labels = [(hoje - timedelta(days=30*i)).strftime("%b/%y") for i in range(5, -1, -1)]
    
    # Monta os dados finais, garantindo que todos os meses tenham um valor (0 se não houver atividade)
    dados_alunos = [alunos_por_mes.get(label, 0) for label in labels]
    dados_eventos = [eventos_por_mes.get(label, 0) for label in labels]

    return {
        "labels": labels,
        "datasets": {
            "alunos": dados_alunos,
            "eventos": dados_eventos,
        }
    }