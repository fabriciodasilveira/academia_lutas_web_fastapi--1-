import pandas as pd
import logging
import re
import os
from src.database import SessionLocal
from src.auth import get_password_hash

# Importar todos os modelos para garantir que o SQLAlchemy os registre
from src.models.usuario import Usuario
from src.models.aluno import Aluno
from src.models.matricula import Matricula
from src.models.turma import Turma
from src.models.plano import Plano
from src.models.mensalidade import Mensalidade
from src.models.inscricao import Inscricao
from src.models.evento import Evento
from src.models.historico_matricula import HistoricoMatricula
from src.models.produto import Produto
from src.models.categoria import Categoria
from src.models.financeiro import Financeiro

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(message)s')

# CONFIGURAÇÃO DO ARQUIVO
# Ajuste o nome do arquivo conforme necessário. 
# O pandas detecta automaticamente se é CSV ou Excel pela extensão.
NOME_ARQUIVO = "alunos.xlsx - Planilha1.csv" 

# SENHA PADRÃO PARA TODOS
SENHA_PADRAO = "123456"

def limpar_cpf(cpf_raw):
    if pd.isna(cpf_raw):
        return None
    return re.sub(r'[^0-9]', '', str(cpf_raw))

def gerar_username_sem_email(nome, cpf_limpo):
    """Gera um username formato nome.sobrenome ou nome.cpf_final se não tiver email."""
    if not nome:
        return None
    parts = nome.lower().split()
    base = parts[0]
    if len(parts) > 1:
        base += f".{parts[-1]}"
    else:
        # Se só tem um nome, usa os 4 primeiros do CPF para garantir unicidade
        sufixo = cpf_limpo[:4] if cpf_limpo else "0000"
        base += f".{sufixo}"
    
    # Remove caracteres especiais básicos
    base = base.replace('á', 'a').replace('ã', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('ç', 'c')
    return base

def importar_em_massa():
    print(f"--- INICIANDO IMPORTAÇÃO DE ALUNOS E USUÁRIOS ---")
    print(f"Arquivo alvo: {NOME_ARQUIVO}")
    print(f"Senha padrão definida: {SENHA_PADRAO}")
    
    db = SessionLocal()
    
    try:
        # Carrega o arquivo
        if NOME_ARQUIVO.endswith('.csv'):
            df = pd.read_csv(NOME_ARQUIVO)
        else:
            df = pd.read_excel(NOME_ARQUIVO)
            
        # Normaliza nomes das colunas (remove espaços e coloca em maiúsculo para facilitar)
        df.columns = [c.strip().upper() for c in df.columns]
        
        # Verifica colunas obrigatórias
        colunas_esperadas = ['NOME', 'CPF', 'EMAIL', 'TELEFONE']
        for col in colunas_esperadas:
            if col not in df.columns:
                print(f"ERRO: Coluna '{col}' não encontrada no arquivo.")
                return

        count_sucesso = 0
        count_erro = 0
        count_pulado = 0

        # Prepara o Hash da senha padrão (faz uma vez só para otimizar)
        senha_hash = get_password_hash(SENHA_PADRAO)

        for index, row in df.iterrows():
            nome = str(row['NOME']).strip() if pd.notna(row['NOME']) else None
            email = str(row['EMAIL']).strip() if pd.notna(row['EMAIL']) else None
            telefone = str(row['TELEFONE']).strip() if pd.notna(row['TELEFONE']) else None
            cpf_raw = row['CPF']
            cpf_limpo = limpar_cpf(cpf_raw)

            if not nome:
                logging.warning(f"Linha {index + 2}: Nome vazio. Pulando.")
                count_erro += 1
                continue

            # 1. Verificar se Aluno (CPF) já existe
            if cpf_limpo:
                aluno_existente = db.query(Aluno).filter(Aluno.cpf == cpf_limpo).first()
                if aluno_existente:
                    logging.info(f"Skipping {nome}: CPF {cpf_limpo} já cadastrado.")
                    count_pulado += 1
                    continue

            # 2. Definir Username e Email do Usuário
            username_final = email
            email_final = email

            if not email_final:
                # Se não tem email, gera username fictício e email fictício
                username_final = gerar_username_sem_email(nome, cpf_limpo)
                email_final = f"{username_final}@sememail.sistema"
            
            # 3. Verificar se Usuário (Username/Email) já existe
            usuario_existente = db.query(Usuario).filter(
                (Usuario.username == username_final) | (Usuario.email == email_final)
            ).first()

            if usuario_existente:
                # Se o usuário já existe (ex: pai já cadastrado), vamos USAR esse usuário
                # para criar o novo aluno (vínculo familiar)
                logging.info(f"--> Vinculando {nome} ao usuário existente: {usuario_existente.username}")
                novo_usuario = usuario_existente
            else:
                # Cria NOVO Usuário
                novo_usuario = Usuario(
                    username=username_final,
                    email=email_final,
                    nome=nome,
                    hashed_password=senha_hash, # Senha Fixa 123456
                    role="aluno"
                )
                db.add(novo_usuario)
                db.flush() # Gera o ID

            # 4. Criar o Aluno
            novo_aluno = Aluno(
                nome=nome,
                cpf=cpf_limpo,
                email=email if email else None, # No cadastro do aluno, deixa vazio se não tiver
                telefone=telefone,
                usuario_id=novo_usuario.id # Vincula ao usuário (novo ou existente)
            )
            db.add(novo_aluno)
            count_sucesso += 1
            logging.info(f"Cadastrado: {nome} (Login: {novo_usuario.username})")

        db.commit()
        print("-" * 30)
        print(f"IMPORTAÇÃO CONCLUÍDA")
        print(f"Novos Alunos: {count_sucesso}")
        print(f"Já Existentes: {count_pulado}")
        print(f"Erros: {count_erro}")

    except FileNotFoundError:
        print(f"ERRO: Arquivo '{NOME_ARQUIVO}' não encontrado.")
    except Exception as e:
        print(f"ERRO CRÍTICO: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    importar_em_massa()