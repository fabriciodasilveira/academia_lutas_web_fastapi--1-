from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import shutil
from pathlib import Path
import logging

from src import database, models, auth
from src.schemas import portal_aluno as schemas_portal
from src.schemas import aluno as schemas_aluno
from src.models.mensalidade import Mensalidade
from src.schemas.mensalidade import MensalidadeRead
from typing import List
from src.models.inscricao import Inscricao
from src.schemas.portal_aluno import PendenciaFinanceira # Adicionado

# --- Lógica de Upload (copiada de alunos_fastapi.py) ---
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads" / "alunos"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def save_upload_file(upload_file: UploadFile, destination: Path) -> None:
    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()
# --- Fim da Lógica de Upload ---


router = APIRouter(
    prefix="/api/v1/portal",
    tags=["Portal do Aluno"]
)

@router.post("/register", response_model=schemas_aluno.AlunoRead, status_code=status.HTTP_201_CREATED)
def register_aluno(aluno_data: schemas_portal.AlunoRegistration, db: Session = Depends(database.get_db)):
    # ... (código existente, sem alterações)
    db_user = auth.get_user(db, email=aluno_data.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este email já está cadastrado no sistema."
        )

    hashed_password = auth.get_password_hash(aluno_data.password)
    new_user = models.usuario.Usuario(
        email=aluno_data.email,
        nome=aluno_data.nome,
        hashed_password=hashed_password,
        role="aluno"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    new_aluno = models.aluno.Aluno(
        usuario_id=new_user.id,
        nome=aluno_data.nome,
        email=aluno_data.email,
        telefone=aluno_data.telefone,
        data_nascimento=aluno_data.data_nascimento
    )
    db.add(new_aluno)
    db.commit()
    db.refresh(new_aluno)
    
    return new_aluno


@router.get("/me", response_model=schemas_aluno.AlunoRead)
def get_current_aluno_profile(
    current_user: models.usuario.Usuario = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    # ... (código existente, sem alterações)
    if current_user.role != "aluno":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")

    aluno_profile = db.query(models.aluno.Aluno).filter(models.aluno.Aluno.usuario_id == current_user.id).first()
    if not aluno_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de aluno não encontrado.")
        
    return aluno_profile


# --- FUNÇÃO INTEIRA ATUALIZADA ---
@router.put("/me", response_model=schemas_aluno.AlunoRead)
def update_current_aluno_profile(
    db: Session = Depends(database.get_db),
    current_user: models.usuario.Usuario = Depends(auth.get_current_active_user),
    # Campos recebidos como Form data
    nome: str = Form(...),
    cpf: Optional[str] = Form(None),
    telefone: Optional[str] = Form(None),
    data_nascimento: Optional[str] = Form(None),
    endereco: Optional[str] = Form(None),
    observacoes: Optional[str] = Form(None),
    foto: Optional[UploadFile] = File(None)
):
    """
    Permite que o aluno logado atualize seu próprio perfil.
    Agora aceita dados de formulário e upload de arquivo.
    """
    if current_user.role != "aluno":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")

    db_aluno = db.query(models.aluno.Aluno).filter(models.aluno.Aluno.usuario_id == current_user.id).first()
    if not db_aluno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de aluno não encontrado.")

    # Atualiza os campos de texto
    db_aluno.nome = nome
    db_aluno.cpf = cpf
    db_aluno.telefone = telefone
    db_aluno.endereco = endereco
    db_aluno.observacoes = observacoes
    
    if data_nascimento:
        try:
            db_aluno.data_nascimento = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
        except ValueError:
            # Ignora data inválida, mas você poderia retornar um erro se preferir
            pass

    # Processa a nova foto, se enviada
    if foto:
        # Remove a foto antiga se ela existir
        if db_aluno.foto:
            old_foto_path = Path(str(BASE_DIR) + db_aluno.foto)
            if old_foto_path.exists():
                old_foto_path.unlink()
        
        # Salva a nova foto
        safe_filename = f"{db_aluno.id}_{foto.filename.replace(' ', '_')}"
        file_location = UPLOAD_DIR / safe_filename
        save_upload_file(foto, file_location)
        db_aluno.foto = f"/static/uploads/alunos/{safe_filename}"
    
    db.commit()
    db.refresh(db_aluno)
    return db_aluno

@router.get("/mensalidades", response_model=List[MensalidadeRead])
def get_aluno_mensalidades(
    current_user: models.usuario.Usuario = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    """
    Retorna o histórico de mensalidades apenas para o aluno logado.
    """
    if current_user.role != "aluno":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")

    aluno_profile = db.query(models.aluno.Aluno).filter(models.aluno.Aluno.usuario_id == current_user.id).first()
    if not aluno_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de aluno não encontrado.")

    mensalidades = db.query(Mensalidade).filter(Mensalidade.aluno_id == aluno_profile.id).order_by(Mensalidade.data_vencimento.desc()).all()
    return mensalidades

# Adicione esta nova rota ao final do arquivo src/routes/portal_aluno_fastapi.py
@router.get("/pendencias", response_model=List[PendenciaFinanceira])
def get_aluno_pendencias_financeiras(
    current_user: models.usuario.Usuario = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    """
    Retorna uma lista unificada de todas as pendências financeiras (mensalidades e inscrições)
    para o aluno logado.
    """
    if current_user.role != "aluno":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")

    aluno_profile = db.query(models.aluno.Aluno).filter(models.aluno.Aluno.usuario_id == current_user.id).first()
    if not aluno_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de aluno não encontrado.")

    pendencias = []

    # Busca mensalidades
    mensalidades = db.query(Mensalidade).filter(Mensalidade.aluno_id == aluno_profile.id).all()
    for m in mensalidades:
        pendencias.append(PendenciaFinanceira(
            tipo='mensalidade',
            id=m.id,
            descricao=f"Mensalidade - {m.plano.nome}",
            data_vencimento=m.data_vencimento,
            valor=m.valor,
            status=m.status
        ))

    # Busca inscrições em eventos
    inscricoes = db.query(Inscricao).filter(Inscricao.aluno_id == aluno_profile.id).all()
    for i in inscricoes:
        pendencias.append(PendenciaFinanceira(
            tipo='inscricao',
            id=i.id,
            descricao=f"Inscrição - {i.evento.nome}",
            # Usamos a data do evento como referência de "vencimento"
            data_vencimento=i.evento.data_evento.date(),
            valor=i.evento.valor_inscricao,
            status=i.status
        ))

    # Ordena a lista combinada pela data, mais recentes primeiro
    pendencias.sort(key=lambda x: x.data_vencimento, reverse=True)
    
    return pendencias