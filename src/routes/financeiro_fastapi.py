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
from sqlalchemy import func
from src.models.mensalidade import Mensalidade
from src.models.usuario import Usuario

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
    Obtém o balanço financeiro (receitas - despesas) em um período de forma otimizada,
    incluindo dados para gráficos.
    """
    hoje = datetime.utcnow().date()
    primeiro_dia_mes = hoje.replace(day=1)

    try:
        data_inicio_obj = datetime.strptime(data_inicio, "%Y-%m-%d").date() if data_inicio else primeiro_dia_mes
        data_fim_obj = datetime.strptime(data_fim, "%Y-%m-%d").date() if data_fim else hoje
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de data inválido. Use YYYY-MM-DD")

    # Cálculos otimizados para os totais
    query_receitas = db.query(func.sum(Financeiro.valor)).filter(
        Financeiro.tipo == 'receita',
        func.date(Financeiro.data) >= data_inicio_obj,
        func.date(Financeiro.data) <= data_fim_obj
    )
    total_receitas = query_receitas.scalar() or 0.0

    query_despesas = db.query(func.sum(Financeiro.valor)).filter(
        Financeiro.tipo == 'despesa',
        func.date(Financeiro.data) >= data_inicio_obj,
        func.date(Financeiro.data) <= data_fim_obj
    )
    total_despesas = query_despesas.scalar() or 0.0
    
    query_total_transacoes = db.query(func.count(Financeiro.id)).filter(
        func.date(Financeiro.data) >= data_inicio_obj,
        func.date(Financeiro.data) <= data_fim_obj
    )
    total_transacoes = query_total_transacoes.scalar() or 0

    mensalidades_pendentes = db.query(Mensalidade).filter(
        Mensalidade.status == 'pendente',
        Mensalidade.data_vencimento <= hoje
    ).count()

    # --- LÓGICA DO GRÁFICO REINSERIDA AQUI ---
    # Agrupa as despesas por categoria
    categorias_despesa_query = db.query(
        Financeiro.categoria, 
        func.sum(Financeiro.valor)
    ).filter(
        Financeiro.tipo == 'despesa',
        func.date(Financeiro.data) >= data_inicio_obj,
        func.date(Financeiro.data) <= data_fim_obj
    ).group_by(Financeiro.categoria).all()

    # Formata os dados para o gráfico
    categorias_data = {categoria: valor for categoria, valor in categorias_despesa_query}
    # --- FIM DA LÓGICA DO GRÁFICO ---

    # --- LÓGICA DO CAIXA VIRTUAL (NOVA) ---
    # Busca receitas em 'Dinheiro' agrupadas por responsável
    # Assume que a transação criada no portal do professor tem 'responsavel_id' e forma_pagamento='Dinheiro'
    
    query_caixas = db.query(
        Usuario.nome,
        func.sum(Financeiro.valor).label("total")
    ).join(
        Financeiro, Usuario.id == Financeiro.responsavel_id
    ).filter(
        Financeiro.tipo == 'receita',
        Financeiro.forma_pagamento == 'Dinheiro', # Filtra apenas dinheiro físico
        func.date(Financeiro.data) >= data_inicio_obj,
        func.date(Financeiro.data) <= data_fim_obj
    ).group_by(Usuario.id, Usuario.nome).all()

    # Formata para lista de dicionários e calcula total geral dos caixas
    lista_caixas = [{"nome": nome, "total": total or 0.0} for nome, total in query_caixas]
    total_caixas_virtuais = sum(item['total'] for item in lista_caixas)
    
    # --- FIM DA LÓGICA DO CAIXA VIRTUAL ---

    return {
        "receitas": total_receitas,
        "despesas": total_despesas,
        "saldo": total_receitas - total_despesas,
        "total_transacoes": total_transacoes,
        "mensalidades_pendentes": mensalidades_pendentes,
        "graficos": {
            "categorias": categorias_data
        },
        # Adicione os novos dados ao retorno
        "caixas_virtuais": lista_caixas,
        "total_caixas_virtuais": total_caixas_virtuais
    }