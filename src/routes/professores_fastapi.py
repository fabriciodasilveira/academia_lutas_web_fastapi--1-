

# -*- coding: utf-8 -*-
"""
Rotas FastAPI para o CRUD de Professores.
"""
import os
import shutil
from typing import List, Optional
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

# Imports para o Armazenamento Externo
import boto3
from botocore.client import Config

from src.database import get_db
from src.models.professor import Professor
from src.schemas.professor import ProfessorCreate, ProfessorRead, ProfessorUpdate
from src.auth import get_admin_or_gerente
from src.models.usuario import Usuario as models_usuario

router = APIRouter(
    tags=["Professores"],
    responses={404: {"description": "Não encontrado"}},
)


BASE_DIR = Path(__file__).resolve().parent.parent

@router.post("", response_model=ProfessorRead, status_code=status.HTTP_201_CREATED)
def create_professor(
    nome: str = Form(...),
    cpf: Optional[str] = Form(None),
    data_nascimento: Optional[str] = Form(None),
    telefone: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    endereco: Optional[str] = Form(None),
    especialidade: Optional[str] = Form(None),
    formacao: Optional[str] = Form(None),
    data_contratacao: Optional[str] = Form(None),
    salario: Optional[float] = Form(None),
    observacoes: Optional[str] = Form(None),
    foto: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Cria um novo professor com upload de foto para o R2.
    """
    # ... (validações de CPF/Email) ...

    parsed_data_nascimento = None
    if data_nascimento:
        try:
            parsed_data_nascimento = datetime.strptime(data_nascimento, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de data de nascimento inválido.")

    parsed_data_contratacao = None
    if data_contratacao:
        try:
            parsed_data_contratacao = datetime.strptime(data_contratacao, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de data de contratação inválido.")

    professor_data = ProfessorCreate(
        nome=nome, cpf=cpf, data_nascimento=parsed_data_nascimento, telefone=telefone, email=email,
        endereco=endereco, especialidade=especialidade, formacao=formacao,
        data_contratacao=parsed_data_contratacao, salario=salario, observacoes=observacoes
    )

    db_professor = Professor(**professor_data.dict(exclude_unset=True))
    db.add(db_professor)
    db.commit()
    db.refresh(db_professor)

    if foto and foto.filename:
        s3_endpoint_url = os.getenv("S3_ENDPOINT_URL")
        s3_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        s3_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        s3_bucket_name = os.getenv("S3_BUCKET_NAME")
        public_bucket_url = os.getenv("PUBLIC_BUCKET_URL")

        if not all([s3_endpoint_url, s3_access_key_id, s3_secret_access_key, s3_bucket_name, public_bucket_url]):
            raise HTTPException(status_code=500, detail="Configuração de armazenamento na nuvem incompleta.")

        try:
            s3_client = boto3.client('s3', endpoint_url=s3_endpoint_url, aws_access_key_id=s3_access_key_id, aws_secret_access_key=s3_secret_access_key, region_name="auto")
            safe_filename = f"professor_{db_professor.id}_{datetime.utcnow().timestamp()}_{foto.filename.replace(' ', '_')}"
            s3_client.upload_fileobj(foto.file, s3_bucket_name, safe_filename, ExtraArgs={'ContentType': foto.content_type})
            db_professor.foto = f"{public_bucket_url.rstrip('/')}/{safe_filename}"
            db.commit()
            db.refresh(db_professor)
        except Exception as e:
            logging.error(f"Erro no upload para o R2 (professor): {e}")
            raise HTTPException(status_code=500, detail="Falha ao fazer upload da foto.")

    return db_professor

@router.put("/{professor_id}", response_model=ProfessorRead)
def update_professor(
    professor_id: int,
    db: Session = Depends(get_db),
    # Formulário de dados
    nome: Optional[str] = Form(None),
    cpf: Optional[str] = Form(None),
    data_nascimento: Optional[str] = Form(None),
    telefone: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    endereco: Optional[str] = Form(None),
    especialidade: Optional[str] = Form(None),
    formacao: Optional[str] = Form(None),
    data_contratacao: Optional[str] = Form(None),
    salario: Optional[float] = Form(None),
    observacoes: Optional[str] = Form(None),
    foto: Optional[UploadFile] = File(None)
):
    """
    Atualiza um professor existente, com upload de foto para o R2.
    """
    db_professor = db.query(Professor).filter(Professor.id == professor_id).first()
    if not db_professor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professor não encontrado")

    update_data = {
        "nome": nome, "cpf": cpf, "telefone": telefone, "email": email, "endereco": endereco,
        "especialidade": especialidade, "formacao": formacao, "salario": salario, "observacoes": observacoes
    }
    for key, value in update_data.items():
        if value is not None:
            setattr(db_professor, key, value)
            
    if data_nascimento:
        try:
            db_professor.data_nascimento = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            pass
    if data_contratacao:
        try:
            db_professor.data_contratacao = datetime.strptime(data_contratacao, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            pass

    if foto and foto.filename:
        s3_endpoint_url = os.getenv("S3_ENDPOINT_URL")
        s3_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        s3_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        s3_bucket_name = os.getenv("S3_BUCKET_NAME")
        public_bucket_url = os.getenv("PUBLIC_BUCKET_URL")

        if not all([s3_endpoint_url, s3_access_key_id, s3_secret_access_key, s3_bucket_name, public_bucket_url]):
            raise HTTPException(status_code=500, detail="Configuração de armazenamento na nuvem incompleta.")

        try:
            s3_client = boto3.client('s3', endpoint_url=s3_endpoint_url, aws_access_key_id=s3_access_key_id, aws_secret_access_key=s3_secret_access_key, region_name="auto")
            safe_filename = f"professor_{db_professor.id}_{datetime.utcnow().timestamp()}_{foto.filename.replace(' ', '_')}"
            s3_client.upload_fileobj(foto.file, s3_bucket_name, safe_filename, ExtraArgs={'ContentType': foto.content_type})
            db_professor.foto = f"{public_bucket_url.rstrip('/')}/{safe_filename}"
        except Exception as e:
            logging.error(f"Erro no upload para o R2 (professor): {e}")
            raise HTTPException(status_code=500, detail="Falha ao fazer upload da foto.")

    db.commit()
    db.refresh(db_professor)
    return db_professor

# --- SUAS OUTRAS ROTAS DE PROFESSOR (read_professores, etc.) PERMANECEM AQUI SEM ALTERAÇÃO ---
# ... (deixe o resto das funções como estão)
@router.get("", response_model=List[ProfessorRead])
def read_professores(
    skip: int = 0,
    limit: int = 100,
    nome: Optional[str] = None,
    especialidade: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Lista professores com filtros opcionais.
    """
    query = db.query(Professor)
    if nome:
        query = query.filter(Professor.nome.ilike(f"%{nome}%"))
    if especialidade:
        query = query.filter(Professor.especialidade.ilike(f"%{especialidade}%"))
        
    professores = query.order_by(Professor.nome).offset(skip).limit(limit).all()
    return professores

@router.get("/{professor_id}", response_model=ProfessorRead)
def read_professor(professor_id: int, db: Session = Depends(get_db)):
    """
    Obtém os detalhes de um professor específico pelo ID.
    """
    db_professor = db.query(Professor).filter(Professor.id == professor_id).first()
    if db_professor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professor não encontrado")
    return db_professor


@router.delete("/{professor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_professor(professor_id: int, db: Session = Depends(get_db), current_user: models_usuario = Depends(get_admin_or_gerente) ):
    """
    Exclui um professor.
    """
    
    db_professor = db.query(Professor).filter(Professor.id == professor_id).first()
    if db_professor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professor não encontrado")

    # Remove a foto se existir - CORRIGIDO
    if db_professor.foto:
        if "r2.dev" not in db_professor.foto: # Deleta apenas se for arquivo local
            foto_path = Path(str(BASE_DIR) + db_professor.foto)
            if foto_path.exists():
                try:
                    foto_path.unlink()
                except OSError as e:
                    print(f"Erro ao remover foto {foto_path}: {e}")

    db.delete(db_professor)
    db.commit()
    return None