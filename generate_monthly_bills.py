import os
import logging
from datetime import date
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, joinedload
from dotenv import load_dotenv

# --- Importações de todos os modelos (necessário) ---
from src.database import Base
from src.models.aluno import Aluno
from src.models.categoria import Categoria
from src.models.evento import Evento
from src.models.financeiro import Financeiro
from src.models.historico_matricula import HistoricoMatricula
from src.models.inscricao import Inscricao
from src.models.matricula import Matricula
from src.models.mensalidade import Mensalidade
from src.models.plano import Plano
from src.models.produto import Produto
from src.models.professor import Professor
from src.models.turma import Turma
from src.models.usuario import Usuario
# ------------------------------------------------------


# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_bills():
    """
    Verifica matrículas ativas e gera a mensalidade para o mês corrente
    se ela ainda não existir, com vencimento padrão no dia 10.
    """
    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")

    if not DATABASE_URL:
        logging.error("DATABASE_URL não encontrada nas variáveis de ambiente.")
        return

    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    logging.info("Conectando ao banco de dados...")
    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        logging.info("Conexão estabelecida.")
    except Exception as e:
        logging.error(f"Erro ao conectar ao banco de dados: {e}")
        return

    today = date.today()
    DIA_VENCIMENTO_PADRAO = 10
    
    # Define a data de vencimento alvo para este mês
    # Ex: Se hoje é 06/11/2025, a data alvo é 10/11/2025
    data_vencimento_alvo = today.replace(day=DIA_VENCIMENTO_PADRAO)
    
    # Se o script rodar DEPOIS do dia 10 (ex: dia 11), 
    # ele ainda gera a fatura do mês corrente com vencimento no dia 10.
    # O script de "catch-up" (alcance) não é mais necessário com esta lógica.

    logging.info(f"Iniciando geração de mensalidades para o vencimento de: {data_vencimento_alvo.strftime('%d/%m/%Y')}")
    mensalidades_criadas = 0
    matriculas_processadas = 0

    try:
        # Busca matrículas ativas, carregando plano e aluno
        active_matriculas = db.query(Matricula).options(
            joinedload(Matricula.plano),
            joinedload(Matricula.aluno)
        ).filter(Matricula.ativa == True).all()

        logging.info(f"Encontradas {len(active_matriculas)} matrículas ativas.")

        for matricula in active_matriculas:
            # Verifica se as relações foram carregadas corretamente
            if not matricula.plano or not matricula.aluno:
                logging.warning(f"Matrícula ID {matricula.id} sem plano ou aluno associado. Pulando.")
                continue

            matriculas_processadas += 1

            # --- LÓGICA DO USUÁRIO ---
            # Verifica se já existe uma mensalidade para esta matrícula
            # E com este vencimento específico.
            existing_bill = db.query(Mensalidade)\
                              .filter(
                                  and_(
                                      Mensalidade.matricula_id == matricula.id,
                                      Mensalidade.data_vencimento == data_vencimento_alvo
                                  )
                              ).first()

            if existing_bill:
                # Log opcional (pode poluir o log, mas é útil para depurar)
                # logging.info(f"Matrícula {matricula.id} (Aluno: {matricula.aluno.nome}) já possui fatura para este mês. Pulando.")
                continue

            # Se não existe, cria a nova mensalidade
            new_bill = Mensalidade(
                aluno_id=matricula.aluno_id,
                plano_id=matricula.plano_id,
                matricula_id=matricula.id,
                valor=matricula.plano.valor,
                data_vencimento=data_vencimento_alvo,
                status="pendente"
            )
            db.add(new_bill)
            mensalidades_criadas += 1
            logging.info(f"-> GERADA fatura para Aluno ID {matricula.aluno_id} (Matrícula ID {matricula.id}), Venc: {data_vencimento_alvo}")
            # --- FIM DA LÓGICA ---

    except Exception as e:
        logging.error(f"Erro durante a busca ou geração de mensalidades: {e}")
        db.rollback()
    else:
        if mensalidades_criadas > 0:
            db.commit()
            logging.info(f"Commit realizado. {mensalidades_criadas} novas mensalidades geradas.")
        else:
            logging.info("Nenhuma nova mensalidade precisou ser gerada nesta execução.")
    finally:
        db.close()
        logging.info(f"Processo concluído. {matriculas_processadas} matrículas ativas verificadas.")

if __name__ == "__main__":
    generate_bills()