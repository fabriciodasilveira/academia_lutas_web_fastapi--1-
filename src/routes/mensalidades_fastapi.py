# -*- coding: utf-8 -*-
"""
Rotas FastAPI para o CRUD de Mensalidades.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import date
import logging

from src.database import get_db
from src.models.mensalidade import Mensalidade
from src.models.aluno import Aluno
from src.models.plano import Plano
from src.schemas.mensalidade import MensalidadeCreate, MensalidadeRead, MensalidadeUpdate

router = APIRouter(
    tags=["Mensalidades"],
    responses={404: {"description": "Mensalidade não encontrada"}},
)

# --- CRUD Endpoints --- 

@router.post("", response_model=MensalidadeRead, status_code=status.HTTP_201_CREATED)
def create_mensalidade(mensalidade: MensalidadeCreate, db: Session = Depends(get_db)):
    """
    Cria uma nova mensalidade.
    """
    db_aluno = db.query(Aluno).filter(Aluno.id == mensalidade.aluno_id).first()
    if not db_aluno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado")

    db_plano = db.query(Plano).filter(Plano.id == mensalidade.plano_id).first()
    if not db_plano:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plano não encontrado")

    db_mensalidade = Mensalidade(**mensalidade.dict())
    
    try:
        db.add(db_mensalidade)
        db.commit()
        db.refresh(db_mensalidade)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro de integridade ao criar a mensalidade."
        )

    return db_mensalidade

@router.get("", response_model=List[MensalidadeRead])
def read_mensalidades(
    skip: int = 0,
    limit: int = 100,
    aluno_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Lista mensalidades com filtros opcionais.
    """
    query = db.query(Mensalidade)
    if aluno_id:
        query = query.filter(Mensalidade.aluno_id == aluno_id)
    if status:
        query = query.filter(Mensalidade.status == status)
        
    mensalidades = query.order_by(Mensalidade.data_vencimento.desc()).offset(skip).limit(limit).all()
    return mensalidades

@router.get("/{mensalidade_id}", response_model=MensalidadeRead)
def read_mensalidade(mensalidade_id: int, db: Session = Depends(get_db)):
    """
    Obtém os detalhes de uma mensalidade específica pelo ID.
    """
    db_mensalidade = db.query(Mensalidade).filter(Mensalidade.id == mensalidade_id).first()
    if db_mensalidade is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mensalidade não encontrada")
    return db_mensalidade

@router.put("/{mensalidade_id}", response_model=MensalidadeRead)
def update_mensalidade(
    mensalidade_id: int,
    mensalidade_update: MensalidadeUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza os dados de uma mensalidade existente.
    """
    db_mensalidade = db.query(Mensalidade).filter(Mensalidade.id == mensalidade_id).first()
    if db_mensalidade is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mensalidade não encontrada")

    update_data = mensalidade_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_mensalidade, key, value)
    
    db.commit()
    db.refresh(db_mensalidade)
    return db_mensalidade

@router.delete("/{mensalidade_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mensalidade(mensalidade_id: int, db: Session = Depends(get_db)):
    """
    Exclui uma mensalidade.
    """
    db_mensalidade = db.query(Mensalidade).filter(Mensalidade.id == mensalidade_id).first()
    if db_mensalidade is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mensalidade não encontrada")

    db.delete(db_mensalidade)
    db.commit()
    return None

# Rotas de utilidade para o frontend
@router.post("/processar_pagamento/{mensalidade_id}", response_model=MensalidadeRead)
def processar_pagamento(mensalidade_id: int, db: Session = Depends(get_db)):
    """
    Processa o pagamento de uma mensalidade, atualizando o status e a data de pagamento.
    """
    db_mensalidade = db.query(Mensalidade).filter(Mensalidade.id == mensalidade_id).first()
    if db_mensalidade is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mensalidade não encontrada")

    if db_mensalidade.status == "pago":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mensalidade já está paga.")

    db_mensalidade.status = "pago"
    db_mensalidade.data_pagamento = date.today()
    db.commit()
    db.refresh(db_mensalidade)

    # TODO: Integrar com o módulo financeiro para registrar a receita.
    # Exemplo: criar_transacao(FinanceiroCreate(...))

    return db_mensalidade