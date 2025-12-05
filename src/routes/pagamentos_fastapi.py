# Arquivo: src/routes/pagamentos_fastapi.py
# -*- coding: utf-8 -*-

import os
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import Optional
import re

from src.database import get_db
from src import auth
from src.models import usuario as models_usuario
from src.models.mensalidade import Mensalidade
from src.models.inscricao import Inscricao

# Importa a lógica do Mercado Pago
from src.routes import pagamentos_mercadopago

router = APIRouter(
    tags=["Pagamentos"],
)

# --- ROTA DE CONFIGURAÇÃO ---
@router.get("/config")
def get_payment_config():
    """
    Retorna a configuração de pagamento ativa.
    Como estamos usando apenas MP Pix, simplificamos o retorno.
    """
    return {
        "provider": "mercadopago",
        "mode": "pix_transparent"
    }

# --- ROTA PARA GERAR PIX (MENSALIDADE OU EVENTO) ---
@router.post("/pix/{item_type}/{item_id}")
def gerar_pix_transparente(
    item_type: str, 
    item_id: int, 
    db: Session = Depends(get_db), 
    current_user: models_usuario.Usuario = Depends(auth.get_current_active_user)
):
    """
    Gera um QR Code PIX direto para o item especificado.
    item_type: 'mensalidade' ou 'inscricao'
    """
    # Valida se o usuário tem perfil de aluno
    if not current_user.aluno:
         raise HTTPException(status_code=400, detail="Usuário não vinculado a um aluno.")
    
    # Limpa o CPF (remove pontos e traços) para enviar ao MP
    cpf_limpo = re.sub(r'[^0-9]', '', current_user.aluno.cpf or "")
    
    if not cpf_limpo:
        raise HTTPException(status_code=400, detail="O CPF é obrigatório para gerar o PIX. Atualize seu perfil.")

    # Chama a função de criação de PIX
    return pagamentos_mercadopago.create_pix_payment(
        db=db,
        item_id=item_id,
        item_type=item_type,
        payer_email=current_user.email,
        payer_first_name=current_user.nome.split()[0], # Pega o primeiro nome
        doc_number=cpf_limpo
    )

@router.get("/status/{item_type}/{item_id}")
def check_payment_status(
    item_type: str, 
    item_id: int, 
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(auth.get_current_active_user)
):
    """
    Verifica o status de um pagamento (usado pelo polling do frontend).
    """
    status_pagamento = "pendente"
    
    if item_type == "mensalidade":
        item = db.query(Mensalidade).filter(Mensalidade.id == item_id).first()
        if item:
            status_pagamento = item.status
            
    elif item_type == "inscricao":
        item = db.query(Inscricao).filter(Inscricao.id == item_id).first()
        if item:
            status_pagamento = item.status
    
    return {"status": status_pagamento}

# --- WEBHOOK (Para confirmar o pagamento automaticamente) ---
@router.post("/mercadopago/webhook")
async def mercadopago_webhook(request: Request, db: Session = Depends(get_db)):
    return await pagamentos_mercadopago.handle_mp_webhook(request, db)