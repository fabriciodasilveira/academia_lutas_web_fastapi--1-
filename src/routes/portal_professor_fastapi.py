# src/routes/portal_professor_fastapi.py
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from src.database import get_db
from src import auth, models
from src.models.mensalidade import Mensalidade
from src.models.financeiro import Financeiro
from src.models.aluno import Aluno
from src.models.usuario import Usuario
from src.schemas.aluno import AlunoCreate
from src.routes.alunos_fastapi import create_aluno as core_create_aluno # Reutiliza lógica core

router = APIRouter(
    prefix="/api/v1/portal-professor",
    tags=["Portal Professor"]
)

# Dependência para garantir que é Staff (Professor ou Atendente)
async def get_current_staff(current_user: Usuario = Depends(auth.get_current_active_user)):
    if current_user.role not in ['administrador', 'gerente', 'atendente', 'professor']:
        raise HTTPException(status_code=403, detail="Acesso restrito a equipe.")
    return current_user

# --- 1. CADASTRAR ALUNO (Simplificado para o PWA) ---
# Vamos reutilizar a rota principal de alunos, mas criar um wrapper se necessário,
# ou o frontend pode chamar a rota /api/v1/alunos diretamente se o usuário tiver permissão.
# Vamos manter simples: O frontend chamará /api/v1/alunos diretamente.

# --- 2. FINANCEIRO: LISTAR MENSALIDADES PENDENTES ---
@router.get("/mensalidades-pendentes")
def list_mensalidades_pendentes(
    busca: str = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_staff)
):
    query = db.query(Mensalidade).options(
        joinedload(Mensalidade.aluno),
        joinedload(Mensalidade.plano)
    ).filter(Mensalidade.status == 'pendente')

    if busca:
        query = query.join(Aluno).filter(Aluno.nome.ilike(f"%{busca}%"))
    
    mensalidades = query.order_by(Mensalidade.data_vencimento).limit(50).all()
    return mensalidades

# --- 3. FINANCEIRO: RECEBER EM DINHEIRO (Caixa Virtual) ---
@router.post("/mensalidades/{id}/receber-dinheiro")
def receber_mensalidade_dinheiro(
    id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_staff)
):
    mensalidade = db.query(Mensalidade).filter(Mensalidade.id == id).first()
    if not mensalidade:
        raise HTTPException(status_code=404, detail="Mensalidade não encontrada")
    
    if mensalidade.status == 'pago':
        raise HTTPException(status_code=400, detail="Esta mensalidade já está paga.")

    # 1. Atualiza Mensalidade
    mensalidade.status = 'pago'
    mensalidade.data_pagamento = datetime.utcnow().date()

    # 2. Cria Transação Financeira (Receita)
    # IMPORTANTE: responsavel_id marca quem recebeu (Caixa Virtual do Professor)
    nova_transacao = Financeiro(
        tipo="receita",
        categoria="Mensalidade",
        descricao=f"Recebimento Manual (Portal): {mensalidade.aluno.nome} - Ref. Mensalidade #{mensalidade.id}",
        valor=mensalidade.valor,
        status="confirmado",
        data=datetime.utcnow(),
        forma_pagamento="Dinheiro",
        observacoes=f"Recebido via Portal do Professor por {current_user.nome}",
        responsavel_id=current_user.id 
    )
    
    db.add(nova_transacao)
    db.commit()
    
    return {"message": "Pagamento recebido com sucesso!", "valor": mensalidade.valor}