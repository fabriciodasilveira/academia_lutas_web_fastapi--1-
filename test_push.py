import firebase_admin
from firebase_admin import credentials, messaging
from sqlalchemy.orm import Session
from src.database import SessionLocal
import os
import json

# --- CARREGAMENTO COMPLETO DO ECOSSISTEMA DE MODELOS ---
# Importamos todos para que o SQLAlchemy resolva os relacionamentos (relationships)
from src.models.usuario import Usuario
from src.models.aluno import Aluno
from src.models.matricula import Matricula
from src.models.historico_matricula import HistoricoMatricula  # Resolve o erro atual
from src.models.mensalidade import Mensalidade
from src.models.inscricao import Inscricao
from src.models.evento import Evento
from src.models.graduacao import Graduacao
from src.models.professor import Professor
from src.models.turma import Turma
from src.models.plano import Plano
# -------------------------------------------------------

# Inicialização do Firebase com tratamento de segurança para a chave
cert_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON')
if cert_json:
    cert_info = json.loads(cert_json)
    cert_info['private_key'] = cert_info['private_key'].replace('\\n', '\n')
    cred = credentials.Certificate(cert_info)
else:
    # Ajuste o caminho conforme necessário para o seu ambiente
    cred = credentials.Certificate("serviceAccountKey.json")

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

def enviar_notificacao_teste(username, titulo, mensagem):
    db = SessionLocal()
    try:
        # Busca o usuário e seu token no banco de dados
        user = db.query(Usuario).filter(Usuario.username == username).first()
        
        if not user:
            print(f"Erro: Usuário '{username}' não encontrado.")
            return
        
        if not user.fcm_token:
            print(f"Erro: O usuário '{username}' não possui um token registrado no banco.")
            return

        print(f"Token localizado para {username}: {user.fcm_token[:20]}...")

        # Monta a estrutura da mensagem
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

        # Dispara o envio
        response = messaging.send(message)
        print('🚀 Sucesso! Notificação enviada com ID:', response)

    except Exception as e:
        print('❌ Erro ao enviar push:', str(e))
    finally:
        db.close()

if __name__ == "__main__":
    # Certifique-se de usar o usuário que registrou o token no PWA
    enviar_notificacao_teste('admin', 'Academia AZE', 'Teste de Push Notification: Sistema Online! 🚀')