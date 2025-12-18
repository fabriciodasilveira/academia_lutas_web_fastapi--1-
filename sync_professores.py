# sync_professores.py
from src.database import SessionLocal
from src.models.professor import Professor
from src.models.usuario import Usuario
from src.auth import get_password_hash
import unidecode

def gerar_username(nome):
    # Remove acentos e espaços, deixa minusculo. Ex: "João Silva" -> "joaosilva"
    return unidecode.unidecode(nome.lower().replace(" ", ""))

def sync_professores():
    db = SessionLocal()
    try:
        print("--- INICIANDO SINCRONIZAÇÃO DE PROFESSORES ---")
        professores = db.query(Professor).all()
        
        if not professores:
            print("❌ Nenhum professor encontrado na tabela de cadastros.")
            return

        print(f"Encontrados {len(professores)} professores cadastrados.")
        
        count_criados = 0
        
        for prof in professores:
            # Tenta achar usuário pelo email ou pelo nome
            usuario_existente = None
            if prof.email:
                usuario_existente = db.query(Usuario).filter(Usuario.email == prof.email).first()
            
            if not usuario_existente:
                # Gera username e senha padrão
                username_base = gerar_username(prof.nome)
                # Verifica se username já existe
                if db.query(Usuario).filter(Usuario.username == username_base).first():
                    username_base = f"{username_base}_{prof.id}"
                
                email_user = prof.email if prof.email else f"{username_base}@sistema.local"
                
                novo_usuario = Usuario(
                    nome=prof.nome,
                    username=username_base,
                    email=email_user,
                    hashed_password=get_password_hash("123456"), # Senha padrão
                    role="professor" # OBRIGATÓRIO PARA APARECER NA LISTA
                )
                db.add(novo_usuario)
                count_criados += 1
                print(f"✅ Usuário criado para: {prof.nome} (Login: {username_base} / Senha: 123456)")
            else:
                # Se já existe, garante que a role está certa
                if usuario_existente.role != 'professor' and usuario_existente.role != 'administrador':
                    usuario_existente.role = 'professor'
                    print(f"🔄 Atualizando perfil de {prof.nome} para 'professor'")
                else:
                    print(f"ℹ️ Usuário já existe e está correto: {prof.nome}")

        db.commit()
        print("------------------------------------------------")
        print(f"Processo finalizado! {count_criados} novos usuários de professor criados.")
        print("Agora eles devem aparecer na lista do Financeiro.")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    sync_professores()