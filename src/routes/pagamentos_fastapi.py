# Crie o arquivo: src/routes/pagamentos_fastapi.py

import mercadopago
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import os

from src.database import get_db
from src.models.mensalidade import Mensalidade
from . import mensalidades_fastapi # Importar para usar a função de processar pagamento

router = APIRouter(
    tags=["Pagamentos"],
    prefix="/pagamentos"
)

# Carregue seu Access Token de uma variável de ambiente
MERCADO_PAGO_ACCESS_TOKEN = "TEST-553726052804131-100313-8e59152f1c52366ae9ad529039d48eec-19988581" #os.environ.get("MERCADO_PAGO_ACCESS_TOKEN")
if not MERCADO_PAGO_ACCESS_TOKEN:
    print("AVISO: MERCADO_PAGO_ACCESS_TOKEN não está configurado.")

sdk = mercadopago.SDK(MERCADO_PAGO_ACCESS_TOKEN)

# Em src/routes/pagamentos_fastapi.py

# ... (outros imports) ...

@router.post("/gerar/{mensalidade_id}")
def gerar_link_pagamento(mensalidade_id: int, db: Session = Depends(get_db)):
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

    base_url = "http://localhost:5000" 

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
        # "auto_return": "approved", # LINHA REMOVIDA
        "external_reference": str(db_mensalidade.id),
        "notification_url": "https://a928-177-94-11-207.ngrok-free.app/api/v1/pagamentos/webhook/mercadopago" # Substitua pela sua URL de webhook
    }

    try:
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response.get("response")

        if not preference or "init_point" not in preference:
            print("Erro ao criar preferência do Mercado Pago:", preference_response)
            raise HTTPException(status_code=500, detail="Falha ao comunicar com o Mercado Pago.")

        return {"init_point": preference["init_point"]}
    
    except Exception as e:
        print(f"Erro inesperado na API do Mercado Pago: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao gerar link de pagamento: {e}")


@router.post("/webhook/mercadopago")
async def webhook_mercadopago(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint para receber notificações de pagamento do Mercado Pago.
    """
    body = await request.json()
    
    if body.get("type") == "payment":
        payment_id = body["data"]["id"]
        payment_info_response = sdk.payment().get(payment_id)
        payment_info = payment_info_response["response"]
        
        if payment_info["status"] == "approved":
            mensalidade_id = int(payment_info["external_reference"])
            
            # Chama a função já existente para processar o pagamento
            mensalidades_fastapi.processar_pagamento(mensalidade_id, db)

    return {"status": "ok"}