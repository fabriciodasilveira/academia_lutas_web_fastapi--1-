# -*- coding: utf-8 -*-
"""
Rotas FastAPI para o CRUD de Transações Financeiras.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import logging

from src.database import get_db
from src.models.financeiro import Financeiro
from src.schemas.financeiro import FinanceiroCreate, FinanceiroRead, FinanceiroUpdate
from src.models.categoria import Categoria 

router = APIRouter(
    tags=["Financeiro"],
    responses={404: {"description": "Não encontrado"}},
)

# --- CRUD Endpoints para Transações Financeiras --- 

@router.post("/transacoes", response_model=FinanceiroRead, status_code=status.HTTP_201_CREATED)
def create_transacao(transacao: FinanceiroCreate, db: Session = Depends(get_db)):
    """
    Cria uma nova transação financeira (receita ou despesa).
    """
    # Validação do tipo e categoria
    tipos_validos = ['receita', 'despesa']
    if transacao.tipo not in tipos_validos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo inválido. Use: receita ou despesa"
        )
    
    # Se a data não for fornecida, usa a data atual
    if not transacao.data:
        transacao.data = datetime.utcnow()
    
    db_transacao = Financeiro(**transacao.dict())
    
    db.add(db_transacao)
    db.commit()
    db.refresh(db_transacao)
    
    return db_transacao

@router.get("/transacoes", response_model=List[FinanceiroRead])
def read_transacoes(
    skip: int = 0,
    limit: int = 100,
    tipo: Optional[str] = None,
    categoria: Optional[str] = None,
    busca: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Lista transações financeiras com filtros opcionais.
    """
    query = db.query(Financeiro)
    
    if tipo:
        query = query.filter(Financeiro.tipo == tipo)
    if categoria:
        query = query.filter(Financeiro.categoria == categoria)
    if busca:
        query = query.filter(
            (Financeiro.descricao.ilike(f"%{busca}%")) |
            (Financeiro.observacoes.ilike(f"%{busca}%"))
        )
    
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, "%Y-%m-%d")
            query = query.filter(Financeiro.data >= data_inicio_obj)
        except ValueError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Formato de data_inicio inválido. Use YYYY-MM-DD")
    
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, "%Y-%m-%d")
            query = query.filter(Financeiro.data <= data_fim_obj)
        except ValueError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Formato de data_fim inválido. Use YYYY-MM-DD")
    
    transacoes = query.order_by(Financeiro.data.desc()).offset(skip).limit(limit).all()
    return transacoes

@router.get("/transacoes/{transacao_id}", response_model=FinanceiroRead)
def read_transacao(transacao_id: int, db: Session = Depends(get_db)):
    """
    Obtém os detalhes de uma transação financeira específica pelo ID.
    """
    db_transacao = db.query(Financeiro).filter(Financeiro.id == transacao_id).first()
    if db_transacao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Transação não encontrada")
    return db_transacao

@router.put("/transacoes/{transacao_id}", response_model=FinanceiroRead)
def update_transacao(transacao_id: int, transacao_update: FinanceiroUpdate, db: Session = Depends(get_db)):
    """
    Atualiza os dados de uma transação financeira existente.
    """
    db_transacao = db.query(Financeiro).filter(Financeiro.id == transacao_id).first()
    if db_transacao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Transação não encontrada")
    
    update_data = transacao_update.dict(exclude_unset=True)
    
    if "tipo" in update_data:
        tipos_validos = ['receita', 'despesa']
        if update_data["tipo"] not in tipos_validos:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Tipo inválido. Use: receita ou despesa")
    
    for key, value in update_data.items():
        setattr(db_transacao, key, value)
    
    db.commit()
    db.refresh(db_transacao)
    return db_transacao

@router.delete("/transacoes/{transacao_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transacao(transacao_id: int, db: Session = Depends(get_db)):
    """
    Exclui uma transação financeira.
    """
    db_transacao = db.query(Financeiro).filter(Financeiro.id == transacao_id).first()
    if db_transacao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Transação não encontrada")
    
    db.delete(db_transacao)
    db.commit()
    return None

@router.get("/balanco", response_model=dict)
def get_balanco(
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Obtém o balanço financeiro (receitas - despesas) em um período.
    """
    hoje = datetime.utcnow().date()
    primeiro_dia_mes = hoje.replace(day=1)

    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Formato de data inválido. Use YYYY-MM-DD")
    else:
        data_inicio_obj = primeiro_dia_mes

    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Formato de data inválido. Use YYYY-MM-DD")
    else:
        data_fim_obj = hoje

    # Calcula totais e obtém dados para gráficos
    receitas_query = db.query(Financeiro.valor).filter(
        Financeiro.tipo == 'receita',
        Financeiro.data >= data_inicio_obj,
        Financeiro.data <= data_fim_obj
    )
    receitas = sum(r[0] for r in receitas_query.all())

    despesas_query = db.query(Financeiro.valor).filter(
        Financeiro.tipo == 'despesa',
        Financeiro.data >= data_inicio_obj,
        Financeiro.data <= data_fim_obj
    )
    despesas = sum(d[0] for d in despesas_query.all())

    total_transacoes = db.query(Financeiro).filter(
        Financeiro.data >= data_inicio_obj,
        Financeiro.data <= data_fim_obj
    ).count()

    categorias_query = db.query(Financeiro.categoria, func.sum(Financeiro.valor)).filter(
        Financeiro.data >= data_inicio_obj,
        Financeiro.data <= data_fim_obj
    ).group_by(Financeiro.categoria).all()

    categorias_data = {}
    for cat, valor in categorias_query:
        categorias_data[cat] = valor

    return {
        "receitas": receitas,
        "despesas": despesas,
        "saldo": receitas - despesas,
        "total_transacoes": total_transacoes,
        "graficos": {
            "categorias": categorias_data
        }
    }