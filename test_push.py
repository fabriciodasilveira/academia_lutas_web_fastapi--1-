import firebase_admin
from firebase_admin import credentials, messaging
from sqlalchemy.orm import Session
from src.database import SessionLocal
import os
import json

# --- ADICIONE ESTES IMPORTS PARA REGISTRAR OS MODELOS ---
from src.models.usuario import Usuario
from src.models.aluno import Aluno  # Importar explicitamente para o SQLAlchemy localizá-lo
# -------------------------------------------------------

# 1. Inicializa o Firebase via Variável de Ambiente (Correção da Chave)
cert_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON')
if cert_json:
    cert_info = json.loads(cert_json)
    cert_info['private_key'] = cert_info['private_key'].replace('\\n', '\n')
    cred = credentials.Certificate(cert_info)
else:
    # Fallback local se o arquivo existir
    cred = credentials.Certificate("src/serviceAccountKey.json")

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

def enviar_notificacao_teste(username, titulo, mensagem):
    db = SessionLocal()
    try:
        # Busca o usuário
        user = db.query(Usuario).filter(Usuario.username == username).first()
        
        if not user or not user.fcm_token:
            print(f"Erro: Usuário '{username}' não encontrado ou sem fcm_token.")
            return

        print(f"Token encontrado: {user.fcm_token[:20]}...")

        # Monta a mensagem
        message = messaging.Message(
            notification=messaging.Notification(
                title=titulo,
                body=mensagem,
            ),
            data={
                'url': '/portal/#/dashboard',
            },
            token=user.fcm_token,
        )

        response = messaging.send(message)
        print('Sucesso! ID da mensagem:', response)

    except Exception as e:
        print('Erro ao enviar push:', str(e))
    finally:
        db.close()

if __name__ == "__main__":
    enviar_notificacao_teste('admin', 'Teste Academia', 'O circuito completo funcionou! 🥋')