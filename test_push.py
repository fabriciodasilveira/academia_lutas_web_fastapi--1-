import firebase_admin
from firebase_admin import credentials, messaging
from sqlalchemy.orm import Session
from src.database import SessionLocal
import os
import json

# --- IMPORTS PARA RESOLVER DEPENDÊNCIAS DO SQLALCHEMY ---
from src.models.usuario import Usuario
from src.models.aluno import Aluno
from src.models.matricula import Matricula
from src.models.turma import Turma
from src.models.plano import Plano
# Adicione outros se o erro pular para o próximo, mas estes costumam resolver o ciclo principal
# -------------------------------------------------------

# Inicialização do Firebase (Mantendo sua correção da chave)
cert_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON')
if cert_json:
    cert_info = json.loads(cert_json)
    cert_info['private_key'] = cert_info['private_key'].replace('\\n', '\n')
    cred = credentials.Certificate(cert_info)
else:
    cred = credentials.Certificate("serviceAccountKey.json")

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

def enviar_notificacao_teste(username, titulo, mensagem):
    db = SessionLocal()
    try:
        user = db.query(Usuario).filter(Usuario.username == username).first()
        
        if not user or not user.fcm_token:
            print(f"Erro: Usuário '{username}' não encontrado ou sem fcm_token.")
            return

        print(f"Token: {user.fcm_token[:20]}...")

        message = messaging.Message(
            notification=messaging.Notification(title=titulo, body=mensagem),
            data={'url': '/portal/#/dashboard'},
            token=user.fcm_token,
        )

        response = messaging.send(message)
        print('Sucesso! ID:', response)

    except Exception as e:
        print('Erro ao enviar push:', str(e))
    finally:
        db.close()

if __name__ == "__main__":
    enviar_notificacao_teste('admin', 'Academia AZE', 'Teste final de conexão! 🥋')