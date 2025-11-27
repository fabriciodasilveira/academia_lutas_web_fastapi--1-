from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile, Response
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import shutil
from pathlib import Path
import logging
import os
import boto3
from botocore.client import Config
from src import auth
from pydantic import BaseModel, Field # Garanta que BaseModel e Field estão importados

from src import database, models, auth
from src.schemas import portal_aluno as schemas_portal
from src.schemas import aluno as schemas_aluno
from src.models.mensalidade import Mensalidade
from src.schemas.mensalidade import MensalidadeRead
from src.models.inscricao import Inscricao
from src.schemas.inscricao import InscricaoRead
from src.schemas.evento import EventoRead as SchemasEventoRead
from src.models.evento import Evento
from src.schemas.portal_aluno import PendenciaFinanceira
from src.models.matricula import Matricula
from src.schemas.matricula import MatriculaRead
from src.image_utils import process_avatar_image
from sqlalchemy.orm import joinedload
from src.schemas import portal_aluno as schemas_portal



router = APIRouter(
    prefix="/api/v1/portal",
    tags=["Portal do Aluno"]
)

@router.post("/register", response_model=schemas_aluno.AlunoRead, status_code=status.HTTP_201_CREATED)
def register_aluno(aluno_data: schemas_portal.AlunoRegistration, db: Session = Depends(database.get_db)):
    """
    Cria um novo Aluno E um novo Usuário (com username).
    """
    # Verifica se o USERNAME já existe
    db_user_check = db.query(models.usuario.Usuario).filter(models.usuario.Usuario.username == aluno_data.username).first()
    if db_user_check:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este nome de usuário já está em uso."
        )

    # Verifica se o EMAIL já existe
    db_email_check = auth.get_user(db, email=aluno_data.email)
    if db_email_check:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este email já está cadastrado no sistema."
        )
    
    hashed_password = auth.get_password_hash(aluno_data.password)
    
    # Cria o novo Usuário com username
    new_user = models.usuario.Usuario(
        username=aluno_data.username, # <--- NOVO
        email=aluno_data.email,
        nome=aluno_data.nome,
        hashed_password=hashed_password,
        role="aluno"
    )
    
    # Cria o novo Aluno
    new_aluno = models.aluno.Aluno(
        nome=aluno_data.nome,
        email=aluno_data.email,
        telefone=aluno_data.telefone,
        data_nascimento=aluno_data.data_nascimento,
        usuario=new_user # Vincula o usuário ao aluno
    )
    
    try:
        # Adiciona os dois
        db.add(new_user)
        db.add(new_aluno)
        db.commit()
        db.refresh(new_user)
        db.refresh(new_aluno)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro ao criar o usuário: {e}"
        )
    return new_aluno

@router.get("/me", response_model=schemas_aluno.AlunoRead)
def get_current_aluno_profile(
    current_user: models.usuario.Usuario = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != "aluno":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")

    # --- LÓGICA DE CONTA FAMILIAR ---
    # 1. Busca TODOS os perfis de aluno vinculados a este login
    alunos_vinculados = db.query(models.aluno.Aluno).options(
        joinedload(models.aluno.Aluno.matriculas)
    ).filter(models.aluno.Aluno.usuario_id == current_user.id).order_by(models.aluno.Aluno.id.asc()).all() # Ordena pelo ID (mais antigo primeiro)

    if not alunos_vinculados:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhum perfil de aluno encontrado para este usuário.")

    # 2. Seleciona o primeiro perfil (o "principal" da conta) para exibir no PWA
    aluno_profile = alunos_vinculados[0]
    # --- FIM DA LÓGICA ---

    # Lógica de status (permanece a mesma)
    status_geral = "Inativo"
    if aluno_profile.matriculas:
        if any(matricula.ativa for matricula in aluno_profile.matriculas):
            status_geral = "Ativo"
    
    aluno_data = schemas_aluno.AlunoRead.from_orm(aluno_profile)
    aluno_data.status_geral = status_geral

    return aluno_data


# --- FUNÇÃO ATUALIZADA E COMPLETA ---
@router.put("/me", response_model=schemas_aluno.AlunoRead)
def update_current_aluno_profile(
    db: Session = Depends(database.get_db),
    current_user: models.usuario.Usuario = Depends(auth.get_current_active_user),
    nome: str = Form(...),
    cpf: Optional[str] = Form(None),
    telefone: Optional[str] = Form(None),
    data_nascimento: Optional[str] = Form(None),
    endereco: Optional[str] = Form(None),
    observacoes: Optional[str] = Form(None),
    foto: Optional[UploadFile] = File(None),
    nome_responsavel: Optional[str] = Form(None),
    cpf_responsavel: Optional[str] = Form(None),
    parentesco_responsavel: Optional[str] = Form(None),
    telefone_responsavel: Optional[str] = Form(None),
    email_responsavel: Optional[str] = Form(None)
):
    if current_user.role != "aluno":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")
    db_aluno = db.query(models.aluno.Aluno).filter(models.aluno.Aluno.usuario_id == current_user.id).first()
    if not db_aluno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de aluno não encontrado.")

    update_data = {
        "nome": nome, "cpf": cpf, "telefone": telefone, "endereco": endereco, "observacoes": observacoes,
        "nome_responsavel": nome_responsavel, "cpf_responsavel": cpf_responsavel, "parentesco_responsavel": parentesco_responsavel,
        "telefone_responsavel": telefone_responsavel, "email_responsavel": email_responsavel
    }
    for key, value in update_data.items():
        setattr(db_aluno, key, value)
    
    if data_nascimento:
        try:
            db_aluno.data_nascimento = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
        except ValueError: pass

    if foto and foto.filename:
        processed_image, mime_type = process_avatar_image(foto.file)
        if processed_image:
            s3_endpoint_url = os.getenv("S3_ENDPOINT_URL")
            s3_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
            s3_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
            s3_bucket_name = os.getenv("S3_BUCKET_NAME")
            public_bucket_url = os.getenv("PUBLIC_BUCKET_URL")

            if not all([s3_endpoint_url, s3_access_key_id, s3_secret_access_key, s3_bucket_name, public_bucket_url]):
                raise HTTPException(status_code=500, detail="Configuração de armazenamento na nuvem incompleta.")

            try:
                s3_client = boto3.client('s3', endpoint_url=s3_endpoint_url, aws_access_key_id=s3_access_key_id, aws_secret_access_key=s3_secret_access_key, region_name="auto")
                base_filename, _ = os.path.splitext(foto.filename)
                safe_filename = f"aluno_{db_aluno.id}_{datetime.utcnow().timestamp()}_{base_filename.replace(' ', '_')}.jpg"
                s3_client.upload_fileobj(processed_image, s3_bucket_name, safe_filename, ExtraArgs={'ContentType': mime_type})
                db_aluno.foto = f"{public_bucket_url.rstrip('/')}/{safe_filename}"
            except Exception as e:
                logging.error(f"Erro no upload para o R2 (portal): {e}")
                raise HTTPException(status_code=500, detail="Falha ao fazer upload da foto.")

    db.commit()
    db.refresh(db_aluno)
    return db_aluno

# --- SUAS OUTRAS ROTAS DO PORTAL (sem alteração) ---
@router.get("/matriculas", response_model=List[MatriculaRead])
def get_aluno_matriculas(
    current_user: models.usuario.Usuario = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != "aluno":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")
    aluno_profile = db.query(models.aluno.Aluno).filter(models.aluno.Aluno.usuario_id == current_user.id).first()
    if not aluno_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de aluno não encontrado.")
    matriculas = db.query(Matricula).filter(
        Matricula.aluno_id == aluno_profile.id,
        Matricula.ativa == True
    ).order_by(Matricula.data_matricula.desc()).all()
    return matriculas

@router.get("/pendencias", response_model=List[PendenciaFinanceira])
def get_aluno_pendencias_financeiras(
    current_user: models.usuario.Usuario = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != "aluno":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")
    aluno_profile = db.query(models.aluno.Aluno).filter(models.aluno.Aluno.usuario_id == current_user.id).first()
    if not aluno_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de aluno não encontrado.")
    pendencias = []
    mensalidades = db.query(Mensalidade).filter(Mensalidade.aluno_id == aluno_profile.id).all()
    for m in mensalidades:
        pendencias.append(PendenciaFinanceira(
            tipo='mensalidade', id=m.id, descricao=f"Mensalidade - {m.plano.nome}",
            data_vencimento=m.data_vencimento, valor=m.valor, status=m.status
        ))
    inscricoes = db.query(Inscricao).filter(Inscricao.aluno_id == aluno_profile.id).all()
    for i in inscricoes:
        pendencias.append(PendenciaFinanceira(
            tipo='inscricao', id=i.id, descricao=f"Inscrição - {i.evento.nome}",
            data_vencimento=i.evento.data_evento.date(), valor=i.evento.valor_inscricao, status=i.status
        ))
    pendencias.sort(key=lambda x: x.data_vencimento, reverse=True)
    return pendencias

@router.get("/eventos", response_model=List[SchemasEventoRead])
def get_portal_eventos(
    current_user: models.usuario.Usuario = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    aluno_profile = db.query(models.aluno.Aluno).filter(models.aluno.Aluno.usuario_id == current_user.id).first()
    if not aluno_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de aluno não encontrado.")
    todos_eventos = db.query(Evento).order_by(Evento.data_evento.desc()).all()
    inscricoes_aluno = db.query(Inscricao.evento_id).filter(Inscricao.aluno_id == aluno_profile.id).all()
    eventos_inscritos_ids = {inscricao.evento_id for inscricao in inscricoes_aluno}
    eventos_com_status = []
    for evento in todos_eventos:
        evento_data = SchemasEventoRead.from_orm(evento)
        evento_data.is_inscrito = evento.id in eventos_inscritos_ids
        eventos_com_status.append(evento_data)
    return eventos_com_status

@router.post("/eventos/{evento_id}/inscrever", response_model=InscricaoRead)
def inscrever_aluno_evento(
    evento_id: int,
    current_user: models.usuario.Usuario = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    aluno_profile = db.query(models.aluno.Aluno).filter(models.aluno.Aluno.usuario_id == current_user.id).first()
    if not aluno_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de aluno não encontrado.")
    db_evento = db.query(Evento).filter(Evento.id == evento_id).first()
    if not db_evento:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    db_inscricao_existente = db.query(Inscricao).filter(Inscricao.aluno_id == aluno_profile.id, Inscricao.evento_id == evento_id).first()
    if db_inscricao_existente:
         raise HTTPException(status_code=400, detail="Você já está inscrito neste evento.")
    if db_evento.capacidade > 0 and len(db_evento.inscricoes) >= db_evento.capacidade:
        raise HTTPException(status_code=400, detail="Evento lotado")
    db_inscricao = Inscricao(aluno_id=aluno_profile.id, evento_id=evento_id)
    if db_evento.valor_inscricao == 0:
        db_inscricao.status = "pago"
        db_inscricao.metodo_pagamento = "Gratuito"
    db.add(db_inscricao)
    db.commit()
    db.refresh(db_inscricao)
    return db_inscricao

class PasswordUpdate(BaseModel):
    current_password: str = Field(..., title="Senha Atual")
    new_password: str = Field(..., min_length=6, title="Nova Senha")
    
    
@router.put("/me/update-password", status_code=status.HTTP_204_NO_CONTENT)
def update_current_aluno_password(
    password_data: PasswordUpdate,
    current_user: models.usuario.Usuario = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    """
    Permite ao aluno logado atualizar sua própria senha.
    """
    if not auth.verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A senha atual está incorreta."
        )
    
    current_user.hashed_password = auth.get_password_hash(password_data.new_password)
    db.add(current_user)
    db.commit()
    
    # Agora retorna o Response correto do FastAPI
    return Response(status_code=status.HTTP_204_NO_CONTENT)