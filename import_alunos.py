import pandas as pd
from sqlalchemy.orm import Session

# --- CORREÇÃO: Importar todos os modelos relacionados ---
from src.database import SessionLocal
from src.models.aluno import Aluno
from src.models.turma import Turma
from src.models.plano import Plano
from src.models.mensalidade import Mensalidade
from src.models.inscricao import Inscricao
from src.models.historico_matricula import HistoricoMatricula
from src.models.matricula import Matricula
from src.models.professor import Professor
from src.models.evento import Evento # <- ADICIONE ESTA LINHA
# -------------------------------------------------------------

# --- CONFIGURAÇÕES ---
EXCEL_FILE_PATH = "importacao_alunos.xlsx"
NOME_DA_COLUNA = "NOME"
# ---------------------

def importar_alunos():
    print("Iniciando a importação de alunos do Excel...")
    
    # Inicia a conexão com o banco de dados
    db: Session = SessionLocal()
    
    try:
        # Tenta ler o arquivo Excel
        try:
            df = pd.read_excel(EXCEL_FILE_PATH)
            print(f"Arquivo '{EXCEL_FILE_PATH}' lido com sucesso.")
        except FileNotFoundError:
            print(f"ERRO: O arquivo '{EXCEL_FILE_PATH}' não foi encontrado na pasta raiz do projeto.")
            return
        except Exception as e:
            print(f"ERRO ao ler o arquivo Excel: {e}")
            return

        # Verifica se a coluna com os nomes existe
        if NOME_DA_COLUNA not in df.columns:
            print(f"ERRO: A coluna '{NOME_DA_COLUNA}' não foi encontrada no arquivo Excel.")
            print(f"Colunas encontradas: {list(df.columns)}")
            return
            
        nomes_para_importar = df[NOME_DA_COLUNA].dropna().unique()
        print(f"Encontrados {len(nomes_para_importar)} nomes únicos para importar.")
        
        alunos_novos = 0
        alunos_existentes = 0
        
        for nome_aluno in nomes_para_importar:
            # Verifica se o aluno já existe no banco de dados
            aluno_existente = db.query(Aluno).filter(Aluno.nome == str(nome_aluno)).first()
            
            if not aluno_existente:
                # Se não existe, cria um novo aluno
                novo_aluno = Aluno(nome=str(nome_aluno))
                db.add(novo_aluno)
                alunos_novos += 1
                print(f"  + Adicionando: {nome_aluno}")
            else:
                alunos_existentes += 1
        
        if alunos_novos > 0:
            print("\nSalvando novos alunos no banco de dados...")
            db.commit()
            print("Alunos salvos com sucesso!")
        else:
            print("\nNenhum aluno novo para adicionar.")

        print("\n--- RESUMO DA IMPORTAÇÃO ---")
        print(f"Alunos novos cadastrados: {alunos_novos}")
        print(f"Alunos que já existiam: {alunos_existentes}")
        print("----------------------------")

    finally:
        # Garante que a conexão com o banco de dados seja fechada
        db.close()
        print("\nConexão com o banco de dados fechada. Processo concluído.")

if __name__ == "__main__":
    importar_alunos()