import os
import logging
from datetime import date
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload
from dotenv import load_dotenv

# --- GARANTIR QUE TODAS AS IMPORTAÇÕES ESTEJAM AQUI ---
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

def calculate_next_due_date(last_due_date: date) -> date:
    """Calcula a próxima data de vencimento (assumindo mensalidade)."""
    # Adiciona 1 mês e mantém o dia (ex: 10/01 -> 10/02)
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
    logging.info(f"Iniciando geração de mensalidades (referência: {today.strftime('%d/%m/%Y')})...")
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

            # Busca a última mensalidade GERADA para esta matrícula
            last_bill = db.query(Mensalidade)\
                          .filter(Mensalidade.matricula_id == matricula.id)\
                          .order_by(Mensalidade.data_vencimento.desc())\
                          .first()

            if not last_bill:
                logging.warning(f"Matrícula ID {matricula.id} (Aluno: {matricula.aluno.nome}) não possui mensalidade inicial (Bug antigo?). Pulando.")
                continue

            # --- LÓGICA DE CATCH-UP (ALCANÇAR) ---
            next_due_date = calculate_next_due_date(last_bill.data_vencimento)

            # Continua gerando faturas ENQUANTO a próxima data for menor ou igual a hoje
            while next_due_date <= today:
                
                # Verifica se a fatura para este vencimento já existe
                existing_bill_for_due_date = db.query(Mensalidade)\
                                                .filter(
                                                    Mensalidade.matricula_id == matricula.id,
                                                    Mensalidade.data_vencimento == next_due_date
                                                )\
                                                .first()

                if not existing_bill_for_due_date:
                    # Se não existe, cria a nova mensalidade
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
                
                # Calcula a próxima data para o loop
                next_due_date = calculate_next_due_date(next_due_date)
            # --- FIM DA LÓGICA DE CATCH-UP ---

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