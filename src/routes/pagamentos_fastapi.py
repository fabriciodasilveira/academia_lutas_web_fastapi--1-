import os
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload

from src.database import get_db
from src.models.mensalidade import Mensalidade
from src.models.inscricao import Inscricao
from src import auth
from src.models import usuario as models_usuario

router = APIRouter(
    tags=["Pagamentos"],
)

# Configura a chave secreta da Stripe a partir das variáveis de ambiente
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Endpoint para o frontend buscar a chave pública
@router.get("/stripe-key")
def get_stripe_key():
    return {"publicKey": os.getenv("STRIPE_PUBLIC_KEY")}

def create_checkout_session(db: Session, current_user: models_usuario.Usuario, item_id: int, item_type: str):
    """Função genérica para criar uma sessão de checkout na Stripe."""
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Chave de API da Stripe não configurada.")

    frontend_url = os.getenv("FRONTEND_PWA_URL", "http://localhost:8000/portal")
    line_item = {}
    
    if item_type == "mensalidade":
        db_item = db.query(Mensalidade).options(joinedload(Mensalidade.aluno), joinedload(Mensalidade.plano)).filter(Mensalidade.id == item_id).first()
        if not db_item or db_item.aluno.usuario_id != current_user.id:
            raise HTTPException(status_code=404, detail="Mensalidade não encontrada ou não pertence a este usuário.")
        line_item = {
            "price_data": {
                "currency": "brl",
                "product_data": {
                    "name": f"Mensalidade - {db_item.plano.nome}",
                    "description": f"Vencimento: {db_item.data_vencimento.strftime('%d/%m/%Y')}",
                },
                "unit_amount": int(db_item.valor * 100),  # Valor em centavos
            },
            "quantity": 1,
        }
        success_path = "#/payments?payment=success"
    
    elif item_type == "inscricao":
        db_item = db.query(Inscricao).options(joinedload(Inscricao.aluno), joinedload(Inscricao.evento)).filter(Inscricao.id == item_id).first()
        if not db_item or db_item.aluno.usuario_id != current_user.id:
            raise HTTPException(status_code=404, detail="Inscrição não encontrada ou não pertence a este usuário.")
        line_item = {
            "price_data": {
                "currency": "brl",
                "product_data": {
                    "name": f"Inscrição - {db_item.evento.nome}",
                },
                "unit_amount": int(db_item.evento.valor_inscricao * 100),
            },
            "quantity": 1,
        }
        success_path = "#/events?payment=success"

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card', 'boleto'],
            line_items=[line_item],
            mode='payment',
            success_url=f"{frontend_url}{success_path}",
            cancel_url=f"{frontend_url}#/payments?payment=canceled",
            metadata={
                'item_id': item_id,
                'item_type': item_type
            }
        )
        return {"sessionId": checkout_session.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stripe/mensalidade/{mensalidade_id}")
def gerar_checkout_stripe_mensalidade(
    mensalidade_id: int, 
    db: Session = Depends(get_db), 
    current_user: models_usuario.Usuario = Depends(auth.get_current_active_user)
):
    return create_checkout_session(db, current_user, mensalidade_id, "mensalidade")

@router.post("/stripe/evento/{inscricao_id}")
def gerar_checkout_stripe_evento(
    inscricao_id: int, 
    db: Session = Depends(get_db), 
    current_user: models_usuario.Usuario = Depends(auth.get_current_active_user)
):
    return create_checkout_session(db, current_user, inscricao_id, "inscricao")