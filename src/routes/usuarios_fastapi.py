# Crie o arquivo: src/routes/usuarios_fastapi.py

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src import database, models, schemas
from src.auth import get_password_hash, get_admin_user

router = APIRouter(
    prefix="/api/v1/usuarios",
    tags=["Usuarios"],
    dependencies=[Depends(get_admin_user)] # Protege TODAS as rotas neste arquivo
)

@router.post("", response_model=schemas.usuario.UsuarioRead, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.usuario.UsuarioCreate, db: Session = Depends(database.get_db)):
    """
    Cria um novo usuário (acesso restrito a administradores).
    """
    db_user = db.query(models.usuario.Usuario).filter(models.usuario.Usuario.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email já registado")
    
    hashed_password = get_password_hash(user.password)
    db_user = models.usuario.Usuario(
        email=user.email,
        nome=user.nome,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("", response_model=List[schemas.usuario.UsuarioRead])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    """
    Lista todos os usuários (acesso restrito a administradores).
    """
    users = db.query(models.usuario.Usuario).offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=schemas.usuario.UsuarioRead)
def read_user(user_id: int, db: Session = Depends(database.get_db)):
    """
    Obtém os detalhes de um usuário específico pelo ID (acesso restrito a administradores).
    """
    db_user = db.query(models.usuario.Usuario).filter(models.usuario.Usuario.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return db_user

@router.put("/{user_id}", response_model=schemas.usuario.UsuarioRead)
def update_user(user_id: int, user: schemas.usuario.UsuarioUpdate, db: Session = Depends(database.get_db)):
    """
    Atualiza um usuário existente (acesso restrito a administradores).
    """
    db_user = db.query(models.usuario.Usuario).filter(models.usuario.Usuario.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    update_data = user.dict(exclude_unset=True)
    if "password" in update_data:
        db_user.hashed_password = get_password_hash(update_data["password"])
        del update_data["password"]
        
    for key, value in update_data.items():
        setattr(db_user, key, value)
        
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(database.get_db)):
    """
    Apaga um usuário (acesso restrito a administradores).
    """
    db_user = db.query(models.usuario.Usuario).filter(models.usuario.Usuario.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    db.delete(db_user)
    db.commit()
    return None