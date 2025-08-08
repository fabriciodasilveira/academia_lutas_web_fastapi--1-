# -*- coding: utf-8 -*-
"""
Rotas FastAPI para o CRUD de Despesas (Transações Financeiras).
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from src.database import get_db
from src.models.financeiro import Financeiro
from src.schemas.financeiro import FinanceiroCreate, FinanceiroRead, FinanceiroUpdate

router = APIRouter(
    prefix="/api/v1/financeiro",
    tags=["Financeiro"],
    responses={404: {"description": "Não encontrado"}},
)

# --- CRUD Endpoints para Transações Financeiras --- 

@router.post("/transacoes", response_model=FinanceiroRead, status_code=status.HTTP_201_CREATED)
def create_transacao(transacao: FinanceiroCreate, db: Session = Depends(get_db)):
    """
    Cria uma nova transação financeira (receita ou despesa).
    """
    # Validação do tipo
    tipos_validos = ['receita', 'despesa']
    if transacao.tipo not in tipos_validos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo inválido. Use: receita ou despesa"
        )
    
    # Se a data não for fornecida, usa a data atual
    if not transacao.data:
        transacao.data = datetime.utcnow()
    
    # Cria a transação
    db_transacao = Financeiro(**transacao.dict())
    
    # Responsável seria definido com base no usuário autenticado
    # Por enquanto, deixamos como null ou poderia ser um valor fixo para testes
    # db_transacao.responsavel_id = 1  # ID fixo para testes
    
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
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Lista transações financeiras com filtros opcionais.
    """
    query = db.query(Financeiro)
    
    # Aplica filtros se fornecidos
    if tipo:
        query = query.filter(Financeiro.tipo == tipo)
    if categoria:
        query = query.filter(Financeiro.categoria == categoria)
    
    # Filtra por período
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, "%Y-%m-%d")
            query = query.filter(Financeiro.data >= data_inicio_obj)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de data_inicio inválido. Use YYYY-MM-DD"
            )
    
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, "%Y-%m-%d")
            query = query.filter(Financeiro.data <= data_fim_obj)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de data_fim inválido. Use YYYY-MM-DD"
            )
    
    transacoes = query.order_by(Financeiro.data.desc()).offset(skip).limit(limit).all()
    return transacoes

@router.get("/transacoes/{transacao_id}", response_model=FinanceiroRead)
def read_transacao(transacao_id: int, db: Session = Depends(get_db)):
    """
    Obtém os detalhes de uma transação financeira específica pelo ID.
    """
    db_transacao = db.query(Financeiro).filter(Financeiro.id == transacao_id).first()
    if db_transacao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transação não encontrada"
        )
    return db_transacao

@router.put("/transacoes/{transacao_id}", response_model=FinanceiroRead)
def update_transacao(
    transacao_id: int,
    transacao_update: FinanceiroUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza os dados de uma transação financeira existente.
    """
    db_transacao = db.query(Financeiro).filter(Financeiro.id == transacao_id).first()
    if db_transacao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transação não encontrada"
        )
    
    update_data = transacao_update.dict(exclude_unset=True)
    
    # Validação do tipo se for atualizado
    if "tipo" in update_data:
        tipos_validos = ['receita', 'despesa']
        if update_data["tipo"] not in tipos_validos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo inválido. Use: receita ou despesa"
            )
    
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transação não encontrada"
        )
    
    db.delete(db_transacao)
    db.commit()
    
    return None

@router.get("/despesas", response_model=List[FinanceiroRead])
def read_despesas(
    skip: int = 0,
    limit: int = 100,
    categoria: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Lista apenas as despesas com filtros opcionais.
    Endpoint específico para despesas, que são transações do tipo 'despesa'.
    """
    query = db.query(Financeiro).filter(Financeiro.tipo == 'despesa')
    
    # Aplica filtros adicionais se fornecidos
    if categoria:
        query = query.filter(Financeiro.categoria == categoria)
    
    # Filtra por período
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, "%Y-%m-%d")
            query = query.filter(Financeiro.data >= data_inicio_obj)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de data_inicio inválido. Use YYYY-MM-DD"
            )
    
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, "%Y-%m-%d")
            query = query.filter(Financeiro.data <= data_fim_obj)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de data_fim inválido. Use YYYY-MM-DD"
            )
    
    despesas = query.order_by(Financeiro.data.desc()).offset(skip).limit(limit).all()
    return despesas

@router.get("/balanco", response_model=dict)
def get_balanco(
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Obtém o balanço financeiro (receitas - despesas) em um período.
    """
    # Datas padrão: mês atual
    if not data_inicio:
        data_inicio = datetime.utcnow().replace(day=1).strftime("%Y-%m-%d")
    if not data_fim:
        data_fim = datetime.utcnow().strftime("%Y-%m-%d")
    
    try:
        data_inicio_obj = datetime.strptime(data_inicio, "%Y-%m-%d")
        data_fim_obj = datetime.strptime(data_fim, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de data inválido. Use YYYY-MM-DD"
        )
    
    # Calcula total de receitas
    receitas_query = db.query(Financeiro).filter(
        Financeiro.tipo == 'receita',
        Financeiro.data >= data_inicio_obj,
        Financeiro.data <= data_fim_obj
    )
    receitas = sum(t.valor for t in receitas_query.all())
    
    # Calcula total de despesas
    despesas_query = db.query(Financeiro).filter(
        Financeiro.tipo == 'despesa',
        Financeiro.data >= data_inicio_obj,
        Financeiro.data <= data_fim_obj
    )
    despesas = sum(t.valor for t in despesas_query.all())
    
    # Calcula balanço
    balanco = receitas - despesas
    
    # Obtém detalhes por categoria
    # Para receitas
    categorias_receita = {}
    for transacao in receitas_query.all():
        if transacao.categoria not in categorias_receita:
            categorias_receita[transacao.categoria] = 0
        categorias_receita[transacao.categoria] += transacao.valor
    
    # Para despesas
    categorias_despesa = {}
    for transacao in despesas_query.all():
        if transacao.categoria not in categorias_despesa:
            categorias_despesa[transacao.categoria] = 0
        categorias_despesa[transacao.categoria] += transacao.valor
    
    return {
        "periodo": {
            "data_inicio": data_inicio,
            "data_fim": data_fim
        },
        "receitas": receitas,
        "despesas": despesas,
        "balanco": balanco,
        "detalhes": {
            "receitas": categorias_receita,
            "despesas": categorias_despesa
        }
    }
