from src.database import SessionLocal
from src.auth import get_password_hash

# Importação de todos os modelos para garantir que o SQLAlchemy
# conheça todas as tabelas e seus relacionamentos.
from src.models.usuario import Usuario
from src.models.aluno import Aluno
from src.models.matricula import Matricula
from src.models.turma import Turma
from src.models.professor import Professor
from src.models.plano import Plano
from src.models.mensalidade import Mensalidade
from src.models.inscricao import Inscricao
from src.models.evento import Evento
from src.models.historico_matricula import HistoricoMatricula
from src.models.produto import Produto
from src.models.categoria import Categoria
from src.models.financeiro import Financeiro


def create_first_user():
    db = SessionLocal()
    try:
        # Verifique se o usuário já existe
        user = db.query(Usuario).filter(Usuario.email == "admin@suaacademia.com").first()
        if not user:
            print("Criando primeiro usuário administrador...")
            hashed_password = get_password_hash("admin") # Senha inicial: "admin"
            
            db_user = Usuario(
                email="admin@suaacademia.com",
                nome="Admin do Sistema",
                hashed_password=hashed_password,
                role="administrador"
            )
            db.add(db_user)
            db.commit()
            print("Usuário 'admin@suaacademia.com' criado com sucesso!")
            print("Senha: admin")
        else:
            print("Usuário administrador já existe.")
    finally:
        db.close()

if __name__ == "__main__":
    create_first_user()