# src/routes/pagamentos_mercadopago.py

import os
import mercadopago
import logging
from fastapi import APIRouter, Request, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from datetime import date, datetime
import uuid # Adicione este import no topo

from src.database import get_db
from src.models.mensalidade import Mensalidade
from src.models.inscricao import Inscricao
from src.models.financeiro import Financeiro
from src.models.aluno import Aluno

# Inicializa o SDK
def get_sdk():
    access_token = os.getenv("MP_ACCESS_TOKEN")
    if not access_token:
        # Loga o erro mas não quebra a aplicação inteira se a chave faltar
        logging.error("MP_ACCESS_TOKEN não configurado no ambiente.")
        return None
    return mercadopago.SDK(access_token)

def create_preference_mp(db: Session, item_id: int, item_type: str):
    """
    Cria uma preferência de pagamento no Mercado Pago (Checkout Pro).
    """
    sdk = get_sdk()
    if not sdk:
         raise HTTPException(status_code=500, detail="Mercado Pago não configurado no servidor.")

    try:
        frontend_pwa_url = os.getenv("FRONTEND_PWA_URL", "http://localhost:8000/portal").rstrip('/')
        
        preference_data = {
            "items": [],
            "payer": {},
            "back_urls": {
                "success": f"{frontend_pwa_url}/#/payments?payment=success",
                "failure": f"{frontend_pwa_url}/#/payments?payment=failure",
                "pending": f"{frontend_pwa_url}/#/payments?payment=pending"
            },
            "auto_return": "approved",
            "statement_descriptor": "ACADEMIA LUTAS",
            "external_reference": f"{item_type}_{item_id}", # ID para o webhook
        }

        if item_type == "mensalidade":
            db_item = db.query(Mensalidade).options(
                joinedload(Mensalidade.aluno), 
                joinedload(Mensalidade.plano)
            ).filter(Mensalidade.id == item_id).first()
            
            if not db_item:
                raise HTTPException(status_code=404, detail="Mensalidade não encontrada.")

            preference_data["items"].append({
                "title": f"Mensalidade - {db_item.plano.nome}",
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": float(db_item.valor)
            })
            
            if db_item.aluno.email:
                 preference_data["payer"]["email"] = db_item.aluno.email

        elif item_type == "inscricao":
            db_item = db.query(Inscricao).options(
                joinedload(Inscricao.aluno), 
                joinedload(Inscricao.evento)
            ).filter(Inscricao.id == item_id).first()
            
            if not db_item:
                 raise HTTPException(status_code=404, detail="Inscrição não encontrada.")

            preference_data["items"].append({
                "title": f"Inscrição - {db_item.evento.nome}",
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": float(db_item.evento.valor_inscricao)
            })
            
            if db_item.aluno.email:
                 preference_data["payer"]["email"] = db_item.aluno.email
                 
            preference_data["back_urls"]["success"] = f"{frontend_pwa_url}/#/events?payment=success"

        # Cria a preferência
        preference_response = sdk.preference().create(preference_data)
        payment_response = preference_response["response"]

        return {"init_point": payment_response["init_point"]}

    except Exception as e:
        logging.error(f"Erro Mercado Pago: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar pagamento MP: {str(e)}")

async def handle_mp_webhook(request: Request, db: Session):
    """
    Processa notificações de pagamento do Mercado Pago.
    """
    try:
        sdk = get_sdk()
        if not sdk: return {"status": "error", "detail": "SDK não inicializado"}

        # O MP envia os dados na query string ou no body
        params = request.query_params
        topic = params.get("topic") or params.get("type")
        id = params.get("id") or params.get("data.id")

        if topic == "payment":
            payment_info = sdk.payment().get(id)
            payment = payment_info["response"]
            
            status_pag = payment.get("status")
            external_ref = payment.get("external_reference")
            
            if status_pag == "approved" and external_ref:
                tipo, item_id = external_ref.split("_")
                item_id = int(item_id)
                
                if tipo == "mensalidade":
                    mensalidade = db.query(Mensalidade).filter(Mensalidade.id == item_id).first()
                    if mensalidade and mensalidade.status == 'pendente':
                        mensalidade.status = 'pago'
                        mensalidade.data_pagamento = date.today()
                        
                        transacao = Financeiro(
                            tipo="receita", 
                            categoria="Mensalidade", 
                            valor=mensalidade.valor, 
                            status="confirmado", 
                            data=datetime.utcnow(), 
                            descricao=f"Pagamento MP - Mensalidade #{mensalidade.id}",
                            forma_pagamento="Mercado Pago"
                        )
                        db.add(transacao)
                        db.commit()

                elif tipo == "inscricao":
                    inscricao = db.query(Inscricao).filter(Inscricao.id == item_id).first()
                    if inscricao and inscricao.status == 'pendente':
                        inscricao.status = 'pago'
                        inscricao.metodo_pagamento = "Mercado Pago"
                        
                        # Garante valor do evento
                        evento = db.query(Evento).filter(Evento.id == inscricao.evento_id).first()
                        valor = evento.valor_inscricao if evento else 0.0
                        inscricao.valor_pago = valor

                        transacao = Financeiro(
                            tipo="receita", 
                            categoria="Evento", 
                            valor=valor, 
                            status="confirmado", 
                            data=datetime.utcnow(), 
                            descricao=f"Pagamento MP - Inscrição #{inscricao.id}",
                            forma_pagamento="Mercado Pago"
                        )
                        db.add(transacao)
                        db.commit()
        
        return {"status": "ok"}

    except Exception as e:
        logging.error(f"Erro Webhook MP: {e}")
        return {"status": "error", "detail": str(e)}

def create_pix_payment(db: Session, item_id: int, item_type: str, payer_email: str, payer_first_name: str, doc_number: str):
    """
    Gera um pagamento PIX direto (Checkout Transparente).
    Retorna os dados do QR Code e Copia e Cola.
    """
    sdk = get_sdk()
    if not sdk:
         raise HTTPException(status_code=500, detail="SDK Mercado Pago não inicializado.")

    try:
        # 1. Buscar os dados do item (Mensalidade ou Inscrição)
        amount = 0.0
        description = ""
        
        if item_type == "mensalidade":
            db_item = db.query(Mensalidade).options(joinedload(Mensalidade.plano)).filter(Mensalidade.id == item_id).first()
            if not db_item: raise HTTPException(status_code=404, detail="Mensalidade não encontrada.")
            amount = float(db_item.valor)
            description = f"Mensalidade - {db_item.plano.nome}"
            
        elif item_type == "inscricao":
            db_item = db.query(Inscricao).options(joinedload(Inscricao.evento)).filter(Inscricao.id == item_id).first()
            if not db_item: raise HTTPException(status_code=404, detail="Inscrição não encontrada.")
            amount = float(db_item.evento.valor_inscricao)
            description = f"Inscrição - {db_item.evento.nome}"

        # 2. Configurar os dados do pagamento PIX
        # Importante: Usamos uuid para a chave de idempotência (evita pagamentos duplicados no clique duplo)
        request_options = mercadopago.config.RequestOptions()
        request_options.custom_headers = {
            'x-idempotency-key': str(uuid.uuid4())
        }

        # URL do seu webhook (para o MP avisar que pagou)
        # Substitua pelo seu domínio real se estiver em produção, ou ngrok em dev
        base_url = os.getenv("BACKEND_URL", "https://sua-api.onrender.com") 
        notification_url = f"{base_url}/api/v1/pagamentos/mercadopago/webhook"

        payment_data = {
            "transaction_amount": amount,
            "description": description,
            "payment_method_id": "pix",
            "payer": {
                "email": payer_email,
                "first_name": payer_first_name,
                "identification": {
                    "type": "CPF",
                    "number": doc_number # O CPF deve vir limpo (só números) ou formatado, o MP aceita ambos geralmente
                }
            },
            "notification_url": notification_url,
            "external_reference": f"{item_type}_{item_id}" # Fundamental para o Webhook saber o que baixar
        }

        # 3. Criar o pagamento
        payment_response = sdk.payment().create(payment_data, request_options)
        payment = payment_response["response"]

        if payment_response["status"] != 201:
             logging.error(f"Erro MP: {payment_response}")
             raise HTTPException(status_code=400, detail="Erro ao gerar PIX no Mercado Pago.")

        # 4. Extrair os dados do QR Code
        poi = payment.get("point_of_interaction", {})
        trans_data = poi.get("transaction_data", {})
        
        return {
            "qr_code": trans_data.get("qr_code"),           # O código Copia e Cola
            "qr_code_base64": trans_data.get("qr_code_base64"), # A imagem em base64
            "payment_id": payment.get("id"),
            "status": payment.get("status")
        }

    except Exception as e:
        logging.error(f"Erro ao gerar PIX: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar PIX: {str(e)}")