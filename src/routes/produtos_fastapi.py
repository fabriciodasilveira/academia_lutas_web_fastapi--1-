# -*- coding: utf-8 -*-
"""
Rotas FastAPI para o CRUD de Produtos.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

from src.database import get_db
from src.models.produto import Produto
from src.schemas.produto import ProdutoCreate, ProdutoRead, ProdutoUpdate

router = APIRouter(
    tags=["Produtos"],
    responses={404: {"description": "Produto não encontrado"}},
)

# --- CRUD Endpoints --- 

@router.post("", response_model=ProdutoRead, status_code=status.HTTP_201_CREATED)
def create_produto(produto: ProdutoCreate, db: Session = Depends(get_db)):
    """
    Cria um novo produto.
    """
    try:
        db_produto = Produto(**produto.dict())
        db.add(db_produto)
        db.commit()
        db.refresh(db_produto)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro ao criar produto. Verifique se o código já existe."
        )
    return db_produto

@router.get("", response_model=List[ProdutoRead])
def read_produtos(
    skip: int = 0,
    limit: int = 100,
    nome: Optional[str] = None,
    codigo: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Lista produtos com filtros opcionais.
    """
    query = db.query(Produto)
    if nome:
        query = query.filter(Produto.nome.ilike(f"%{nome}%"))
    if codigo:
        query = query.filter(Produto.codigo == codigo)
        
    produtos = query.order_by(Produto.nome).offset(skip).limit(limit).all()
    return produtos

@router.get("/{produto_id}", response_model=ProdutoRead)
def read_produto(produto_id: int, db: Session = Depends(get_db)):
    """
    Obtém os detalhes de um produto específico pelo ID.
    """
    db_produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if db_produto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")
    return db_produto

@router.put("/{produto_id}", response_model=ProdutoRead)
def update_produto(
    produto_id: int,
    produto_update: ProdutoUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza os dados de um produto existente.
    """
    db_produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if db_produto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")

    update_data = produto_update.dict(exclude_unset=True)
    
    try:
        for key, value in update_data.items():
            setattr(db_produto, key, value)
        db.commit()
        db.refresh(db_produto)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro de integridade ao atualizar. Verifique se o código já existe."
        )
        
    return db_produto

@router.delete("/{produto_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_produto(produto_id: int, db: Session = Depends(get_db)):
    """
    Exclui um produto.
    """
    db_produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if db_produto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")

    db.delete(db_produto)
    db.commit()
    return None