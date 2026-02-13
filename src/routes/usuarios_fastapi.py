# Crie o arquivo: src/routes/usuarios_fastapi.py

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_ # <--- IMPORTANTE: Import para a busca

from src import database, models, schemas, auth
from src.models.usuario import Usuario
from src.auth import get_password_hash, get_admin_user, get_current_user

router = APIRouter(
    prefix="/api/v1/usuarios",
    tags=["Usuarios"],
    dependencies=[Depends(get_admin_user)] # Protege TODAS as rotas neste arquivo
)

@router.post("", response_model=schemas.usuario.UsuarioRead, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.usuario.UsuarioCreate, db: Session = Depends(database.get_db)):
    # Verifica se email já existe
    if db.query(models.usuario.Usuario).filter(models.usuario.Usuario.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email já registrado")
    
    # Verifica se username já existe
    if db.query(models.usuario.Usuario).filter(models.usuario.Usuario.username == user.username).first():
        raise HTTPException(status_code=400, detail="Nome de usuário já registrado")
    
    hashed_password = get_password_hash(user.password)
    db_user = models.usuario.Usuario(
        email=user.email,
        username=user.username,
        nome=user.nome,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- ROTA DE LEITURA ATUALIZADA COM BUSCA ---
@router.get("", response_model=schemas.usuario.UsuarioPaginated)
def read_users(
    skip: int = 0, 
    limit: int = 20, # Limite padrão ajustado para 20
    busca: Optional[str] = None, 
    db: Session = Depends(database.get_db)
):
    """
    Lista usuários com paginação e busca.
    """
    query = db.query(models.usuario.Usuario)

    if busca:
        query = query.filter(
            or_(
                models.usuario.Usuario.nome.ilike(f"%{busca}%"),
                models.usuario.Usuario.email.ilike(f"%{busca}%"),
                models.usuario.Usuario.username.ilike(f"%{busca}%")
            )
        )

    # 1. Conta o total de resultados (antes da paginação)
    total = query.count()

    # 2. Aplica a paginação
    usuarios = query.order_by(models.usuario.Usuario.nome).offset(skip).limit(limit).all()

    # 3. Retorna no formato do Schema Paginated
    return {"total": total, "usuarios": usuarios}
# --------------------------------------------

@router.get("/{user_id}", response_model=schemas.usuario.UsuarioRead)
def read_user(user_id: int, db: Session = Depends(database.get_db)):
    db_user = db.query(models.usuario.Usuario).filter(models.usuario.Usuario.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return db_user

@router.put("/{user_id}", response_model=schemas.usuario.UsuarioRead)
def update_user(user_id: int, user: schemas.usuario.UsuarioUpdate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.usuario.Usuario).filter(models.usuario.Usuario.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    update_data = user.dict(exclude_unset=True)
    
    if "username" in update_data and update_data["username"] != db_user.username:
         if db.query(models.usuario.Usuario).filter(models.usuario.Usuario.username == update_data["username"]).first():
            raise HTTPException(status_code=400, detail="Nome de usuário já está em uso.")

    if "password" in update_data:
        db_user.hashed_password = get_password_hash(update_data["password"])
        del update_data["password"]
        
    for key, value in update_data.items():
        setattr(db_user, key, value)
        
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# No arquivo src/routes/usuarios_fastapi.py

@router.put("/{user_id}/reset-password", response_model=schemas.usuario.UsuarioRead)
def reset_user_password(
    user_id: int, 
    db: Session = Depends(database.get_db),
    # Garanta que apenas admins possam chamar esta rota
    current_user: models.usuario.Usuario = Depends(auth.get_admin_user)
):
    db_user = db.query(models.usuario.Usuario).filter(models.usuario.Usuario.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Define a senha padrão criptografada
    db_user.hashed_password = auth.get_password_hash("123456")
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(database.get_db)):
    db_user = db.query(models.usuario.Usuario).filter(models.usuario.Usuario.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    db.delete(db_user)
    db.commit()
    return None



@router.post("/register-token")
async def register_fcm_token(
    data: dict, 
    db: Session = Depends(database.get_db),
    current_user: Usuario = Depends(get_current_user)
):
    token = data.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Token não fornecido")
    
    # Atualiza o token no objeto do usuário
    current_user.fcm_token = token
    db.commit() # Salva no Postgres
    
    return {"status": "success", "message": "Token atualizado com sucesso"}

@router.post("/register-token")
async def register_token(data: dict, current_user: Usuario = Depends(get_current_user), db: Session = Depends(database.get_db)):
    token = data.get("token")
    if token:
        current_user.fcm_token = token
        db.commit()
        return {"status": "success", "message": "Token atualizado"}
    return {"status": "error", "message": "Token não enviado"}, 400