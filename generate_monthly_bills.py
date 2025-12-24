import os
import logging
import argparse
from datetime import date
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, joinedload
from dotenv import load_dotenv

# --- Importações de todos os modelos ---
from src.database import Base
from src.models.aluno import Aluno
from src.models.matricula import Matricula
from src.models.mensalidade import Mensalidade
from src.models.plano import Plano
# (Outros imports mantidos)
from src.models.categoria import Categoria
from src.models.evento import Evento
from src.models.financeiro import Financeiro
from src.models.historico_matricula import HistoricoMatricula
from src.models.inscricao import Inscricao
from src.models.produto import Produto
from src.models.professor import Professor
from src.models.turma import Turma
from src.models.usuario import Usuario
# ------------------------------------------------------

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_bills():
    """
    Gera mensalidades para todas as matrículas ativas.
    Por padrão, gera para o PRÓXIMO MÊS com vencimento no dia 10.
    Aceita argumentos --month e --year para forçar um período específico.
    """
    # 1. Configurar leitura de argumentos da linha de comando
    parser = argparse.ArgumentParser(description='Gerador de Mensalidades')
    parser.add_argument('--month', type=int, help='Mês de referência (1-12)')
    parser.add_argument('--year', type=int, help='Ano de referência (ex: 2025)')
    args = parser.parse_args()

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

    # 2. Definir a Data Alvo
    hoje = date.today()
    DIA_VENCIMENTO_PADRAO = 10

    if args.month and args.year:
        # Se o usuário passou parâmetros, usamos eles
        try:
            data_vencimento_alvo = date(args.year, args.month, DIA_VENCIMENTO_PADRAO)
            logging.info(f"MODO MANUAL: Gerando faturas para {data_vencimento_alvo.strftime('%m/%Y')}")
        except ValueError:
            logging.error("Data inválida fornecida nos parâmetros.")
            return
    else:
        # Se não passou nada, padrão é PRÓXIMO MÊS (Next Month)
        # Ex: Rodando em Dezembro -> Gera Janeiro
        data_base = hoje + relativedelta(months=1)
        data_vencimento_alvo = date(data_base.year, data_base.month, DIA_VENCIMENTO_PADRAO)
        logging.info(f"MODO AUTOMÁTICO: Gerando faturas para o próximo mês ({data_vencimento_alvo.strftime('%m/%Y')})")

    mensalidades_criadas = 0
    matriculas_processadas = 0

    try:
        # Busca matrículas ativas
        active_matriculas = db.query(Matricula).options(
            joinedload(Matricula.plano),
            joinedload(Matricula.aluno)
        ).filter(Matricula.ativa == True).all()

        logging.info(f"Encontradas {len(active_matriculas)} matrículas ativas.")

        for matricula in active_matriculas:
            if not matricula.plano or not matricula.aluno:
                logging.warning(f"Matrícula ID {matricula.id} sem plano ou aluno. Pulando.")
                continue

            matriculas_processadas += 1

            # 3. Verificar se já existe (Evitar duplicidade)
            existing_bill = db.query(Mensalidade)\
                              .filter(
                                  and_(
                                      Mensalidade.matricula_id == matricula.id,
                                      Mensalidade.data_vencimento == data_vencimento_alvo
                                  )
                              ).first()

            if existing_bill:
                # Já existe cobrança para este mês/ano específico
                continue

            # 4. Criar a nova mensalidade
            # Mantém sempre o DIA_VENCIMENTO_PADRAO (10) independente do cadastro da matrícula
            new_bill = Mensalidade(
                aluno_id=matricula.aluno_id,
                plano_id=matricula.plano_id,
                matricula_id=matricula.id,
                valor=matricula.plano.valor,
                data_vencimento=data_vencimento_alvo, # Sempre dia 10 do mês/ano alvo
                status="pendente"
            )
            db.add(new_bill)
            mensalidades_criadas += 1
            logging.info(f"-> GERADA: {matricula.aluno.nome} | Venc: {data_vencimento_alvo} | R$ {matricula.plano.valor}")

    except Exception as e:
        logging.error(f"Erro durante a geração de mensalidades: {e}")
        db.rollback()
    else:
        if mensalidades_criadas > 0:
            db.commit()
            logging.info(f"SUCESSO: {mensalidades_criadas} novas mensalidades geradas.")
        else:
            logging.info(f"Nenhuma nova mensalidade necessária para {data_vencimento_alvo.strftime('%m/%Y')} (todas já existem).")
    finally:
        db.close()

if __name__ == "__main__":
    generate_bills()