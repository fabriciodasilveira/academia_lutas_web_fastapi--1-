# Arquivo: src/routes/pagamentos_mercadopago.py
# -*- coding: utf-8 -*-

import os
import mercadopago
import logging
import uuid
from fastapi import APIRouter, Request, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from datetime import date, datetime, timedelta

from src.models.mensalidade import Mensalidade
from src.models.inscricao import Inscricao
from src.models.financeiro import Financeiro
from src.models.evento import Evento

# Inicializa o SDK
def get_sdk():
    access_token = os.getenv("MP_ACCESS_TOKEN")
    if not access_token:
        logging.error("MP_ACCESS_TOKEN não configurado no ambiente.")
        return None
    return mercadopago.SDK(access_token)

def create_pix_payment(db: Session, item_id: int, item_type: str, payer_email: str, payer_first_name: str, doc_number: str):
    """
    Gera um pagamento PIX direto (Checkout Transparente) e retorna o QR Code.
    """
    sdk = get_sdk()
    if not sdk:
         raise HTTPException(status_code=500, detail="Erro de configuração de pagamento (SDK).")

    try:
        amount = 0.0
        description = ""
        external_ref = ""
        
        # 1. Identifica o item (Mensalidade ou Inscrição)
        if item_type == "mensalidade":
            db_item = db.query(Mensalidade).options(joinedload(Mensalidade.plano)).filter(Mensalidade.id == item_id).first()
            if not db_item: raise HTTPException(status_code=404, detail="Mensalidade não encontrada.")
            amount = float(db_item.valor)
            description = f"Mensalidade - {db_item.plano.nome}"
            external_ref = f"mensalidade_{item_id}"
            
        elif item_type == "inscricao":
            db_item = db.query(Inscricao).options(joinedload(Inscricao.evento)).filter(Inscricao.id == item_id).first()
            if not db_item: raise HTTPException(status_code=404, detail="Inscrição não encontrada.")
            amount = float(db_item.evento.valor_inscricao)
            description = f"Inscrição - {db_item.evento.nome}"
            external_ref = f"inscricao_{item_id}"
        else:
            raise HTTPException(status_code=400, detail="Tipo de item inválido.")

        # 2. Prepara a chave de idempotência e URLs
        request_options = mercadopago.config.RequestOptions()
        request_options.custom_headers = {
            'x-idempotency-key': str(uuid.uuid4())
        }

        # URL do Webhook (Deve ser HTTPS público para funcionar em produção)
        base_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        # Remove a barra final se houver para evitar //api...
        base_url = base_url.rstrip('/') 
        notification_url = f"{base_url}/api/v1/pagamentos/mercadopago/webhook"

        # 3. Monta o objeto de pagamento
        payment_data = {
            "transaction_amount": amount,
            "description": description,
            "payment_method_id": "pix",
            "payer": {
                "email": payer_email,
                "first_name": payer_first_name,
                "identification": {
                    "type": "CPF",
                    "number": doc_number
                }
            },
            "notification_url": notification_url,
            "external_reference": external_ref,
            # Validade do código PIX: 30 minutos
            "date_of_expiration": (datetime.utcnow() + timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
        }

        # 4. Envia para o Mercado Pago
        payment_response = sdk.payment().create(payment_data, request_options)
        payment = payment_response["response"]

        if payment_response["status"] != 201:
             logging.error(f"Erro MP Response: {payment}")
             detail_msg = payment.get("message", "Erro ao gerar PIX.")
             raise HTTPException(status_code=400, detail=detail_msg)

        # 5. Extrai os dados para o Frontend
        poi = payment.get("point_of_interaction", {})
        trans_data = poi.get("transaction_data", {})
        
        return {
            "qr_code": trans_data.get("qr_code"),           # Texto Copia e Cola
            "qr_code_base64": trans_data.get("qr_code_base64"), # Imagem Base64
            "payment_id": payment.get("id"),
            "status": payment.get("status")
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Erro interno ao gerar PIX: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao processar pagamento.")

async def handle_mp_webhook(request: Request, db: Session):
    """
    Recebe o aviso do Mercado Pago e confirma o pagamento no banco.
    """
    try:
        sdk = get_sdk()
        if not sdk: return {"status": "error", "detail": "SDK não inicializado"}

        params = request.query_params
        topic = params.get("topic") or params.get("type")
        data_id = params.get("id") or params.get("data.id")

        if topic == "payment" and data_id:
            # Busca informações atualizadas do pagamento
            payment_info = sdk.payment().get(data_id)
            payment = payment_info.get("response", {})
            
            status_pag = payment.get("status")
            external_ref = payment.get("external_reference")
            
            if status_pag == "approved" and external_ref:
                try:
                    tipo, item_id_str = external_ref.split("_")
                    item_id = int(item_id_str)
                    
                    if tipo == "mensalidade":
                        mensalidade = db.query(Mensalidade).filter(Mensalidade.id == item_id).first()
                        if mensalidade and mensalidade.status == 'pendente':
                            mensalidade.status = 'pago'
                            mensalidade.data_pagamento = date.today()
                            
                            transacao = Financeiro(
                                tipo="receita", 
                                categoria="Mensalidade", 
                                valor=mensalidade.valor, 
                                descricao=f"Pix MP - Mensalidade #{mensalidade.id}",
                                status="confirmado", 
                                data=datetime.utcnow(), 
                                forma_pagamento="Pix Mercado Pago"
                            )
                            db.add(transacao)
                            db.commit()

                    elif tipo == "inscricao":
                        inscricao = db.query(Inscricao).filter(Inscricao.id == item_id).first()
                        if inscricao and inscricao.status == 'pendente':
                            inscricao.status = 'pago'
                            inscricao.metodo_pagamento = "Pix Mercado Pago"
                            
                            evento = db.query(Evento).filter(Evento.id == inscricao.evento_id).first()
                            valor = evento.valor_inscricao if evento else 0.0
                            inscricao.valor_pago = valor

                            transacao = Financeiro(
                                tipo="receita", 
                                categoria="Evento", 
                                valor=valor, 
                                descricao=f"Pix MP - Inscrição #{inscricao.id}",
                                status="confirmado", 
                                data=datetime.utcnow(), 
                                forma_pagamento="Pix Mercado Pago"
                            )
                            db.add(transacao)
                            db.commit()
                except ValueError:
                    logging.error(f"Erro ao processar external_reference: {external_ref}")

        return {"status": "ok"}

    except Exception as e:
        logging.error(f"Erro Webhook MP: {e}")
        # Retornamos OK para o Mercado Pago não ficar reenviando em caso de erro interno nosso
        return {"status": "ok", "detail": "handled_with_error"}

# Mantido apenas para compatibilidade se necessário, mas não usado no fluxo Pix
def create_preference_mp(db, item_id, item_type):
    return {"init_point": "#"}