from src.database import SessionLocal
from src.auth import get_password_hash
import unidecode

# --- IMPORTAÇÃO DE TODOS OS MODELOS PARA GARANTIR O MAPEAMENTO ---
# A ordem importa pouco aqui, mas é crucial que todos sejam lidos
from src.models.usuario import Usuario
from src.models.professor import Professor
from src.models.aluno import Aluno
from src.models.matricula import Matricula
from src.models.turma import Turma
from src.models.plano import Plano
from src.models.mensalidade import Mensalidade
from src.models.inscricao import Inscricao
from src.models.evento import Evento
from src.models.financeiro import Financeiro
# -----------------------------------------------------------------

def gerar_username(nome):
    # Remove acentos e espaços, deixa minusculo. Ex: "João Silva" -> "joaosilva"
    try:
        return unidecode.unidecode(nome.lower().replace(" ", ""))
    except:
        # Fallback caso unidecode falhe ou nome seja vazio
        return "usuario_sem_nome"

def sync_professores():
    db = SessionLocal()
    try:
        print("--- INICIANDO SINCRONIZAÇÃO DE PROFESSORES ---")
        
        # Busca todos os professores
        professores = db.query(Professor).all()
        
        if not professores:
            print("❌ Nenhum professor encontrado na tabela de cadastros.")
            return

        print(f"Encontrados {len(professores)} professores cadastrados.")
        
        count_criados = 0
        
        for prof in professores:
            if not prof.nome:
                print(f"⚠️ Professor ID {prof.id} sem nome. Pulando...")
                continue

            # Tenta achar usuário pelo email (se tiver) ou pelo nome de usuário gerado
            usuario_existente = None
            username_base = gerar_username(prof.nome)
            
            # 1. Tenta buscar por email
            if prof.email:
                usuario_existente = db.query(Usuario).filter(Usuario.email == prof.email).first()
            
            # 2. Se não achou por email, tenta buscar pelo username que vamos criar
            if not usuario_existente:
                 usuario_existente = db.query(Usuario).filter(Usuario.username == username_base).first()

            if not usuario_existente:
                # Verifica se o username já está em uso por outra pessoa (duplicidade de nomes)
                if db.query(Usuario).filter(Usuario.username == username_base).first():
                    username_base = f"{username_base}_{prof.id}"
                
                email_user = prof.email if prof.email else f"{username_base}@sistema.local"
                
                novo_usuario = Usuario(
                    nome=prof.nome,
                    username=username_base,
                    email=email_user,
                    hashed_password=get_password_hash("123456"), # Senha padrão
                    role="professor" # OBRIGATÓRIO
                )
                db.add(novo_usuario)
                count_criados += 1
                print(f"✅ Usuário criado para: {prof.nome} (Login: {username_base} / Senha: 123456)")
            else:
                # Se já existe, apenas atualiza a role se necessário
                role_atual = usuario_existente.role.lower() if usuario_existente.role else ""
                if role_atual not in ['professor', 'administrador', 'gerente']:
                    usuario_existente.role = 'professor'
                    db.add(usuario_existente)
                    print(f"🔄 Perfil atualizado para 'professor': {prof.nome}")
                else:
                    print(f"ℹ️ Usuário já existe e está correto: {prof.nome}")

        db.commit()
        print("------------------------------------------------")
        print(f"Processo finalizado! {count_criados} novos usuários criados/atualizados.")
        
    except Exception as e:
        print(f"❌ Erro Crítico: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    sync_professores()