# Em src/routes/auth_fastapi.py

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src import auth, database, models
from src.schemas import usuario as schemas_usuario # Importa o arquivo 'usuario' e dá-lhe um apelido
from src.schemas import aluno as schemas_aluno

router = APIRouter(
    prefix="/auth", # <-- ALTERADO
    tags=["Authentication"]
)

# --- ROTAS PARA STAFF (ÁREA ADMINISTRATIVA) ---

@router.post("/token", response_model=schemas_usuario.Token)
async def login_staff_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = auth.get_user_staff(db, email=form_data.username)
    if not user or not user.hashed_password or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha incorretos")
    
    # Cria token para STAFF
    access_token = auth.create_access_token(data={"sub": user.email, "role": user.role, "type": "staff"})
    
    user_info = schemas_usuario.UsuarioRead.from_orm(user)
    return {"access_token": access_token, "token_type": "bearer", "user_info": user_info}

@router.get('/staff/login/google')
async def login_staff_google(request: Request):
    redirect_uri = "http://localhost:8000/api/v1/auth/staff/callback/google"
    return await auth.oauth.google.authorize_redirect(request, redirect_uri)

@router.get('/staff/callback/google')
async def auth_staff_google_callback(request: Request, db: Session = Depends(database.get_db)):
    try:
        token = await auth.oauth.google.authorize_access_token(request)
    except Exception:
        raise HTTPException(status_code=401, detail="Não foi possível obter o token do Google.")

    user_info_google = token.get('userinfo')
    email = user_info_google['email']
    user = auth.get_user_staff(db, email=email)

    if not user:
        # Se não existe, cria um novo STAFF como 'pendente'
        user = models.usuario.Usuario(
            email=email,
            nome=user_info_google.get('name'),
            role='pendente'
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = auth.create_access_token(data={"sub": user.email, "role": user.role, "type": "staff"})
    
    frontend_url = "http://localhost:5700"
    return RedirectResponse(url=f"{frontend_url}/login/callback?token={access_token}")

@router.get("/me/staff", response_model=schemas_usuario.UsuarioRead)
async def read_staff_me(current_user: models.usuario.Usuario = Depends(auth.get_current_active_user_staff)):
    return current_user

# --- ROTAS PARA ALUNOS (PORTAL DO ALUNO) ---

@router.get('/aluno/login/google')
async def login_aluno_google(request: Request):
    redirect_uri = "http://localhost:8000/api/v1/auth/aluno/callback/google"
    return await auth.oauth.google.authorize_redirect(request, redirect_uri)

@router.get('/aluno/callback/google')
async def auth_aluno_google_callback(request: Request, db: Session = Depends(database.get_db)):
    try:
        token = await auth.oauth.google.authorize_access_token(request)
    except Exception:
        raise HTTPException(status_code=401, detail="Não foi possível obter o token do Google.")

    user_info_google = token.get('userinfo')
    email = user_info_google['email']
    aluno = auth.get_user_aluno(db, email=email)

    # Se o aluno não existe, cria um novo
    if not aluno:
        aluno = models.aluno.Aluno(
            email=email,
            nome=user_info_google.get('name', 'Aluno Google'),
        )
        db.add(aluno)
        db.commit()
        db.refresh(aluno)

    # Cria token para ALUNO
    access_token = auth.create_access_token(data={"sub": aluno.email, "aluno_id": aluno.id, "type": "aluno"})
    
    frontend_url = "http://localhost:5700"
    # Redireciona para um novo callback no frontend, específico do portal
    return RedirectResponse(url=f"{frontend_url}/portal/login/callback?token={access_token}")

@router.get("/me/aluno", response_model=schemas_aluno.AlunoRead)
async def read_aluno_me(current_aluno: models.aluno.Aluno = Depends(auth.get_current_aluno)):
    return current_aluno