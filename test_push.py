import firebase_admin
from firebase_admin import credentials, messaging
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.models.usuario import Usuario
import os

# 1. Inicializa o Firebase
# Garanta que o arquivo serviceAccountKey.json esteja na mesma pasta ou ajuste o caminho
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

def enviar_notificacao_teste(username, titulo, mensagem):
    db = SessionLocal()
    try:
        # 2. Busca o usuário e o token no banco
        user = db.query(Usuario).filter(Usuario.username == username).first()
        
        if not user or not user.fcm_token:
            print(f"Erro: Usuário '{username}' não encontrado ou não possui fcm_token.")
            return

        print(f"Enviando notificação para {username} (Token: {user.fcm_token[:15]}...)")

        # 3. Monta a mensagem (Estrutura idêntica à que o sw.js espera)
        message = messaging.Message(
            notification=messaging.Notification(
                title=titulo,
                body=mensagem,
            ),
            data={
                'url': '/portal/#/dashboard', # Página que abrirá ao clicar
            },
            token=user.fcm_token,
        )

        # 4. Envia
        response = messaging.send(message)
        print('Sucesso! Mensagem enviada com ID:', response)

    except Exception as e:
        print('Erro ao enviar push:', str(e))
    finally:
        db.close()

if __name__ == "__main__":
    # Substitua 'admin' pelo seu username de teste que registrou o token
    enviar_notificacao_teste('admin', 'Academia AZE', 'Sua primeira notificação real funcionou! 🚀')