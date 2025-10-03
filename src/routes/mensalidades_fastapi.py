# -*- coding: utf-8 -*-
"""
Rotas FastAPI para o CRUD de Mensalidades.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import date
from src.models.financeiro import Financeiro
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
    Processa o pagamento de uma mensalidade, atualizando o status, a data de pagamento
    e registrando a transação no financeiro.
    """
    db_mensalidade = db.query(Mensalidade).filter(Mensalidade.id == mensalidade_id).first()
    if db_mensalidade is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mensalidade não encontrada")

    if db_mensalidade.status == "pago":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mensalidade já está paga.")

    # Atualiza a mensalidade
    db_mensalidade.status = "pago"
    db_mensalidade.data_pagamento = date.today()

    # Cria a transação financeira correspondente
    transacao_financeira = Financeiro(
        tipo="receita",
        categoria="Mensalidade",
        descricao=f"Mensalidade de {db_mensalidade.aluno.nome} - Venc: {db_mensalidade.data_vencimento.strftime('%d/%m/%Y')}",
        valor=db_mensalidade.valor,
        status="confirmado",
        data=datetime.now()
    )
    db.add(transacao_financeira)
    
    db.commit()
    db.refresh(db_mensalidade)

    return db_mensalidade

@router.post("/gerar-mensalidades", status_code=status.HTTP_201_CREATED)
def gerar_mensalidades_do_mes(db: Session = Depends(get_db)):
    """
    Gera as mensalidades para todas as matrículas ativas que ainda não
    possuem mensalidade para o mês corrente.
    """
    hoje = date.today()
    primeiro_dia_mes = hoje.replace(day=1)
    
    # Busca todas as matrículas ativas
    matriculas_ativas = db.query(Matricula).filter(Matricula.ativa == True).all()
    
    mensalidades_criadas = 0
    for matricula in matriculas_ativas:
        # Verifica se já existe mensalidade para o mês atual
        mensalidade_existente = db.query(Mensalidade).filter(
            Mensalidade.aluno_id == matricula.aluno_id,
            Mensalidade.data_vencimento >= primeiro_dia_mes
        ).first()

        if not mensalidade_existente:
            # Busca o plano associado à matrícula para obter o valor
            plano = db.query(Plano).filter(Plano.id == matricula.plano_id).first()
            if plano:
                nova_mensalidade = Mensalidade(
                    aluno_id=matricula.aluno_id,
                    plano_id=matricula.plano_id,
                    valor=plano.valor,
                    data_vencimento=primeiro_dia_mes.replace(day=10), # Vencimento no dia 10
                    status="pendente"
                )
                db.add(nova_mensalidade)
                mensalidades_criadas += 1

    db.commit()
    
    return {"mensagem": f"{mensalidades_criadas} mensalidades geradas com sucesso."}
