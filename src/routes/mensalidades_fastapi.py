# -*- coding: utf-8 -*-
"""
Rotas FastAPI para o CRUD de Mensalidades.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from datetime import date, datetime

from src.database import get_db
from src.models.mensalidade import Mensalidade
from src.schemas.mensalidade import MensalidadeCreate, MensalidadeRead
from src.models.aluno import Aluno
from src.models.plano import Plano
from src.models.financeiro import Financeiro
from src.schemas.mensalidade import MensalidadePaginated


router = APIRouter(
    tags=["Mensalidades"],
    responses={404: {"description": "Não encontrado"}},
)

@router.post("", response_model=MensalidadeRead, status_code=status.HTTP_201_CREATED)
def create_mensalidade(mensalidade: MensalidadeCreate, db: Session = Depends(get_db)):
    db_aluno = db.query(Aluno).filter(Aluno.id == mensalidade.aluno_id).first()
    if not db_aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    
    db_plano = db.query(Plano).filter(Plano.id == mensalidade.plano_id).first()
    if not db_plano:
        raise HTTPException(status_code=404, detail="Plano não encontrado")

    db_mensalidade = Mensalidade(**mensalidade.dict())
    db.add(db_mensalidade)
    db.commit()
    db.refresh(db_mensalidade)
    return db_mensalidade

@router.get("", response_model=MensalidadePaginated) # Altera o response_model
def read_mensalidades(
    skip: int = 0,
    limit: int = 20, # Define um limite padrão menor para paginação
    status: Optional[str] = None,
    busca_aluno: Optional[str] = None, # Novo parâmetro de busca
    db: Session = Depends(get_db)
):
    """
    Lista mensalidades com filtros, busca por nome do aluno,
    ordenação por nome e paginação.
    """
    query = db.query(Mensalidade).options(
        joinedload(Mensalidade.aluno), # Garante que o aluno seja carregado
        joinedload(Mensalidade.plano)
    ).join(Aluno, Mensalidade.aluno_id == Aluno.id) # Faz o JOIN para poder buscar e ordenar

    if status:
        query = query.filter(Mensalidade.status == status)
    if busca_aluno:
        # Filtra pelo nome do aluno (case-insensitive)
        query = query.filter(Aluno.nome.ilike(f"%{busca_aluno}%"))

    # Conta o total ANTES de aplicar limit/offset
    total = query.count()

    # Ordena pelo nome do aluno e depois pela data de vencimento
    mensalidades_paginadas = query.order_by(Aluno.nome.asc(), Mensalidade.data_vencimento.desc())\
                                  .offset(skip).limit(limit).all()

    # Filtra mensalidades com aluno/plano None para evitar erro de validação (mantido)
    mensalidades_validas = [m for m in mensalidades_paginadas if m.aluno is not None and m.plano is not None]

    return {"total": total, "mensalidades": mensalidades_validas}

@router.delete("/{mensalidade_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mensalidade(mensalidade_id: int, db: Session = Depends(get_db)):
    db_mensalidade = db.query(Mensalidade).filter(Mensalidade.id == mensalidade_id).first()
    if db_mensalidade is None:
        raise HTTPException(status_code=404, detail="Mensalidade não encontrada")
    db.delete(db_mensalidade)
    db.commit()
    return None

@router.post("/processar_pagamento/{mensalidade_id}", response_model=MensalidadeRead)
def processar_pagamento_mensalidade(mensalidade_id: int, db: Session = Depends(get_db)):
    """
    Processa o pagamento manual de uma mensalidade e cria uma transação no financeiro.
    """
    db_mensalidade = db.query(Mensalidade).options(joinedload(Mensalidade.aluno)).filter(Mensalidade.id == mensalidade_id).first() # Carrega o aluno junto
    if not db_mensalidade:
        raise HTTPException(status_code=404, detail="Mensalidade não encontrada")
    if db_mensalidade.status == 'pago':
        raise HTTPException(status_code=400, detail="Esta mensalidade já foi paga.")

    # Atualiza a mensalidade
    db_mensalidade.status = 'pago'
    db_mensalidade.data_pagamento = date.today()

    # Cria a transação no financeiro
    if db_mensalidade.aluno: # Verifica se o aluno ainda existe
        descricao_transacao = f"Pagamento manual da mensalidade ID {db_mensalidade.id} do aluno {db_mensalidade.aluno.nome}"
    else:
        descricao_transacao = f"Pagamento manual da mensalidade ID {db_mensalidade.id} (Aluno ID {db_mensalidade.aluno_id})"

    nova_transacao = Financeiro(
        tipo="receita",
        categoria="Mensalidade",
        descricao=descricao_transacao,
        valor=db_mensalidade.valor,
        status="confirmado",
        data=datetime.utcnow()
    )
    db.add(nova_transacao)
    
    db.commit()
    db.refresh(db_mensalidade)
    
    return db_mensalidade