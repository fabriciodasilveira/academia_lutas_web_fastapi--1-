import sys
import firebase_admin
from firebase_admin import credentials, messaging
import sqlalchemy
from sqlalchemy import create_engine, text
import os

# --- CONFIGURAÇÕES ---
CHAVE_JSON = "src/serviceAccountKey.json"
# Ajuste sua URL de conexão se necessário (usando as variáveis do seu .env)
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/fightclube" 

def enviar_por_id(usuario_id):
    # 1. Inicializa Firebase
    if not firebase_admin._apps:
        cred = credentials.Certificate(CHAVE_JSON)
        firebase_admin.initialize_app(cred)

    # 2. Busca o Token no Banco de Dados
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        # Buscamos o token na tabela usuarios
        result = connection.execute(
            text("SELECT fcm_token, nome FROM usuarios WHERE id = :id"),
            {"id": usuario_id}
        ).fetchone()

    if not result:
        print(f"❌ Usuário com ID {usuario_id} não encontrado no banco.")
        return

    token, nome = result

    if not token:
        print(f"⚠️ O usuário {nome} (ID {usuario_id}) não possui um token registrado.")
        print("Dica: Abra o portal com esse usuário para sincronizar o token.")
        return

    # 3. Envia a Notificação
    message = messaging.Message(
        notification=messaging.Notification(
            title='AZE Studio 🥋',
            body=f'Olá {nome}, seu teste por ID funcionou!',
        ),
        token=token,
    )

    try:
        response = messaging.send(message)
        print(f"🚀 Sucesso! Enviado para {nome}. ID da mensagem: {response}")
    except Exception as e:
        print(f"❌ Erro ao enviar: {e}")

if __name__ == "__main__":
    # Verifica se o ID foi passado como argumento no terminal
    if len(sys.argv) < 2:
        print("Uso correto: python disparo_id.py [ID_DO_USUARIO]")
        sys.exit(1)

    id_digitado = sys.argv[1]
    enviar_por_id(id_digitado)