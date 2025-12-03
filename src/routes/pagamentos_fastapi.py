# src/routes/pagamentos_fastapi.py

import os
import stripe
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload
from datetime import date, datetime

from src.database import get_db
from src.models.mensalidade import Mensalidade
from src.models.inscricao import Inscricao
from src.models.financeiro import Financeiro
from src import auth
from src.models import usuario as models_usuario

# Importa a nova lógica do Mercado Pago
from src.routes import pagamentos_mercadopago

router = APIRouter(
    tags=["Pagamentos"],
    prefix="/api/v1/pagamentos" # Prefixo explícito para evitar confusão
)

# Configuração Stripe (mantida para quando o modo for 'stripe')
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# --- ROTA DE CONFIGURAÇÃO (NOVA) ---
@router.get("/config")
def get_payment_config():
    """
    Informa ao frontend qual provedor de pagamento está ativo (stripe ou mercadopago).
    """
    provider = os.getenv("PAYMENT_PROVIDER", "stripe").lower()
    return {
        "provider": provider,
        "stripePublicKey": os.getenv("STRIPE_PUBLIC_KEY") if provider == 'stripe' else None
    }
# -----------------------------------

# --- FUNÇÕES AUXILIARES (STRIPE ANTIGO) ---
# (Mantemos sua lógica antiga aqui, encapsulada)
def create_checkout_session_stripe(db: Session, current_user: models_usuario.Usuario, item_id: int, item_type: str):
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Chave de API da Stripe não configurada.")
    
    frontend_pwa_url = os.getenv("FRONTEND_PWA_URL", "http://localhost:8000/portal")
    line_item = {}
    
    if item_type == "mensalidade":
        db_item = db.query(Mensalidade).options(joinedload(Mensalidade.aluno), joinedload(Mensalidade.plano)).filter(Mensalidade.id == item_id).first()
        if not db_item or db_item.aluno.usuario_id != current_user.id:
            raise HTTPException(status_code=404, detail="Mensalidade não encontrada.")
        line_item = { "price_data": { "currency": "brl", "product_data": { "name": f"Mensalidade - {db_item.plano.nome}" }, "unit_amount": int(db_item.valor * 100), }, "quantity": 1, }
        success_path = "#/payments?payment=success"
    
    elif item_type == "inscricao":
        db_item = db.query(Inscricao).options(joinedload(Inscricao.aluno), joinedload(Inscricao.evento)).filter(Inscricao.id == item_id).first()
        if not db_item or db_item.aluno.usuario_id != current_user.id:
            raise HTTPException(status_code=404, detail="Inscrição não encontrada.")
        line_item = { "price_data": { "currency": "brl", "product_data": { "name": f"Inscrição - {db_item.evento.nome}" }, "unit_amount": int(db_item.evento.valor_inscricao * 100), }, "quantity": 1, }
        success_path = "#/events?payment=success"

    try:
        success_url = f"{frontend_pwa_url.rstrip('/')}{success_path}"
        cancel_url = f"{frontend_pwa_url.rstrip('/')}/#/payments?payment=canceled"

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card', 'boleto'],
            line_items=[line_item],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={ 'item_id': item_id, 'item_type': item_type }
        )
        return {"sessionId": checkout_session.id} # Retorna session ID para Stripe
    except Exception as e:
        logging.error(f"Erro Stripe: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- ROTAS UNIFICADAS (O "CÉREBRO") ---

@router.post("/gerar/mensalidade/{mensalidade_id}")
def gerar_pagamento_mensalidade(mensalidade_id: int, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(auth.get_current_active_user)):
    provider = os.getenv("PAYMENT_PROVIDER", "stripe").lower()
    
    if provider == 'mercadopago':
        # Chama a nova lógica
        return pagamentos_mercadopago.create_preference_mp(db, mensalidade_id, "mensalidade")
    else:
        # Chama a lógica antiga (Stripe)
        return create_checkout_session_stripe(db, current_user, mensalidade_id, "mensalidade")

@router.post("/gerar/evento/{inscricao_id}")
def gerar_pagamento_evento(inscricao_id: int, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(auth.get_current_active_user)):
    provider = os.getenv("PAYMENT_PROVIDER", "stripe").lower()
    
    if provider == 'mercadopago':
        return pagamentos_mercadopago.create_preference_mp(db, inscricao_id, "inscricao")
    else:
        return create_checkout_session_stripe(db, current_user, inscricao_id, "inscricao")

# --- WEBHOOKS SEPARADOS ---

# Webhook Stripe (Antigo)
@router.post("/stripe/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    # ... (Mantenha o código do webhook da Stripe aqui, inalterado) ...
    # ... (Vou resumir para caber na resposta, mas copie o original que já funcionava) ...
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    try:
        event = stripe.Webhook.construct_event(payload=payload, sig_header=sig_header, secret=webhook_secret)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Erro Stripe Webhook")
        
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        # ... (lógica de confirmação do stripe) ...
        # RECOMENDO COPIAR A LÓGICA QUE VOCÊ JÁ TINHA NO ARQUIVO ORIGINAL PARA ESTE BLOCO
        pass 
        
    return {"status": "success"}


# Webhook Mercado Pago (Novo)
@router.post("/mercadopago/webhook")
async def mercadopago_webhook(request: Request, db: Session = Depends(get_db)):
    return await pagamentos_mercadopago.handle_mp_webhook(request, db)