import os
import stripe
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status, Header
from sqlalchemy.orm import Session, joinedload
from datetime import date, datetime

from src.database import get_db
from src.models.mensalidade import Mensalidade
from src.models.inscricao import Inscricao
from src.models.financeiro import Financeiro
from src import auth
from src.models import usuario as models_usuario

router = APIRouter(
    tags=["Pagamentos"]
)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@router.get("/stripe-key")
def get_stripe_key():
    return {"publicKey": os.getenv("STRIPE_PUBLIC_KEY")}

def create_checkout_session(db: Session, current_user: models_usuario.Usuario, item_id: int, item_type: str):
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Chave de API da Stripe não configurada.")
    
    frontend_pwa_url = os.getenv("FRONTEND_PWA_URL", "http://localhost:8000/portal")
    line_item = {}
    
    if item_type == "mensalidade":
        db_item = db.query(Mensalidade).options(joinedload(Mensalidade.aluno), joinedload(Mensalidade.plano)).filter(Mensalidade.id == item_id).first()
        if not db_item or db_item.aluno.usuario_id != current_user.id:
            raise HTTPException(status_code=404, detail="Mensalidade não encontrada ou não pertence a este usuário.")
        line_item = { "price_data": { "currency": "brl", "product_data": { "name": f"Mensalidade - {db_item.plano.nome}" }, "unit_amount": int(db_item.valor * 100), }, "quantity": 1, }
        success_path = "#/payments?payment=success"
    
    elif item_type == "inscricao":
        db_item = db.query(Inscricao).options(joinedload(Inscricao.aluno), joinedload(Inscricao.evento)).filter(Inscricao.id == item_id).first()
        if not db_item or db_item.aluno.usuario_id != current_user.id:
            raise HTTPException(status_code=404, detail="Inscrição não encontrada ou não pertence a este usuário.")
        line_item = { "price_data": { "currency": "brl", "product_data": { "name": f"Inscrição - {db_item.evento.nome}" }, "unit_amount": int(db_item.evento.valor_inscricao * 100), }, "quantity": 1, }
        success_path = "#/events?payment=success"

    try:
        # --- CORREÇÃO APLICADA AQUI ---
        # Removemos a barra entre a URL base e o caminho com hash (#)
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
        return {"sessionId": checkout_session.id}
    except Exception as e:
        logging.error(f"Erro ao criar sessão de checkout na Stripe: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stripe/mensalidade/{mensalidade_id}")
def gerar_checkout_stripe_mensalidade(mensalidade_id: int, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(auth.get_current_active_user)):
    return create_checkout_session(db, current_user, mensalidade_id, "mensalidade")

@router.post("/stripe/evento/{inscricao_id}")
def gerar_checkout_stripe_evento(inscricao_id: int, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(auth.get_current_active_user)):
    return create_checkout_session(db, current_user, inscricao_id, "inscricao")

@router.post("/stripe/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    if not webhook_secret:
        raise HTTPException(status_code=500, detail="Secret do webhook da Stripe não configurado.")

    try:
        event = stripe.Webhook.construct_event(payload=payload, sig_header=sig_header, secret=webhook_secret)
    except ValueError:
        raise HTTPException(status_code=400, detail="Payload inválido")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Assinatura inválida")

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        item_id = int(session['metadata']['item_id'])
        item_type = session['metadata']['item_type']

        if item_type == 'mensalidade':
            db_mensalidade = db.query(Mensalidade).filter(Mensalidade.id == item_id).first()
            if db_mensalidade and db_mensalidade.status == 'pendente':
                db_mensalidade.status = 'pago'
                db_mensalidade.data_pagamento = date.today()
                transacao = Financeiro(tipo="receita", categoria="Mensalidade", valor=db_mensalidade.valor, status="confirmado", data=datetime.utcnow(), descricao=f"Pagamento online (Stripe) da mensalidade ID {db_mensalidade.id}")
                db.add(transacao)

        elif item_type == 'inscricao':
            db_inscricao = db.query(Inscricao).filter(Inscricao.id == item_id).first()
            if db_inscricao and db_inscricao.status == 'pendente':
                db_inscricao.status = 'pago'
                db_inscricao.valor_pago = db_inscricao.evento.valor_inscricao
                db_inscricao.metodo_pagamento = "Stripe"
                transacao = Financeiro(tipo="receita", categoria="Evento", valor=db_inscricao.valor_pago, status="confirmado", data=datetime.utcnow(), descricao=f"Pagamento online (Stripe) da inscrição ID {db_inscricao.id}")
                db.add(transacao)
        
        db.commit()

    return {"status": "success"}