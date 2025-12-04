# Arquivo: src/routes/pagamentos_fastapi.py
# -*- coding: utf-8 -*-

import os
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import Optional

from src.database import get_db
from src import auth
from src.models import usuario as models_usuario

# Importa a lógica do Mercado Pago
from src.routes import pagamentos_mercadopago

# Cria o roteador sem prefixo duplicado (o prefixo já vem do main.py)
router = APIRouter(
    tags=["Pagamentos"],
)

# --- ROTA DE CONFIGURAÇÃO ---
@router.get("/config")
def get_payment_config():
    """
    Informa ao frontend que o provedor ativo é o Mercado Pago.
    """
    return {
        "provider": "mercadopago",
        "stripePublicKey": None 
    }

# --- ROTAS DE CHECKOUT PRO (Link de Pagamento) ---
# Úteis se você quiser manter a opção de boleto/cartão via redirecionamento

@router.post("/gerar/mensalidade/{mensalidade_id}")
def gerar_pagamento_mensalidade(mensalidade_id: int, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(auth.get_current_active_user)):
    return pagamentos_mercadopago.create_preference_mp(db, mensalidade_id, "mensalidade")

@router.post("/gerar/evento/{inscricao_id}")
def gerar_pagamento_evento(inscricao_id: int, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(auth.get_current_active_user)):
    return pagamentos_mercadopago.create_preference_mp(db, inscricao_id, "inscricao")

# --- NOVA ROTA DE PIX TRANSPARENTE (QR Code na Tela) ---

@router.post("/pix/{item_type}/{item_id}")
def gerar_pix_transparente(
    item_type: str, 
    item_id: int, 
    db: Session = Depends(get_db), 
    current_user: models_usuario.Usuario = Depends(auth.get_current_active_user)
):
    """
    Gera um QR Code PIX direto para o item especificado.
    """
    if not current_user.aluno:
         raise HTTPException(status_code=400, detail="Usuário não vinculado a um aluno.")
    
    # Limpa o CPF (remove pontos e traços)
    import re
    cpf_limpo = re.sub(r'[^0-9]', '', current_user.aluno.cpf or "")
    
    if not cpf_limpo:
        raise HTTPException(status_code=400, detail="CPF do aluno é obrigatório para gerar o PIX.")

    # Chama a função de PIX no arquivo de lógica
    return pagamentos_mercadopago.create_pix_payment(
        db=db,
        item_id=item_id,
        item_type=item_type,
        payer_email=current_user.email,
        payer_first_name=current_user.nome.split()[0], # Primeiro nome
        doc_number=cpf_limpo
    )

# --- WEBHOOK (Notificações do Mercado Pago) ---

@router.post("/mercadopago/webhook")
async def mercadopago_webhook(request: Request, db: Session = Depends(get_db)):
    return await pagamentos_mercadopago.handle_mp_webhook(request, db)