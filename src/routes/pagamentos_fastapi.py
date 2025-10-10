# src/routes/pagamentos_fastapi.py

import mercadopago
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload
import os

from src.database import get_db
from src.models.mensalidade import Mensalidade
from src.models.inscricao import Inscricao
from src.routes import mensalidades_fastapi
from src import auth
from src.models import usuario as models_usuario

router = APIRouter(
    tags=["Pagamentos"]
)

# Carregue seu Access Token de uma variável de ambiente
MERCADO_PAGO_ACCESS_TOKEN = "TEST-553726052804131-100313-8e59152f1c52366ae9ad529039d48eec-19988581"
if not MERCADO_PAGO_ACCESS_TOKEN:
    print("AVISO: MERCADO_PAGO_ACCESS_TOKEN não está configurado.")

# Inicializa o SDK
sdk = mercadopago.SDK(MERCADO_PAGO_ACCESS_TOKEN)

@router.post("/gerar/mensalidade/{mensalidade_id}")
def gerar_link_pagamento_mensalidade(
    mensalidade_id: int, 
    db: Session = Depends(get_db), 
    current_user: models_usuario.Usuario = Depends(auth.get_current_active_user)
):
    """
    Gera um link de pagamento do Mercado Pago para uma mensalidade específica.
    """
    if not MERCADO_PAGO_ACCESS_TOKEN:
        raise HTTPException(status_code=500, detail="Access Token do Mercado Pago não configurado no servidor.")
        
    db_mensalidade = db.query(Mensalidade).filter(Mensalidade.id == mensalidade_id).first()
    if not db_mensalidade:
        raise HTTPException(status_code=404, detail="Mensalidade não encontrada")

    if db_mensalidade.status == 'pago':
        raise HTTPException(status_code=400, detail="Esta mensalidade já foi paga.")

    # base_url = "http://localhost:5000"
    base_url = os.getenv("FRONTEND_URL", "http://localhost:5700") 

    preference_data = {
        "items": [
            {
                "title": f"Mensalidade {db_mensalidade.plano.nome} - {db_mensalidade.aluno.nome}",
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": float(db_mensalidade.valor),
            }
        ],
        "back_urls": {
            "success": f"{base_url}/mensalidades",
            "failure": f"{base_url}/mensalidades",
            "pending": f"{base_url}/mensalidades"
        },
        "external_reference": f"mensalidade_{db_mensalidade.id}",
        "notification_url": "SUA_URL_WEBHOOK_AQUI/api/v1/pagamentos/webhook/mercadopago" 
    }

    try:
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response.get("response")
        if not preference or "init_point" not in preference:
            print("Erro ao criar preferência do Mercado Pago:", preference_response)
            raise HTTPException(status_code=500, detail="Falha ao comunicar com o Mercado Pago.")
        return {"init_point": preference["init_point"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno ao gerar link de pagamento: {e}")


@router.post("/gerar/evento/{inscricao_id}")
def gerar_link_pagamento_evento(inscricao_id: int, db: Session = Depends(get_db)):
    """
    Gera um link de pagamento do Mercado Pago para uma inscrição de evento.
    """
    if not MERCADO_PAGO_ACCESS_TOKEN:
        raise HTTPException(status_code=500, detail="Access Token do Mercado Pago não configurado no servidor.")

    db_inscricao = db.query(Inscricao).options(joinedload(Inscricao.aluno), joinedload(Inscricao.evento)).filter(Inscricao.id == inscricao_id).first()
    if not db_inscricao:
        raise HTTPException(status_code=404, detail="Inscrição não encontrada")

    if db_inscricao.status == 'pago':
        raise HTTPException(status_code=400, detail="Esta inscrição já foi paga.")

    # base_url = "http://localhost:5000" 
    base_url = os.getenv("FRONTEND_URL", "http://localhost:5700")

    preference_data = {
        "items": [
            {
                "title": f"Inscrição: {db_inscricao.evento.nome} - {db_inscricao.aluno.nome}",
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": float(db_inscricao.evento.valor_inscricao),
            }
        ],
        "back_urls": {
            "success": f"{base_url}/eventos/{db_inscricao.evento_id}",
            "failure": f"{base_url}/eventos/{db_inscricao.evento_id}",
            "pending": f"{base_url}/eventos/{db_inscricao.evento_id}"
        },
        "external_reference": f"evento_{db_inscricao.id}",
        "notification_url": "SUA_URL_WEBHOOK_AQUI/api/v1/pagamentos/webhook/mercadopago" 
    }

    try:
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response.get("response")
        if not preference or "init_point" not in preference:
            print("Erro ao criar preferência do Mercado Pago:", preference_response)
            raise HTTPException(status_code=500, detail="Falha ao comunicar com o Mercado Pago.")
        return {"init_point": preference["init_point"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno ao gerar link de pagamento: {e}")


@router.post("/webhook/mercadopago")
async def webhook_mercadopago(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint para receber notificações de pagamento do Mercado Pago.
    """
    body = await request.json()
    
    if body.get("type") == "payment":
        payment_id = body["data"]["id"]
        payment_info = sdk.payment().get(payment_id)["response"]
        
        if payment_info["status"] == "approved":
            external_reference = payment_info["external_reference"]
            
            # Diferencia se o pagamento é de uma mensalidade ou de um evento
            if external_reference.startswith("mensalidade_"):
                mensalidade_id = int(external_reference.split('_')[1])
                mensalidades_fastapi.processar_pagamento(mensalidade_id, db)
            
            elif external_reference.startswith("evento_"):
                inscricao_id = int(external_reference.split('_')[1])
                # Aqui você precisaria de uma função para confirmar o pagamento da inscrição
                # Vamos assumir que ela existe em 'inscricoes_fastapi'
                # inscricoes_fastapi.confirmar_pagamento(inscricao_id, db)

    return {"status": "ok"}