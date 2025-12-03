import re
import logging
import os
from src.database import SessionLocal
from src.auth import get_password_hash

# --- IMPORTANTE: Importar TODOS os modelos para o SQLAlchemy registrá-los ---
from src.models.usuario import Usuario
from src.models.aluno import Aluno
from src.models.professor import Professor
from src.models.turma import Turma
from src.models.matricula import Matricula
from src.models.mensalidade import Mensalidade
from src.models.plano import Plano
from src.models.inscricao import Inscricao
from src.models.evento import Evento
from src.models.historico_matricula import HistoricoMatricula
from src.models.produto import Produto
from src.models.categoria import Categoria
from src.models.financeiro import Financeiro
# ---------------------------------------------------------------------------

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
            if aluno.email:
                username_tentativa = aluno.email
            else:
                # Remove espaços e caracteres especiais do nome para criar um login
                primeiro_nome = aluno.nome.split()[0].lower()
                # Remove acentos simples
                primeiro_nome = primeiro_nome.replace('ã', 'a').replace('é', 'e').replace('í', 'i').replace('á', 'a').replace('ó', 'o').replace('ú', 'u').replace('ç', 'c')
                cpf_resumo = senha_raw[:4]
                username_tentativa = f"{primeiro_nome}.{cpf_resumo}"

            # 4. Verifica se já existe um USUÁRIO com esse username (evita duplicidade de login)
            usuario_existente = db.query(Usuario).filter(Usuario.username == username_tentativa).first()
            
            if usuario_existente:
                # Se tem o mesmo email, vincula
                if aluno.email and usuario_existente.email == aluno.email:
                     logging.info(f"[VINCULADO] {aluno.nome} -> Usuário existente: {username_tentativa}")
                     aluno.usuario_id = usuario_existente.id
                     count_criados += 1
                     continue
                else:
                    # Se o username existe mas é outra pessoa (ex: homônimo sem email), 
                    # adiciona mais números do CPF ao login para torná-lo único
                    username_tentativa = f"{username_tentativa}.{senha_raw[-3:]}"

            # 5. CORREÇÃO DO ERRO DE EMAIL: Tratamento de Email vazio
            email_final = aluno.email
            if not email_final:
                # Se não tem email, cria um fictício único para satisfazer o banco
                # Ex: joao.1234@sememail.sistema
                email_final = f"{username_tentativa}@sememail.sistema"

            # Verificação extra de segurança para email único
            if db.query(Usuario).filter(Usuario.email == email_final).first():
                 # Se até o fictício existir, adiciona algo aleatório
                 email_final = f"{username_tentativa}.{senha_raw[-2:]}@sememail.sistema"

            # 6. Cria o Novo Usuário
            logging.info(f"[CRIANDO] Usuário para: {aluno.nome} | Login: {username_tentativa}")
            
            new_user = Usuario(
                username=username_tentativa,
                email=email_final, # Usa o email tratado (original ou fictício)
                nome=aluno.nome,
                hashed_password=get_password_hash(senha_raw),
                role="aluno"
            )
            db.add(new_user)
            db.flush() # Garante que new_user ganhe um ID
            
            # 7. Vincula ao aluno
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