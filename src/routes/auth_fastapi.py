# Crie o arquivo: src/routes/auth_fastapi.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src import auth, database, models
from src.schemas import usuario as schemas_usuario # Importa especificamente e dá um apelido
from src import auth, database, models, schemas
import os # Importe o 'os' para usar variáveis de ambiente


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

@router.post("/token", response_model=schemas_usuario.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = auth.get_user(db, email=form_data.username) # Usamos email como username
    if not user or not user.hashed_password or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(
        data={"sub": user.email, "role": user.role}
    )

    user_info = schemas_usuario.UsuarioRead.from_orm(user)
    return {"access_token": access_token, "token_type": "bearer", "user_info": user_info}

@router.get('/login/google')
async def login_google(request: Request):
    """
    Redireciona o usuário para a página de login do Google.
    Armazena a origem (PWA ou Flask) na sessão para o callback.
    """
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    redirect_uri = f"{backend_url}/api/v1/auth/callback/google"

    # Guarda a origem da solicitação na sessão do usuário
    origin = request.query_params.get('origin', 'flask')
    request.session['google_auth_origin'] = origin
    
    return await auth.oauth.google.authorize_redirect(request, redirect_uri)

@router.get('/callback/google', name='auth_google_callback')
async def auth_google_callback(request: Request, db: Session = Depends(database.get_db)):
    """
    Callback que o Google chama após o usuário autorizar.
    Redireciona para o frontend correto (PWA ou Flask) com o token.
    """
    try:
        token = await auth.oauth.google.authorize_access_token(request)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Não foi possível obter o token do Google: {e}")

    user_info_from_google = token.get('userinfo')
    if not user_info_from_google or not user_info_from_google.get('email'):
        raise HTTPException(status_code=400, detail="Não foi possível obter informações do usuário do Google.")

    email = user_info_from_google['email']
    user = auth.get_user(db, email=email)

    if not user:
        new_user = models.usuario.Usuario(
            email=email,
            nome=user_info_from_google.get('name', 'Usuário Google'),
            role='pendente'
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        user = new_user
    
    access_token = auth.create_access_token(
        data={"sub": user.email, "role": user.role}
    )
    
    # --- LÓGICA DE REDIRECIONAMENTO ---
    origin = request.session.get('google_auth_origin', 'flask')

    if origin == 'pwa':
        # Se veio do PWA, redireciona para a rota de callback do PWA
        response = RedirectResponse(url=f"/portal#/login/callback?token={access_token}")
    else:
        # Se veio do sistema de gestão (Flask), usa a lógica antiga
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5700") 
        response = RedirectResponse(url=f"{frontend_url}/login/callback?token={access_token}")
    
    return response

@router.get("/me", response_model=schemas.usuario.UsuarioRead)
async def read_users_me(current_user: models.usuario.Usuario = Depends(auth.get_current_active_user)):
    """
    Retorna os dados do usuário atualmente logado.
    """
    return current_user