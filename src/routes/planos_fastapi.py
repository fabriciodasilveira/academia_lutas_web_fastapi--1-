# -*- coding: utf-8 -*-
"""
Rotas FastAPI para o CRUD de Planos.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

from src.database import get_db
from src.models.plano import Plano
from src.schemas.plano import PlanoCreate, PlanoRead, PlanoUpdate

router = APIRouter(
    tags=["Planos"],
    responses={404: {"description": "Plano não encontrado"}},
)

# --- CRUD Endpoints --- 

@router.post("", response_model=PlanoRead, status_code=status.HTTP_201_CREATED)
def create_plano(plano: PlanoCreate, db: Session = Depends(get_db)):
    """
    Cria um novo plano de mensalidade.
    """
    try:
        db_plano = Plano(**plano.dict())
        db.add(db_plano)
        db.commit()
        db.refresh(db_plano)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro ao criar plano. Verifique se o nome já existe."
        )
    return db_plano

@router.get("", response_model=List[PlanoRead])
def read_planos(
    skip: int = 0,
    limit: int = 100,
    nome: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Lista planos com filtros opcionais.
    """
    query = db.query(Plano)
    if nome:
        query = query.filter(Plano.nome.ilike(f"%{nome}%"))
        
    planos = query.order_by(Plano.valor).offset(skip).limit(limit).all()
    return planos

@router.get("/{plano_id}", response_model=PlanoRead)
def read_plano(plano_id: int, db: Session = Depends(get_db)):
    """
    Obtém os detalhes de um plano específico pelo ID.
    """
    db_plano = db.query(Plano).filter(Plano.id == plano_id).first()
    if db_plano is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plano não encontrado")
    return db_plano

@router.put("/{plano_id}", response_model=PlanoRead)
def update_plano(
    plano_id: int,
    plano_update: PlanoUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza os dados de um plano existente.
    """
    db_plano = db.query(Plano).filter(Plano.id == plano_id).first()
    if db_plano is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plano não encontrado")

    update_data = plano_update.dict(exclude_unset=True)
    
    try:
        for key, value in update_data.items():
            setattr(db_plano, key, value)
        db.commit()
        db.refresh(db_plano)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro de integridade ao atualizar. Verifique se o nome já existe."
        )
        
    return db_plano

@router.delete("/{plano_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plano(plano_id: int, db: Session = Depends(get_db)):
    """
    Exclui um plano.
    """
    db_plano = db.query(Plano).filter(Plano.id == plano_id).first()
    if db_plano is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plano não encontrado")

    db.delete(db_plano)
    db.commit()
    return None