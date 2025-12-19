# src/routes/financeiro_fastapi.py
# -*- coding: utf-8 -*-
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from datetime import datetime
from pydantic import BaseModel

from src.database import get_db
from src.models.financeiro import Financeiro
from src.schemas.financeiro import FinanceiroCreate, FinanceiroRead, FinanceiroUpdate
from src.models.mensalidade import Mensalidade
from src.models.usuario import Usuario

router = APIRouter(
    tags=["Financeiro"],
    responses={404: {"description": "Não encontrado"}},
)

# --- SCHEMA AUXILIAR PARA O DROPDOWN ---
class StaffSelect(BaseModel):
    id: int
    nome: str
    role: str

    class Config:
        orm_mode = True

# --- Endpoint para preencher o Dropdown ---
@router.get("/staff", response_model=List[StaffSelect])
def get_staff_users(db: Session = Depends(get_db)):
    """Retorna lista de usuários com perfil de staff."""
    staff = db.query(Usuario).filter(
        or_(
            func.lower(Usuario.role) == 'professor',
            func.lower(Usuario.role) == 'administrador',
            func.lower(Usuario.role) == 'gerente',
            func.lower(Usuario.role) == 'atendente'
        )
    ).order_by(Usuario.nome).all()
    return staff

# --- CRUD Endpoints --- 

@router.post("/transacoes", response_model=FinanceiroRead, status_code=status.HTTP_201_CREATED)
def create_transacao(transacao: FinanceiroCreate, db: Session = Depends(get_db)):
    if transacao.tipo not in ['receita', 'despesa']:
        raise HTTPException(status_code=400, detail="Tipo inválido.")
    if not transacao.data:
        transacao.data = datetime.utcnow()
    
    db_transacao = Financeiro(**transacao.dict())
    db.add(db_transacao)
    db.commit()
    db.refresh(db_transacao)
    return db_transacao

@router.get("/transacoes", response_model=List[FinanceiroRead])
def read_transacoes(skip: int = 0, limit: int = 100, tipo: Optional[str] = None, categoria: Optional[str] = None, busca: Optional[str] = None, data_inicio: Optional[str] = None, data_fim: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Financeiro)
    if tipo: query = query.filter(Financeiro.tipo == tipo)
    if categoria: query = query.filter(Financeiro.categoria == categoria)
    if busca: query = query.filter((Financeiro.descricao.ilike(f"%{busca}%")) | (Financeiro.observacoes.ilike(f"%{busca}%")))
    
    if data_inicio:
        try: query = query.filter(Financeiro.data >= datetime.strptime(data_inicio, "%Y-%m-%d"))
        except: pass
    if data_fim:
        try: query = query.filter(Financeiro.data <= datetime.strptime(data_fim, "%Y-%m-%d"))
        except: pass
    
    return query.order_by(Financeiro.data.desc()).offset(skip).limit(limit).all()

@router.get("/transacoes/{transacao_id}", response_model=FinanceiroRead)
def read_transacao(transacao_id: int, db: Session = Depends(get_db)):
    db_transacao = db.query(Financeiro).filter(Financeiro.id == transacao_id).first()
    if not db_transacao: raise HTTPException(status_code=404, detail="Não encontrado")
    return db_transacao

@router.put("/transacoes/{transacao_id}", response_model=FinanceiroRead)
def update_transacao(transacao_id: int, dados: FinanceiroUpdate, db: Session = Depends(get_db)):
    db_transacao = db.query(Financeiro).filter(Financeiro.id == transacao_id).first()
    if not db_transacao: raise HTTPException(status_code=404, detail="Não encontrado")
    
    for key, value in dados.dict(exclude_unset=True).items():
        setattr(db_transacao, key, value)
    
    db.commit()
    db.refresh(db_transacao)
    return db_transacao

@router.delete("/transacoes/{transacao_id}", status_code=204)
def delete_transacao(transacao_id: int, db: Session = Depends(get_db)):
    db_transacao = db.query(Financeiro).filter(Financeiro.id == transacao_id).first()
    if not db_transacao: raise HTTPException(status_code=404, detail="Não encontrado")
    db.delete(db_transacao)
    db.commit()

# --- CÁLCULO DE BALANÇO E CAIXA VIRTUAL ---
@router.get("/balanco", response_model=dict)
def get_balanco(data_inicio: Optional[str] = None, data_fim: Optional[str] = None, db: Session = Depends(get_db)):
    hoje = datetime.utcnow().date()
    primeiro_dia = hoje.replace(day=1)
    
    try:
        d_ini = datetime.strptime(data_inicio, "%Y-%m-%d").date() if data_inicio else primeiro_dia
        d_fim = datetime.strptime(data_fim, "%Y-%m-%d").date() if data_fim else hoje
    except:
        d_ini = primeiro_dia
        d_fim = hoje

    # Totais do Período (Mês atual ou selecionado)
    receitas = db.query(func.sum(Financeiro.valor)).filter(Financeiro.tipo == 'receita', func.date(Financeiro.data) >= d_ini, func.date(Financeiro.data) <= d_fim).scalar() or 0.0
    despesas = db.query(func.sum(Financeiro.valor)).filter(Financeiro.tipo == 'despesa', func.date(Financeiro.data) >= d_ini, func.date(Financeiro.data) <= d_fim).scalar() or 0.0
    total_trans = db.query(func.count(Financeiro.id)).filter(func.date(Financeiro.data) >= d_ini, func.date(Financeiro.data) <= d_fim).scalar() or 0
    pendentes = db.query(Mensalidade).filter(Mensalidade.status == 'pendente', Mensalidade.data_vencimento <= hoje).count()
    
    cats = db.query(Financeiro.categoria, func.sum(Financeiro.valor)).filter(Financeiro.tipo == 'despesa', func.date(Financeiro.data) >= d_ini, func.date(Financeiro.data) <= d_fim).group_by(Financeiro.categoria).all()
    grafico_data = {c: v for c, v in cats}

    # --- LÓGICA DO CAIXA VIRTUAL (BALDE ACUMULATIVO) ---
    # Nota: Removemos os filtros de data (d_ini, d_fim) para pegar o histórico completo
    
    # 1. Buscar a equipe para garantir que todos apareçam, mesmo com saldo 0
    equipe = db.query(Usuario).filter(
        or_(func.lower(Usuario.role) == 'professor', func.lower(Usuario.role) == 'administrador', func.lower(Usuario.role) == 'gerente')
    ).order_by(Usuario.nome).all()

    # 2. Total que entrou no caixa (Recebido em Dinheiro) - DESDE O INÍCIO
    entradas_query = db.query(Financeiro.responsavel_id, func.sum(Financeiro.valor)).filter(
        Financeiro.tipo == 'receita', 
        Financeiro.forma_pagamento == 'Dinheiro'
    ).group_by(Financeiro.responsavel_id).all()
    map_entradas = {uid: val for uid, val in entradas_query}

    # 3. Total que saiu do caixa (Abatido em Pagamentos) - DESDE O INÍCIO
    saidas_query = db.query(Financeiro.beneficiario_id, func.sum(Financeiro.valor_abatido_caixa)).filter(
        Financeiro.valor_abatido_caixa > 0
    ).group_by(Financeiro.beneficiario_id).all()
    map_saidas = {uid: val for uid, val in saidas_query}

    caixas = []
    total_caixas_virtuais = 0.0
    
    for membro in equipe:
        entrada = map_entradas.get(membro.id, 0.0)
        saida = map_saidas.get(membro.id, 0.0)
        saldo = (entrada or 0.0) - (saida or 0.0)
        
        # Adiciona na lista
        caixas.append({
            "id": membro.id,
            "nome": membro.nome,
            "total": saldo
        })
        total_caixas_virtuais += saldo

    return {
        "receitas": receitas, "despesas": despesas, "saldo": receitas - despesas,
        "total_transacoes": total_trans, "mensalidades_pendentes": pendentes,
        "graficos": {"categorias": grafico_data},
        "caixas_virtuais": caixas, "total_caixas_virtuais": total_caixas_virtuais
    }