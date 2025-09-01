# -*- coding: utf-8 -*-
"""
Rotas FastAPI para o CRUD de Categorias Financeiras.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

from src.database import get_db
from src.models.categoria import Categoria
from src.schemas.categoria import CategoriaCreate, CategoriaRead

router = APIRouter(
    tags=["Categorias"],
    responses={404: {"description": "Categoria não encontrada"}},
)

@router.post("", response_model=CategoriaRead, status_code=status.HTTP_201_CREATED)
def create_categoria(categoria: CategoriaCreate, db: Session = Depends(get_db)):
    """
    Cria uma nova categoria financeira.
    """
    try:
        db_categoria = Categoria(**categoria.dict())
        db.add(db_categoria)
        db.commit()
        db.refresh(db_categoria)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Categoria com este nome já existe."
        )
    return db_categoria

@router.get("", response_model=List[CategoriaRead])
def read_categorias(
    tipo: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Lista categorias, opcionalmente filtradas por tipo.
    """
    query = db.query(Categoria)
    if tipo:
        query = query.filter(Categoria.tipo == tipo)
    return query.order_by(Categoria.nome).all()

# Outras rotas (PUT, DELETE) podem ser adicionadas conforme necessidade.