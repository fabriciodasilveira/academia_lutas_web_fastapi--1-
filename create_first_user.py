from src.database import SessionLocal
from src.auth import get_password_hash
from src.models.usuario import Usuario

# Importação dos outros modelos para garantir que o SQLAlchemy registre tudo
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
        # Verifica se o usuário já existe (agora buscando por username)
        user = db.query(Usuario).filter(Usuario.username == "admin").first()
        
        if not user:
            print("Criando primeiro usuário administrador...")
            hashed_password = get_password_hash("admin") # Senha inicial: "admin"
            
            db_user = Usuario(
                username="admin",  # <--- CAMPO NOVO E OBRIGATÓRIO
                email="admin@suaacademia.com",
                nome="Admin do Sistema",
                hashed_password=hashed_password,
                role="administrador"
            )
            db.add(db_user)
            db.commit()
            print("✅ Usuário criado com sucesso!")
            print("👤 Usuário: admin")
            print("🔑 Senha: admin")
        else:
            print("ℹ️ Usuário administrador 'admin' já existe.")
            
    except Exception as e:
        print(f"❌ Erro ao criar usuário: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_first_user()