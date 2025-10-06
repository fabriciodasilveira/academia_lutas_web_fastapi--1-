# Crie o arquivo: create_first_user.py
from src.database import SessionLocal
from src.models.usuario import Usuario
from src.auth import get_password_hash

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