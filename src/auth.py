# Crie o arquivo: src/auth.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
import httpx

# --- MODIFICAÇÕES AQUI ---
from src import database
from src.models import usuario as models_usuario # Importa o módulo 'usuario' e dá um apelido
# --- FIM DAS MODIFICAÇÕES ---


# --- CONFIGURAÇÃO DE SEGURANÇA ---
SECRET_KEY = os.environ.get("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8 # Token expira em 8 horas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

config = Config('.env') # Lê as variáveis do arquivo .env

timeout_client = httpx.AsyncClient(timeout=15.0)

oauth = OAuth(config, client=timeout_client)

oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- DEPENDÊNCIAS DE AUTENTICAÇÃO E AUTORIZAÇÃO ---
def get_user(db: Session, email: str):
    # --- MODIFICAÇÃO AQUI ---
    return db.query(models_usuario.Usuario).filter(models_usuario.Usuario.email == email).first()

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas", headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(db, email=email)
    if user is None:
        raise credentials_exception
    return user

# --- MODIFICAÇÃO AQUI ---
async def get_current_active_user(current_user: models_usuario.Usuario = Depends(get_current_user)):
    """
    Verifica se o usuário está ativo. Bloqueia se o papel for 'pendente'.
    """
    if current_user.role == "pendente":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Sua conta está pendente de aprovação por um administrador."
        )
    return current_user

# --- MODIFICAÇÃO AQUI ---
async def get_admin_or_gerente(current_user: models_usuario.Usuario = Depends(get_current_active_user)):
    if current_user.role not in ["administrador", "gerente"]:
        raise HTTPException(status_code=403, detail="Acesso restrito a Administradores ou Gerentes.")
    return current_user

# --- MODIFICAÇÃO AQUI ---
async def get_admin_user(current_user: models_usuario.Usuario = Depends(get_current_active_user)):
    """
    Verifica se o usuário atual tem o papel de 'administrador'.
    Se não tiver, bloqueia a requisição.
    """
    if current_user.role != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Acesso restrito a administradores."
        )
    return current_user