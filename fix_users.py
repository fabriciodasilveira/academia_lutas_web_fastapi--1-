import re
import logging
import os
from src.database import SessionLocal

# --- IMPORTANTE: Importar TODOS os modelos para o SQLAlchemy registrá-los ---
# Se não importarmos Matricula, Mensalidade, etc., o modelo Aluno vai dar erro
# ao tentar criar suas relações (back_populates).
from src.models.usuario import Usuario
from src.models.aluno import Aluno
from src.models.matricula import Matricula
from src.models.mensalidade import Mensalidade
from src.models.inscricao import Inscricao
from src.models.turma import Turma
from src.models.plano import Plano
# ---------------------------------------------------------------------------

from src.auth import get_password_hash

# Configuração de log simples
logging.basicConfig(level=logging.INFO, format='%(message)s')

def fix_missing_users():
    db = SessionLocal()
    try:
        print("--- INICIANDO VERIFICAÇÃO DE ALUNOS SEM LOGIN ---")
        
        # 1. Busca alunos que não têm usuário vinculado (usuario_id IS NULL)
        alunos_sem_login = db.query(Aluno).filter(Aluno.usuario_id == None).all()
        
        if not alunos_sem_login:
            print("Tudo certo! Todos os alunos já possuem usuário vinculado.")
            return

        print(f"Encontrados {len(alunos_sem_login)} alunos sem login. Processando...")

        count_criados = 0
        count_pulados = 0

        for aluno in alunos_sem_login:
            # Validações básicas
            if not aluno.cpf:
                logging.warning(f"[PULADO] {aluno.nome}: Não possui CPF cadastrado.")
                count_pulados += 1
                continue
            
            # 2. Gera a senha (CPF limpo, apenas números)
            senha_raw = re.sub(r'[^0-9]', '', aluno.cpf)
            
            if len(senha_raw) < 6:
                logging.warning(f"[PULADO] {aluno.nome}: CPF inválido/curto para senha ({aluno.cpf}).")
                count_pulados += 1
                continue

            # 3. Gera o Username
            # Tenta usar o email. Se não tiver email, cria um padrão nome.cpf
            if aluno.email:
                username_tentativa = aluno.email
            else:
                # Remove espaços e caracteres especiais do nome para criar um login
                # Ex: João Silva -> joao.1234
                primeiro_nome = aluno.nome.split()[0].lower()
                # Remove acentos simples (opcional, mas recomendado)
                primeiro_nome = primeiro_nome.replace('ã', 'a').replace('é', 'e').replace('í', 'i')
                cpf_resumo = senha_raw[:4]
                username_tentativa = f"{primeiro_nome}.{cpf_resumo}"

            # 4. Verifica se já existe um USUÁRIO com esse username (evita duplicidade)
            usuario_existente = db.query(Usuario).filter(Usuario.username == username_tentativa).first()
            
            if usuario_existente:
                # Se o usuário já existe (ex: Pai já cadastrado com esse email), apenas vinculamos!
                logging.info(f"[VINCULADO] {aluno.nome} -> Usuário existente: {username_tentativa}")
                aluno.usuario_id = usuario_existente.id
                count_criados += 1
                continue

            # 5. Se não existe, CRIA O NOVO USUÁRIO
            logging.info(f"[CRIANDO] Usuário para: {aluno.nome} | Login: {username_tentativa}")
            
            new_user = Usuario(
                username=username_tentativa,
                email=aluno.email, # Pode ser None se o banco permitir
                nome=aluno.nome,
                hashed_password=get_password_hash(senha_raw),
                role="aluno"
            )
            db.add(new_user)
            db.flush() # Garante que new_user ganhe um ID
            
            # 6. Vincula ao aluno
            aluno.usuario_id = new_user.id
            count_criados += 1
        
        db.commit()
        print("-" * 30)
        print(f"RESUMO:")
        print(f"Processados/Criados: {count_criados}")
        print(f"Pulados (Erros): {count_pulados}")
        print("Processo concluído com sucesso.")

    except Exception as e:
        print(f"ERRO CRÍTICO DURANTE O PROCESSO: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_missing_users()