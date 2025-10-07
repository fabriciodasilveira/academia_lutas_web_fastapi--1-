from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config

from src import database, models

# --- CONFIGURAÇÃO DE SEGURANÇA ---
SECRET_KEY = os.environ.get("SECRET_KEY", "uma_chave_secreta_muito_forte_deve_ser_usada_aqui")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8 # Token expira em 8 horas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token") # Para login do staff

# --- FUNÇÕES DE SENHA ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# --- FUNÇÃO DE TOKEN ATUALIZADA ---
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- CONFIGURAÇÃO DO OAUTH (LOGIN COM GOOGLE) ---
config = Config('.env')
oauth = OAuth(config)
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# --- DEPENDÊNCIAS DE AUTENTICAÇÃO E AUTORIZAÇÃO ---

# Para Staff (Usuários do sistema de gestão)
def get_user_staff(db: Session, email: str):
    return db.query(models.usuario.Usuario).filter(models.usuario.Usuario.email == email).first()

async def get_current_user_staff(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas", headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "staff": # Verifica se o token é do tipo 'staff'
            raise credentials_exception
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user_staff(db, email=email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user_staff(current_user: models.usuario.Usuario = Depends(get_current_user_staff)):
    if current_user.role == "pendente":
        raise HTTPException(status_code=403, detail="Sua conta está pendente de aprovação.")
    return current_user

async def get_admin_user(current_user: models.usuario.Usuario = Depends(get_current_active_user_staff)):
    if current_user.role != "administrador":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores.")
    return current_user

# --- NOVAS DEPENDÊNCIAS PARA ALUNOS ---
def get_user_aluno(db: Session, email: str):
    return db.query(models.aluno.Aluno).filter(models.aluno.Aluno.email == email).first()

async def get_current_aluno(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais de aluno inválidas", headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "aluno": # Verifica se o token é do tipo 'aluno'
            raise credentials_exception
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    aluno = get_user_aluno(db, email=email)
    if aluno is None:
        raise credentials_exception
    return aluno


# Em src/auth.py

# ... (imports e código existentes até a função get_admin_user) ...

async def get_admin_user(current_user: models.usuario.Usuario = Depends(get_current_active_user_staff)):
    if current_user.role != "administrador":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores.")
    return current_user

# --- ADICIONE ESTA FUNÇÃO DE VOLTA ---
async def get_admin_or_gerente(current_user: models.usuario.Usuario = Depends(get_current_active_user_staff)):
    """
    Verifica se o usuário atual tem o papel de 'administrador' ou 'gerente'.
    """
    if current_user.role not in ["administrador", "gerente"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Acesso restrito a Administradores ou Gerentes."
        )
    return current_user
# --- FIM DA ADIÇÃO ---


