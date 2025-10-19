import os
import logging
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta # Para adicionar meses facilmente
from sqlalchemy import create_engine, select, and_
from sqlalchemy.orm import sessionmaker, joinedload
from dotenv import load_dotenv

# Importe seus modelos do SQLAlchemy
from src.database import Base # Seus modelos devem herdar de Base
from src.models.matricula import Matricula
from src.models.mensalidade import Mensalidade
from src.models.plano import Plano
from src.models.aluno import Aluno # Importa Aluno para carregar o nome

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_next_due_date(last_due_date: date) -> date:
    """Calcula a próxima data de vencimento (assumindo mensalidade)."""
    # Adiciona um mês à última data de vencimento
    return last_due_date + relativedelta(months=1)

def generate_bills():
    """
    Função principal que busca matrículas ativas e gera novas mensalidades
    para o mês atual, se ainda não existirem.
    """
    load_dotenv() # Carrega variáveis do .env (útil para teste local)
    DATABASE_URL = os.getenv("DATABASE_URL")

    if not DATABASE_URL:
        logging.error("DATABASE_URL não encontrada nas variáveis de ambiente.")
        return

    # Corrige a URL do banco de dados para SQLAlchemy V2 (se estiver usando postgres://)
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
    # Define o primeiro dia do mês atual para a consulta
    start_of_current_month = date(current_year, current_month, 1)

    logging.info(f"Iniciando geração de mensalidades para {current_month}/{current_year}...")
    mensalidades_criadas = 0

    try:
        # 1. Buscar todas as matrículas ativas, carregando o plano e o aluno associados
        active_matriculas = db.query(Matricula).options(
            joinedload(Matricula.plano),
            joinedload(Matricula.aluno) # Carrega o aluno para log
        ).filter(Matricula.ativa == True).all()

        logging.info(f"Encontradas {len(active_matriculas)} matrículas ativas.")

        for matricula in active_matriculas:
            if not matricula.plano or not matricula.aluno:
                logging.warning(f"Matrícula ID {matricula.id} sem plano ou aluno associado. Pulando.")
                continue

            # 2. Encontrar a última mensalidade gerada para esta matrícula
            last_bill = db.query(Mensalidade)\
                          .filter(Mensalidade.matricula_id == matricula.id)\
                          .order_by(Mensalidade.data_vencimento.desc())\
                          .first()

            if not last_bill:
                logging.warning(f"Matrícula ID {matricula.id} (Aluno: {matricula.aluno.nome}) não possui nenhuma mensalidade inicial. Pulando.")
                # Idealmente, a primeira mensalidade é criada na matrícula.
                # Poderíamos adicionar lógica aqui para criar a primeira se necessário.
                continue

            # 3. Calcular a próxima data de vencimento
            next_due_date = calculate_next_due_date(last_bill.data_vencimento)

            # 4. Verificar se a próxima mensalidade é para o mês/ano ATUAL
            #    e se ela ainda não foi gerada
            if next_due_date.month == current_month and next_due_date.year == current_year:
                # Verifica se já existe uma mensalidade para esta matrícula E esta data de vencimento
                existing_bill_for_due_date = db.query(Mensalidade)\
                                                .filter(
                                                    Mensalidade.matricula_id == matricula.id,
                                                    Mensalidade.data_vencimento == next_due_date
                                                )\
                                                .first()

                if not existing_bill_for_due_date:
                    # 5. Criar a nova mensalidade
                    new_bill = Mensalidade(
                        aluno_id=matricula.aluno_id,
                        plano_id=matricula.plano_id,
                        matricula_id=matricula.id,
                        valor=matricula.plano.valor, # Pega o valor atual do plano
                        data_vencimento=next_due_date,
                        status="pendente"
                    )
                    db.add(new_bill)
                    mensalidades_criadas += 1
                    logging.info(f"-> Gerada nova mensalidade para Aluno ID {matricula.aluno_id} (Matrícula ID {matricula.id}), Venc: {next_due_date}")

    except Exception as e:
        logging.error(f"Erro durante a busca ou geração de mensalidades: {e}")
        db.rollback() # Desfaz qualquer adição parcial em caso de erro
    else:
        # Se tudo correu bem, salva as novas mensalidades no banco
        db.commit()
        logging.info(f"Processo concluído. {mensalidades_criadas} novas mensalidades geradas.")
    finally:
        db.close()
        logging.info("Conexão com o banco de dados fechada.")

if __name__ == "__main__":
    generate_bills()