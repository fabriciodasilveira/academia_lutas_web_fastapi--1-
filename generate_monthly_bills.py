import os
import logging
from datetime import date
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload
from dotenv import load_dotenv

# --- CORREÇÃO DEFINITIVA: Importar TODOS os modelos do seu projeto ---
from src.database import Base
# Garanta que TODOS os seus arquivos .py dentro de src/models/ estejam listados aqui
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
# Certifique-se de que não falta nenhum modelo!
# ------------------------------------------------------------------

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_next_due_date(last_due_date: date) -> date:
    """Calcula a próxima data de vencimento (assumindo mensalidade)."""
    return last_due_date + relativedelta(months=1)

def generate_bills():
    """
    Função principal que busca matrículas ativas e gera novas mensalidades
    para o mês atual, se ainda não existirem.
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
    current_month = today.month
    current_year = today.year
    start_of_current_month = date(current_year, current_month, 1)

    logging.info(f"Iniciando geração de mensalidades para {current_month}/{current_year}...")
    mensalidades_criadas = 0

    try:
        # Busca matrículas ativas, carregando plano e aluno
        active_matriculas = db.query(Matricula).options(
            joinedload(Matricula.plano),
            joinedload(Matricula.aluno),
            joinedload(Matricula.turma)
        ).filter(Matricula.ativa == True).all()

        logging.info(f"Encontradas {len(active_matriculas)} matrículas ativas.")

        for matricula in active_matriculas:
            # Verifica se as relações foram carregadas corretamente
            if not matricula.plano or not matricula.aluno or not matricula.turma:
                logging.warning(f"Matrícula ID {matricula.id} sem plano, aluno ou turma associado(a). Pulando.")
                continue

            last_bill = db.query(Mensalidade)\
                          .filter(Mensalidade.matricula_id == matricula.id)\
                          .order_by(Mensalidade.data_vencimento.desc())\
                          .first()

            if not last_bill:
                logging.warning(f"Matrícula ID {matricula.id} (Aluno: {matricula.aluno.nome}) não possui mensalidade inicial. Pulando.")
                continue

            next_due_date = calculate_next_due_date(last_bill.data_vencimento)

            if next_due_date.month == current_month and next_due_date.year == current_year:
                existing_bill_for_due_date = db.query(Mensalidade)\
                                                .filter(
                                                    Mensalidade.matricula_id == matricula.id,
                                                    Mensalidade.data_vencimento == next_due_date
                                                )\
                                                .first()

                if not existing_bill_for_due_date:
                    new_bill = Mensalidade(
                        aluno_id=matricula.aluno_id,
                        plano_id=matricula.plano_id,
                        matricula_id=matricula.id,
                        valor=matricula.plano.valor,
                        data_vencimento=next_due_date,
                        status="pendente"
                    )
                    db.add(new_bill)
                    mensalidades_criadas += 1
                    logging.info(f"-> Gerada nova mensalidade para Aluno ID {matricula.aluno_id} (Matrícula ID {matricula.id}), Venc: {next_due_date}")

    except Exception as e:
        logging.error(f"Erro durante a busca ou geração de mensalidades: {e}")
        db.rollback()
    else:
        db.commit()
        logging.info(f"Processo concluído. {mensalidades_criadas} novas mensalidades geradas.")
    finally:
        db.close()
        logging.info("Conexão com o banco de dados fechada.")

if __name__ == "__main__":
    generate_bills()