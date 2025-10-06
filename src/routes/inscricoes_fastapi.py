# src/routes/inscricoes_fastapi.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from src.database import get_db
from src.models.inscricao import Inscricao
from src.models.aluno import Aluno
from src.models.evento import Evento
from src.models.financeiro import Financeiro
from src.schemas.inscricao import InscricaoCreate, InscricaoRead
from datetime import datetime

router = APIRouter(
    tags=["Inscrições"],
)

@router.post("", response_model=InscricaoRead)
def create_inscricao(inscricao: InscricaoCreate, db: Session = Depends(get_db)):
    db_evento = db.query(Evento).filter(Evento.id == inscricao.evento_id).first()
    if not db_evento:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    
    db_aluno = db.query(Aluno).filter(Aluno.id == inscricao.aluno_id).first()
    if not db_aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    # Verifica se o evento está lotado
    if db_evento.capacidade > 0 and len(db_evento.inscricoes) >= db_evento.capacidade:
        raise HTTPException(status_code=400, detail="Evento lotado")

    # Cria a inscrição
    db_inscricao = Inscricao(**inscricao.dict())
    
    # Se o evento for gratuito, confirma a inscrição automaticamente
    if db_evento.valor_inscricao == 0:
        db_inscricao.status = "pago" # Usamos 'pago' para indicar confirmação
        db_inscricao.metodo_pagamento = "Gratuito"

    db.add(db_inscricao)
    db.commit()
    db.refresh(db_inscricao)
    return db_inscricao

@router.get("/evento/{evento_id}", response_model=List[InscricaoRead])
def read_inscricoes_por_evento(evento_id: int, db: Session = Depends(get_db)):
    inscricoes = db.query(Inscricao).options(joinedload(Inscricao.aluno)).filter(Inscricao.evento_id == evento_id).all()
    return inscricoes

@router.post("/{inscricao_id}/confirmar-pagamento-manual", response_model=InscricaoRead)
def confirmar_pagamento_manual(inscricao_id: int, db: Session = Depends(get_db)):
    db_inscricao = db.query(Inscricao).options(joinedload(Inscricao.evento), joinedload(Inscricao.aluno)).filter(Inscricao.id == inscricao_id).first()
    if not db_inscricao:
        raise HTTPException(status_code=404, detail="Inscrição não encontrada")

    if db_inscricao.status == 'pago':
        raise HTTPException(status_code=400, detail="Inscrição já foi paga")

    db_inscricao.status = "pago"
    db_inscricao.metodo_pagamento = "Manual"
    db_inscricao.valor_pago = db_inscricao.evento.valor_inscricao

    # Registra no financeiro
    transacao = Financeiro(
        tipo="receita",
        categoria="Evento",
        descricao=f"Inscrição: {db_inscricao.evento.nome} - Aluno: {db_inscricao.aluno.nome}",
        valor=db_inscricao.valor_pago,
        data=datetime.utcnow(),
        status="confirmado"
    )
    db.add(transacao)
    db.commit()
    db.refresh(db_inscricao)
    return db_inscricao