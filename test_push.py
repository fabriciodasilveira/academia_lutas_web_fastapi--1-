import firebase_admin
from firebase_admin import credentials, messaging
from sqlalchemy.orm import Session
from src.database import SessionLocal
import os
import json

# --- CARREGAMENTO DO ECOSSISTEMA DE MODELOS ---
# Importamos todos para que o SQLAlchemy resolva os relacionamentos (relationships)
from src.models.usuario import Usuario
from src.models.aluno import Aluno
from src.models.matricula import Matricula
from src.models.mensalidade import Mensalidade
from src.models.turma import Turma
from src.models.plano import Plano
# ----------------------------------------------

# Inicialização do Firebase (Mantendo a lógica de segurança)
cert_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON')
if cert_json:
    cert_info = json.loads(cert_json)
    cert_info['private_key'] = cert_info['private_key'].replace('\\n', '\n')
    cred = credentials.Certificate(cert_info)
else:
    # Ajuste o caminho conforme a localização real do arquivo no seu servidor
    cred = credentials.Certificate("serviceAccountKey.json")

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

def enviar_notificacao_teste(username, titulo, mensagem):
    db = SessionLocal()
    try:
        # Busca o usuário e seu token
        user = db.query(Usuario).filter(Usuario.username == username).first()
        
        if not user:
            print(f"Erro: Usuário '{username}' não encontrado.")
            return
        
        if not user.fcm_token:
            print(f"Erro: Usuário '{username}' existe, mas não registrou um fcm_token.")
            return

        print(f"Token localizado para {username}: {user.fcm_token[:20]}...")

        # Estrutura da mensagem compatível com o seu sw.js
        message = messaging.Message(
            notification=messaging.Notification(
                title=titulo,
                body=mensagem,
            ),
            data={
                'url': '/portal/#/dashboard', # Link que o sw.js usará no notificationclick
            },
            token=user.fcm_token,
        )

        response = messaging.send(message)
        print('🚀 Sucesso! Notificação enviada. ID:', response)

    except Exception as e:
        print('❌ Erro ao enviar push:', str(e))
    finally:
        db.close()

if __name__ == "__main__":
    # Use o username que você confirmou que possui o token no banco
    enviar_notificacao_teste('admin', 'Academia AZE', 'Teste de Push Notification finalizado! 🥋')