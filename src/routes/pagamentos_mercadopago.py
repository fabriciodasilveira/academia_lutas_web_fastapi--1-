# src/routes/pagamentos_mercadopago.py

import os
import mercadopago
import logging
from fastapi import APIRouter, Request, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from datetime import date, datetime

from src.database import get_db
from src.models.mensalidade import Mensalidade
from src.models.inscricao import Inscricao
from src.models.financeiro import Financeiro
from src.models.aluno import Aluno # Importante para acessar o email

# Inicializa o SDK
def get_sdk():
    access_token = os.getenv("MP_ACCESS_TOKEN")
    if not access_token:
        raise Exception("MP_ACCESS_TOKEN não configurado.")
    return mercadopago.SDK(access_token)

def create_preference_mp(db: Session, item_id: int, item_type: str):
    """
    Cria uma preferência de pagamento no Mercado Pago (Checkout Pro).
    """
    try:
        sdk = get_sdk()
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
            "external_reference": f"{item_type}_{item_id}", # Identificador único para o webhook
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
            
            # Dados do Pagador (Importante para o Anti-Fraude e PIX)
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
                 
            # Ajusta url de retorno para eventos
            preference_data["back_urls"]["success"] = f"{frontend_pwa_url}/#/events?payment=success"

        # Cria a preferência
        preference_response = sdk.preference().create(preference_data)
        payment_response = preference_response["response"]

        return {"init_point": payment_response["init_point"]} # Link para redirecionar o usuário

    except Exception as e:
        logging.error(f"Erro Mercado Pago: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar pagamento MP: {str(e)}")

async def handle_mp_webhook(request: Request, db: Session):
    """
    Processa notificações de pagamento do Mercado Pago.
    """
    try:
        # O MP envia os dados na query string ou no body dependendo do tipo
        params = request.query_params
        topic = params.get("topic") or params.get("type")
        id = params.get("id") or params.get("data.id")

        if topic == "payment":
            sdk = get_sdk()
            payment_info = sdk.payment().get(id)
            payment = payment_info["response"]
            
            status = payment.get("status")
            external_ref = payment.get("external_reference") # Ex: "mensalidade_12"
            
            if status == "approved" and external_ref:
                tipo, item_id = external_ref.split("_")
                item_id = int(item_id)
                
                if tipo == "mensalidade":
                    mensalidade = db.query(Mensalidade).filter(Mensalidade.id == item_id).first()
                    if mensalidade and mensalidade.status == 'pendente':
                        mensalidade.status = 'pago'
                        mensalidade.data_pagamento = date.today()
                        
                        # Lança no financeiro
                        transacao = Financeiro(
                            tipo="receita", 
                            categoria="Mensalidade", 
                            valor=mensalidade.valor, 
                            status="confirmado", 
                            data=datetime.utcnow(), 
                            descricao=f"Pagamento MP (Pix/Cartão) - Mensalidade #{mensalidade.id}",
                            forma_pagamento="Mercado Pago"
                        )
                        db.add(transacao)
                        db.commit()
                        logging.info(f"Mensalidade {item_id} paga via Mercado Pago.")

                elif tipo == "inscricao":
                    inscricao = db.query(Inscricao).filter(Inscricao.id == item_id).first()
                    if inscricao and inscricao.status == 'pendente':
                        inscricao.status = 'pago'
                        inscricao.metodo_pagamento = "Mercado Pago"
                        
                        # Busca valor do evento para garantir
                        evento = inscricao.evento # assume que o relacionamento está carregado ou lazy load funciona
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
                        logging.info(f"Inscrição {item_id} paga via Mercado Pago.")
        
        return {"status": "ok"}

    except Exception as e:
        logging.error(f"Erro Webhook MP: {e}")
        # Retorna 200 para o MP parar de tentar reenviar, mesmo com erro interno nosso
        return {"status": "error", "detail": str(e)}