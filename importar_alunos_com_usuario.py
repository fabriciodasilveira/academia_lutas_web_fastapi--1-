import pandas as pd
import logging
import re
import os
from sqlalchemy import or_
from src.database import SessionLocal
from src.auth import get_password_hash

# --- IMPORTAÇÃO DE TODOS OS MODELOS ---
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
# --------------------------------------

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(message)s')

# NOME DO ARQUIVO (Verifique se está correto)
NOME_ARQUIVO = "alunos.xlsx"

# SENHA PADRÃO
SENHA_PADRAO = "123456"

def limpar_cpf(cpf_raw):
    if pd.isna(cpf_raw):
        return None
    return re.sub(r'[^0-9]', '', str(cpf_raw))

def gerar_username_base(nome, email):
    """
    Define uma base para o username. 
    Se tiver email, usa o email. Se não, usa nome.primeiro_nome.
    """
    if email and isinstance(email, str) and '@' in email:
        return email.strip()
    
    if nome:
        # Limpa o nome para criar um login (ex: Joao Silva -> joao.silva)
        parts = nome.lower().split()
        base = parts[0]
        
        # Remove acentos
        base = base.replace('á', 'a').replace('ã', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('ç', 'c')
        
        if len(parts) > 1:
            sobrenome = parts[-1].replace('á', 'a').replace('ã', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('ç', 'c')
            base += f".{sobrenome}"
        else:
            base += ".aluno"
        return base
        
    return "usuario.desconhecido"

def encontrar_credenciais_unicas(db, base_username):
    """
    Gera um username e email únicos, incrementando um contador se necessário.
    Ex: joao@gmail.com -> joao@gmail.com.1 -> joao@gmail.com.2
    """
    contador = 0
    username_tentativa = base_username
    
    while True:
        # Se contador > 0, anexa o sufixo (ex: .1)
        if contador > 0:
            username_tentativa = f"{base_username}.{contador}"
        
        # Define o email do usuário
        # Se o username parece um email e é a primeira tentativa, tenta usar ele mesmo
        if '@' in username_tentativa and contador == 0:
            email_tentativa = username_tentativa
        else:
            # Se não parece email ou já teve colisão, gera um email interno único
            email_tentativa = f"{username_tentativa}@sememail.sistema"

        # Verifica colisão na tabela USUARIOS (username E email devem ser únicos)
        # Verifica também na tabela ALUNOS (email deve ser único)
        
        # 1. Checa tabela Usuario
        colisao_usuario = db.query(Usuario).filter(
            or_(Usuario.username == username_tentativa, Usuario.email == email_tentativa)
        ).first()
        
        # 2. Checa tabela Aluno (apenas se formos usar esse email no campo email do aluno)
        # Mas aqui faremos diferente: se o email já existe no Aluno, nós apenas limpamos o campo email do Aluno
        # e mantemos o email do Usuário (que é obrigatório e único).
        # Portanto, só precisamos garantir unicidade na tabela USUARIO para gerar o login.
        
        if not colisao_usuario:
            return username_tentativa, email_tentativa
        
        contador += 1

def importar_em_massa():
    print(f"--- INICIANDO IMPORTAÇÃO ---")
    print(f"Lendo arquivo: {NOME_ARQUIVO}")
    
    db = SessionLocal()
    
    try:
        if NOME_ARQUIVO.endswith('.csv'):
            df = pd.read_csv(NOME_ARQUIVO)
        else:
            try:
                df = pd.read_excel(NOME_ARQUIVO)
            except:
                df = pd.read_csv(NOME_ARQUIVO)
            
        df.columns = [c.strip().upper() for c in df.columns]
        
        count_sucesso = 0
        count_pulado = 0
        senha_hash = get_password_hash(SENHA_PADRAO)

        for index, row in df.iterrows():
            nome = str(row['NOME']).strip() if pd.notna(row['NOME']) else None
            email_raw = str(row['EMAIL']).strip() if pd.notna(row['EMAIL']) else None
            telefone = str(row['TELEFONE']).strip() if pd.notna(row['TELEFONE']) else None
            cpf_raw = row['CPF']
            cpf_limpo = limpar_cpf(cpf_raw)

            if not nome:
                continue

            # 1. Verifica se Aluno (CPF) já existe para não duplicar cadastro
            if cpf_limpo:
                if db.query(Aluno).filter(Aluno.cpf == cpf_limpo).first():
                    logging.warning(f"Pulando {nome}: CPF {cpf_limpo} já cadastrado.")
                    count_pulado += 1
                    continue

            # 2. Gera Username e Email Únicos para o Login
            base_user = gerar_username_base(nome, email_raw)
            username_final, email_user_final = encontrar_credenciais_unicas(db, base_user)
            
            # 3. Cria o Usuário
            novo_usuario = Usuario(
                username=username_final,
                email=email_user_final,
                nome=nome,
                hashed_password=senha_hash,
                role="aluno"
            )
            db.add(novo_usuario)
            db.flush() # Gera o ID

            # 4. Define o email do Aluno (cadastro)
            # Se o email original já estiver em uso por OUTRO aluno, deixamos None
            email_aluno_final = None
            if email_raw and '@' in email_raw:
                if not db.query(Aluno).filter(Aluno.email == email_raw).first():
                    email_aluno_final = email_raw

            # 5. Cria o Aluno vinculado ao Usuário
            novo_aluno = Aluno(
                nome=nome,
                cpf=cpf_limpo,
                email=email_aluno_final, # Pode ser None se repetido
                telefone=telefone,
                usuario_id=novo_usuario.id # Vínculo 1-para-1
            )
            db.add(novo_aluno)
            
            count_sucesso += 1
            logging.info(f"[OK] {nome} -> Login: {username_final} | Senha: {SENHA_PADRAO}")

        db.commit()
        print("-" * 30)
        print(f"Processados com sucesso: {count_sucesso}")
        print(f"Já existentes (pulados): {count_pulado}")

    except FileNotFoundError:
        print(f"ERRO: Arquivo '{NOME_ARQUIVO}' não encontrado.")
    except Exception as e:
        print(f"ERRO CRÍTICO: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    importar_em_massa()