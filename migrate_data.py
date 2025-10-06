# migrate_data.py

import sqlalchemy
from sqlalchemy.orm import sessionmaker

print("Iniciando script de migração de dados...")

# --- Configuração ---
OLD_DB_URL = "sqlite:///./database/academia__.db"
NEW_DB_URL = "sqlite:///./database/academia.db"

# Tabelas a serem migradas (em ordem de dependência, se houver)
# Deixamos 'matriculas' e 'mensalidades' por último, pois dependem de outras
TABLES_TO_MIGRATE = [
    "alunos",
    "professores",
    "planos",
    "turmas",
    "eventos",
    "produtos",
    "categorias",
    "financeiro",
    "matriculas",
    "mensalidades"
]

# --- Conexão com os Bancos de Dados ---
try:
    old_engine = sqlalchemy.create_engine(OLD_DB_URL)
    OldSession = sessionmaker(autocommit=False, autoflush=False, bind=old_engine)
    old_db_session = OldSession()

    new_engine = sqlalchemy.create_engine(NEW_DB_URL)
    NewSession = sessionmaker(autocommit=False, autoflush=False, bind=new_engine)
    new_db_session = NewSession()

    print("Conexão com ambos os bancos de dados estabelecida com sucesso.")
except Exception as e:
    print(f"Erro ao conectar com os bancos de dados: {e}")
    exit()

# --- Função de Migração ---
def migrate_table(table_name, old_session, new_session):
    print(f"\n--- Migrando tabela: {table_name} ---")
    
    try:
        # Pega a referência da tabela do banco de dados antigo
        old_table = sqlalchemy.Table(table_name, sqlalchemy.MetaData(), autoload_with=old_session.bind)
        
        # Pega a referência da tabela do banco de dados novo
        new_table = sqlalchemy.Table(table_name, sqlalchemy.MetaData(), autoload_with=new_session.bind)

        # Lê todos os dados da tabela antiga
        old_data = old_session.query(old_table).all()
        print(f"Encontrados {len(old_data)} registros em '{table_name}' no banco antigo.")

        count = 0
        for row in old_data:
            # Converte a linha em um dicionário
            row_data = dict(row._mapping)
            
            # ATENÇÃO: Lógica especial para a tabela 'matriculas'
            # O banco antigo não tem 'plano_id', o que causaria um erro.
            # Vamos pular a migração de matrículas por enquanto.
            if table_name == 'matriculas' and 'plano_id' not in row_data:
                print(f"AVISO: Pulando registro de matrícula ID {row_data.get('id')} por não conter 'plano_id'. Você precisará recriar as matrículas manualmente.")
                continue

            # Prepara os dados para inserção, garantindo que apenas as colunas existentes no novo banco sejam usadas
            data_to_insert = {c.name: row_data.get(c.name) for c in new_table.columns if c.name in row_data}

            # Insere os dados na nova tabela
            new_session.execute(new_table.insert().values(data_to_insert))
            count += 1
        
        new_session.commit()
        print(f"Sucesso! {count} registros foram migrados para a tabela '{table_name}' no novo banco.")

    except Exception as e:
        new_session.rollback()
        print(f"ERRO ao migrar a tabela '{table_name}': {e}")
        print("As alterações para esta tabela foram revertidas.")

# --- Execução da Migração ---
for table in TABLES_TO_MIGRATE:
    migrate_table(table, old_db_session, new_db_session)

# --- Finalização ---
old_db_session.close()
new_db_session.close()
print("\nMigração de dados concluída!")