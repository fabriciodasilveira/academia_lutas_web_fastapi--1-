# -*- coding: utf-8 -*-
import os
import shutil
from typing import List, Optional
from pathlib import Path
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session, joinedload, selectinload # selectinload ainda é útil em read_aluno
from sqlalchemy.exc import IntegrityError
import logging

import boto3
from botocore.client import Config

from src.image_utils import process_avatar_image
from src.database import get_db
from src.models.aluno import Aluno
from src.schemas.aluno import AlunoCreate, AlunoRead, AlunoUpdate, AlunoPaginated
from src.models.matricula import Matricula
from sqlalchemy import func
from src.models.mensalidade import Mensalidade
from src.models.usuario import Usuario
from src import auth

router = APIRouter(
    tags=["Alunos"],
    responses={404: {"description": "Aluno não encontrado"}},
)

# --- CREATE ALUNO (sem alterações aqui) ---
@router.post("", response_model=AlunoRead, status_code=status.HTTP_201_CREATED)
def create_aluno(
    nome: str = Form(...), email: Optional[str] = Form(None), data_nascimento: Optional[str] = Form(None),
    cpf: Optional[str] = Form(None), telefone: Optional[str] = Form(None), endereco: Optional[str] = Form(None),
    observacoes: Optional[str] = Form(None), foto: Optional[UploadFile] = File(None), nome_responsavel: Optional[str] = Form(None),
    cpf_responsavel: Optional[str] = Form(None), parentesco_responsavel: Optional[str] = Form(None),
    telefone_responsavel: Optional[str] = Form(None), email_responsavel: Optional[str] = Form(None),
    responsavel_aluno_id: Optional[int] = Form(None), db: Session = Depends(get_db)
):
    # ... (código existente create_aluno) ...
    new_user = None; hashed_password = None; default_password = None
    if responsavel_aluno_id:
        db_responsavel = db.query(Aluno).filter(Aluno.id == responsavel_aluno_id).first()
        if not db_responsavel: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Resp ID {responsavel_aluno_id} não encontrado.")
        if db_responsavel.responsavel_aluno_id: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dependente não pode ser resp.")
    if email and not responsavel_aluno_id:
        db_user_check = auth.get_user(db, email=email)
        if db_user_check: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Email {email} já em uso.")
        try: partes_nome = nome.strip().split(); ano_atual = datetime.now().year; ultimo_sobrenome = partes_nome[-1] if len(partes_nome) > 1 else partes_nome[0]; default_password = f"{ultimo_sobrenome.lower()}@{ano_atual}"
        except: default_password = f"senha@{ano_atual}"
        hashed_password = auth.get_password_hash(default_password)
        new_user = Usuario(email=email, nome=nome, hashed_password=hashed_password, role="aluno")
    parsed_data_nascimento = None
    if data_nascimento: 
        try: 
            parsed_data_nascimento = date.fromisoformat(data_nascimento); 
        except ValueError: 
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato data inválido (YYYY-MM-DD)")
    db_aluno = Aluno( nome=nome, email=email, data_nascimento=parsed_data_nascimento, cpf=cpf, telefone=telefone, endereco=endereco, observacoes=observacoes, nome_responsavel=nome_responsavel, cpf_responsavel=cpf_responsavel, parentesco_responsavel=parentesco_responsavel, telefone_responsavel=telefone_responsavel, email_responsavel=email_responsavel, responsavel_aluno_id=responsavel_aluno_id, usuario=new_user )
    try:
        if new_user: db.add(new_user)
        db.add(db_aluno); db.commit();
        if new_user: db.refresh(new_user); logging.info(f"Usuário {new_user.id} criado.")
        db.refresh(db_aluno); logging.info(f"Aluno {db_aluno.id} criado. Resp ID: {responsavel_aluno_id}. Senha: {default_password if default_password else 'N/A'}")
    except IntegrityError as e: db.rollback(); logging.error(f"Erro Integridade: {e}"); raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Erro DB: Dados únicos.")
    except Exception as e: db.rollback(); logging.error(f"Erro Inesperado: {e}"); raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno.")
    if foto and foto.filename:
        processed_image, mime_type = process_avatar_image(foto.file)
        if processed_image:
            s3_endpoint_url=os.getenv("S3_ENDPOINT_URL"); s3_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"); s3_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"); s3_bucket_name=os.getenv("S3_BUCKET_NAME"); public_bucket_url=os.getenv("PUBLIC_BUCKET_URL")
            if not all([s3_endpoint_url, s3_access_key_id, s3_secret_access_key, s3_bucket_name, public_bucket_url]): logging.warning(f"Aluno {db_aluno.id} criado, foto não salva (config S3).")
            else:
                try: s3_client = boto3.client('s3', endpoint_url=s3_endpoint_url, aws_access_key_id=s3_access_key_id, aws_secret_access_key=s3_secret_access_key, region_name="auto"); base_filename, _ = os.path.splitext(foto.filename); safe_filename = f"aluno_{db_aluno.id}_{datetime.utcnow().timestamp()}_{base_filename.replace(' ', '_')}.jpg"; s3_client.upload_fileobj(processed_image, s3_bucket_name, safe_filename, ExtraArgs={'ContentType': mime_type}); db_aluno.foto = f"{public_bucket_url.rstrip('/')}/{safe_filename}"; db.commit(); db.refresh(db_aluno); logging.info(f"Foto aluno {db_aluno.id} salva.")
                except Exception as e: logging.error(f"Erro upload R2 (create aluno {db_aluno.id}): {e}")
    db_aluno_loaded = db.query(Aluno).options(selectinload(Aluno.dependentes), joinedload(Aluno.responsavel)).filter(Aluno.id == db_aluno.id).first()
    return db_aluno_loaded


# --- UPDATE ALUNO (sem alterações aqui) ---
@router.put("/{aluno_id}", response_model=AlunoRead)
def update_aluno(
    aluno_id: int, db: Session = Depends(get_db), nome: Optional[str] = Form(None), email: Optional[str] = Form(None),
    data_nascimento: Optional[str] = Form(None), cpf: Optional[str] = Form(None), telefone: Optional[str] = Form(None),
    endereco: Optional[str] = Form(None), observacoes: Optional[str] = Form(None), foto: Optional[UploadFile] = File(None),
    nome_responsavel: Optional[str] = Form(None), cpf_responsavel: Optional[str] = Form(None), parentesco_responsavel: Optional[str] = Form(None),
    telefone_responsavel: Optional[str] = Form(None), email_responsavel: Optional[str] = Form(None), responsavel_aluno_id: Optional[int] = Form(None)
):
    # ... (código existente update_aluno) ...
    db_aluno = db.query(Aluno).options(joinedload(Aluno.usuario)).filter(Aluno.id == aluno_id).first()
    if not db_aluno: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado")
    if responsavel_aluno_id is not None and responsavel_aluno_id != db_aluno.responsavel_aluno_id:
         if responsavel_aluno_id == db_aluno.id: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Aluno não pode ser resp. de si mesmo.")
         db_responsavel = db.query(Aluno).filter(Aluno.id == responsavel_aluno_id).first()
         if not db_responsavel: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Resp ID {responsavel_aluno_id} não encontrado.")
         if db_responsavel.responsavel_aluno_id: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dependente não pode ser resp.")
         db_aluno.responsavel_aluno_id = responsavel_aluno_id
    elif responsavel_aluno_id is None and db_aluno.responsavel_aluno_id is not None: db_aluno.responsavel_aluno_id = None
    update_data = { "nome": nome, "cpf": cpf, "telefone": telefone, "endereco": endereco, "observacoes": observacoes, "nome_responsavel": nome_responsavel, "cpf_responsavel": cpf_responsavel, "parentesco_responsavel": parentesco_responsavel, "telefone_responsavel": telefone_responsavel, "email_responsavel": email_responsavel }
    for key, value in update_data.items():
        if value is not None: setattr(db_aluno, key, value)
    if data_nascimento: 
        try: db_aluno.data_nascimento = date.fromisoformat(data_nascimento); 
        except: pass
    if email is not None and db_aluno.email != email:
        if db_aluno.usuario:
             existing_user = auth.get_user(db, email=email)
             if existing_user and existing_user.id != db_aluno.usuario_id: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Email {email} já em uso.")
             db_aluno.email = email; db_aluno.usuario.email = email; logging.warning(f"Email aluno/usuário {aluno_id} alterado para {email}.")
        elif not db_aluno.usuario: db_aluno.email = email; logging.info(f"Email dependente {aluno_id} atualizado para {email}.")
    if nome is not None and db_aluno.usuario and db_aluno.usuario.nome != nome: db_aluno.usuario.nome = nome
    if foto and foto.filename:
        processed_image, mime_type = process_avatar_image(foto.file)
        if processed_image:
             s3_endpoint_url=os.getenv("S3_ENDPOINT_URL"); s3_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"); s3_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"); s3_bucket_name=os.getenv("S3_BUCKET_NAME"); public_bucket_url=os.getenv("PUBLIC_BUCKET_URL")
             if not all([s3_endpoint_url, s3_access_key_id, s3_secret_access_key, s3_bucket_name, public_bucket_url]): logging.warning(f"Aluno {aluno_id} atualizado, foto não salva (config S3).")
             else:
                  try: s3_client = boto3.client('s3', endpoint_url=s3_endpoint_url, aws_access_key_id=s3_access_key_id, aws_secret_access_key=s3_secret_access_key, region_name="auto"); base_filename, _ = os.path.splitext(foto.filename); safe_filename = f"aluno_{db_aluno.id}_{datetime.utcnow().timestamp()}_{base_filename.replace(' ', '_')}.jpg"; s3_client.upload_fileobj(processed_image, s3_bucket_name, safe_filename, ExtraArgs={'ContentType': mime_type}); db_aluno.foto = f"{public_bucket_url.rstrip('/')}/{safe_filename}"; logging.info(f"Foto aluno {aluno_id} atualizada.")
                  except Exception as e: logging.error(f"Erro upload R2 (update aluno {aluno_id}): {e}")
    try: db.commit(); db.refresh(db_aluno)
    except Exception as e: db.rollback(); logging.error(f"Erro commit update aluno {aluno_id}: {e}"); raise HTTPException(status_code=500, detail="Erro ao salvar.")
    db_aluno_loaded = db.query(Aluno).options(selectinload(Aluno.dependentes), joinedload(Aluno.responsavel)).filter(Aluno.id == db_aluno.id).first()
    return db_aluno_loaded


# --- READ ALUNOS (CORRIGIDO) ---
@router.get("", response_model=AlunoPaginated)
def read_alunos(
    skip: int = 0, limit: int = 20, nome: Optional[str] = None, cpf: Optional[str] = None,
    status: Optional[str] = None, db: Session = Depends(get_db)
):
    query = db.query(Aluno).options(
        joinedload(Aluno.matriculas),
        # selectinload(Aluno.dependentes), # <<< REMOVIDO PARA EVITAR O ERRO
        joinedload(Aluno.responsavel)
    )
    # ... (filtros de nome, cpf, status permanecem iguais) ...
    if nome: query = query.filter(Aluno.nome.ilike(f"%{nome}%"))
    if cpf: query = query.filter(Aluno.cpf == cpf)
    if status:
        subquery = db.query(Matricula.aluno_id).filter(Matricula.ativa == True).distinct()
        if status == 'ativo': query = query.filter(Aluno.id.in_(subquery))
        elif status == 'inativo': query = query.filter(Aluno.id.notin_(subquery))
        
    total = query.count()
    alunos_paginados = query.order_by(Aluno.nome).offset(skip).limit(limit).all()

    # Monta a resposta - Pydantic/SQLAlchemy lidarão com 'dependentes' (lazy load ou vazio)
    response_alunos = []
    for aluno in alunos_paginados:
        aluno_read = AlunoRead.from_orm(aluno)
        aluno_read.status_geral = "Ativo" if any(m.ativa for m in aluno.matriculas) else "Inativo"
        response_alunos.append(aluno_read)

    return {"total": total, "alunos": response_alunos}


# --- READ ALUNO (Mantém selectinload aqui, pois é para um único aluno) ---
@router.get("/{aluno_id}", response_model=AlunoRead)
def read_aluno(aluno_id: int, db: Session = Depends(get_db)):
    db_aluno = db.query(Aluno).options(
        selectinload(Aluno.dependentes), # Mantém aqui para detalhes
        joinedload(Aluno.responsavel),
        joinedload(Aluno.matriculas)
    ).filter(Aluno.id == aluno_id).first()
    if db_aluno is None: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado")
    aluno_data = AlunoRead.from_orm(db_aluno)
    aluno_data.status_geral = "Ativo" if any(m.ativa for m in db_aluno.matriculas) else "Inativo"
    return aluno_data


# --- DELETE ALUNO (sem alterações) ---
@router.delete("/{aluno_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_aluno(aluno_id: int, db: Session = Depends(get_db)):
    # ... (código existente delete_aluno) ...
    db_aluno = db.query(Aluno).options(joinedload(Aluno.usuario)).filter(Aluno.id == aluno_id).first()
    if db_aluno is None: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado")
    try: db.delete(db_aluno); db.commit(); logging.info(f"Aluno {aluno_id} excluído.")
    except Exception as e: db.rollback(); logging.error(f"Erro excluir aluno {aluno_id}: {e}"); raise HTTPException(status_code=500, detail=f"Erro excluir: {e}")
    return None

# --- OUTRAS ROTAS (histórico, status-detalhado) (sem alterações) ---
@router.get("/{aluno_id}/historico")
def get_aluno_historico(aluno_id: int, db: Session = Depends(get_db)):
    # ... (código existente) ...
    aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first();
    if not aluno: raise HTTPException(status_code=404, detail="Aluno não encontrado"); historico = []
    if aluno.data_cadastro: historico.append({"data": aluno.data_cadastro.isoformat(), "descricao": "Aluno cadastrado", "tipo": "cadastro"})
    matriculas = db.query(Matricula).options(joinedload(Matricula.turma), joinedload(Matricula.historico)).filter(Matricula.aluno_id == aluno_id).all()
    for m in matriculas:
        historico.append({"data": m.data_matricula.isoformat(), "descricao": f"Matriculado na turma '{m.turma.nome if m.turma else 'N/A'}'", "tipo": "matricula"})
        for evento_historico in m.historico: historico.append({"data": evento_historico.data_alteracao.isoformat(), "descricao": evento_historico.descricao, "tipo": "status_change"})
    historico.sort(key=lambda x: x['data'])
    return historico

@router.get("/{aluno_id}/status-detalhado")
def get_aluno_status_detalhado(aluno_id: int, db: Session = Depends(get_db)):
    # ... (código existente) ...
    aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first();
    if not aluno: raise HTTPException(status_code=404, detail="Aluno não encontrado")
    matricula_ativa = db.query(Matricula).filter(Matricula.aluno_id == aluno_id, Matricula.ativa == True).first()
    situacao_geral = "Ativo" if matricula_ativa else "Inativo"
    mensalidades_pendentes = db.query(func.sum(Mensalidade.valor)).filter(Mensalidade.aluno_id == aluno_id, Mensalidade.status == 'pendente').scalar() or 0.0
    status_mensalidade = "Em dia" if mensalidades_pendentes == 0 else "Pendente"
    return {"situacao_geral": situacao_geral, "status_mensalidade": status_mensalidade, "valor_pendente": mensalidades_pendentes}