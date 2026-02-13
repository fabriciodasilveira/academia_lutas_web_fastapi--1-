# -*- coding: utf-8 -*-
import sys
import firebase_admin
from firebase_admin import credentials, messaging
from sqlalchemy import text
import os

# Importamos a engine e o get_db diretamente do seu código de produção
from src.database import engine 

# Caminho das credenciais Firebase
CHAVE_JSON = "src/serviceAccountKey.json"

def enviar_por_id(usuario_id):
    # 1. Inicializa Firebase Admin
    if not firebase_admin._apps:
        if not os.path.exists(CHAVE_JSON):
            print(f"❌ Erro: Arquivo {CHAVE_JSON} não encontrado!")
            return
        cred = credentials.Certificate(CHAVE_JSON)
        firebase_admin.initialize_app(cred)

    # 2. Busca o Token usando a sua configuração de banco oficial
    print(f"🔍 Conectando ao banco para buscar o usuário ID: {usuario_id}...")
    
    try:
        with engine.connect() as connection:
            # Query para buscar o token e nome
            query = text("SELECT fcm_token, nome FROM usuarios WHERE id = :id")
            result = connection.execute(query, {"id": usuario_id}).fetchone()

        if not result:
            print(f"❌ Usuário com ID {usuario_id} não encontrado.")
            return

        token, nome = result

        if not token:
            print(f"⚠️ O usuário {nome} (ID {usuario_id}) não tem fcm_token no banco.")
            print("Dica: Logue no portal com este usuário para sincronizar o token.")
            return

        # 3. Monta e Envia a Notificação
        message = messaging.Message(
            notification=messaging.Notification(
                title='AZE Studio 🥋',
                body=f'Olá {nome}, este é um teste disparado pelo ID!',
            ),
            data={
                'url': '/portal/#/dashboard',
            },
            token=token,
        )

        response = messaging.send(message)
        print(f"🚀 Sucesso! Notificação enviada para {nome}.")
        print(f"🆔 ID da Mensagem: {response}")

    except Exception as e:
        print(f"❌ Erro durante o processo: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python disparo_id.py [ID_DO_USUARIO]")
        sys.exit(1)

    id_alvo = sys.argv[1]
    enviar_por_id(id_alvo)