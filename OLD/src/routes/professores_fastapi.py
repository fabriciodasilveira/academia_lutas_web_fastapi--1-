# -*- coding: utf-8 -*-
"""
Rotas FastAPI para o CRUD de Professores.
"""

import os
import shutil
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import logging

from src.database import get_db
from src.models.professor import Professor
from src.schemas.professor import ProfessorCreate, ProfessorRead, ProfessorUpdate

# Configuração de diretórios - CORRIGIDO
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR_PROFESSORES = BASE_DIR / "src" / "static" / "uploads" / "professores"

# Garante que o diretório existe - CORRIGIDO
try:
    UPLOAD_DIR_PROFESSORES.mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(f"Erro ao criar diretório de uploads de professores: {e}")
    # Fallback para diretório temporário
    UPLOAD_DIR_PROFESSORES = Path("/tmp/academia_uploads/professores")
    UPLOAD_DIR_PROFESSORES.mkdir(parents=True, exist_ok=True)

router = APIRouter(
    tags=["Professores"],
    responses={404: {"description": "Não encontrado"}},
)

# --- Helper Function --- 
def save_upload_file(upload_file: UploadFile, destination: Path) -> None:
    """Salva um arquivo de upload no destino especificado."""
    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()

# --- CRUD Endpoints --- 

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
    observacoes: Optional[str] = Form(None),
    foto: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Cria um novo professor.
    Permite upload de foto opcional.
    """
    # Validação de CPF/Email único
    if cpf:
        db_prof_cpf = db.query(Professor).filter(Professor.cpf == cpf).first()
        if db_prof_cpf:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CPF já cadastrado")
    if email:
        db_prof_email = db.query(Professor).filter(Professor.email == email).first()
        if db_prof_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email já cadastrado")

    # Converte datas
    parsed_data_nascimento = None
    if data_nascimento:
        try:
            parsed_data_nascimento = datetime.strptime(data_nascimento, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de data de nascimento inválido. Use YYYY-MM-DD")
            
    parsed_data_contratacao = None
    if data_contratacao:
        try:
            parsed_data_contratacao = datetime.strptime(data_contratacao, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de data de contratação inválido. Use YYYY-MM-DD")

    professor_data = ProfessorCreate(
        nome=nome,
        cpf=cpf,
        data_nascimento=parsed_data_nascimento,
        telefone=telefone,
        email=email,
        endereco=endereco,
        especialidade=especialidade,
        formacao=formacao,
        data_contratacao=parsed_data_contratacao,
        observacoes=observacoes
    )

    db_professor = Professor(**professor_data.dict(exclude_unset=True))
    
    try:
        db.add(db_professor)
        db.commit()
        db.refresh(db_professor)
    except IntegrityError:
        db.rollback()
        if cpf and db.query(Professor).filter(Professor.cpf == cpf).first():
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CPF já cadastrado")
        if email and db.query(Professor).filter(Professor.email == email).first():
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email já cadastrado")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno ao salvar professor.")

    # Processa upload de foto
    if foto:
        base, ext = os.path.splitext(foto.filename)
        safe_base = "".join(c if c.isalnum() or c in ('_', '-') else '' for c in base)[:50]
        filename = f"{db_professor.id}_{safe_base}{ext}"
        file_location = UPLOAD_DIR_PROFESSORES / filename
        
        save_upload_file(foto, file_location)
        
        db_professor.foto = f"/static/uploads/professores/{filename}"
        db.commit()
        db.refresh(db_professor)

    return db_professor

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

@router.put("/{professor_id}", response_model=ProfessorRead)
def update_professor(
    professor_id: int,
    professor_update: ProfessorUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza os dados de um professor existente.
    """
    db_professor = db.query(Professor).filter(Professor.id == professor_id).first()
    if db_professor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professor não encontrado")

    update_data = professor_update.dict(exclude_unset=True)

    # Validação de CPF/Email único (se alterado)
    if "cpf" in update_data and update_data["cpf"] is not None:
        db_prof_cpf = db.query(Professor).filter(Professor.cpf == update_data["cpf"], Professor.id != professor_id).first()
        if db_prof_cpf:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CPF já cadastrado para outro professor")
    if "email" in update_data and update_data["email"] is not None:
        db_prof_email = db.query(Professor).filter(Professor.email == update_data["email"], Professor.id != professor_id).first()
        if db_prof_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email já cadastrado para outro professor")

    # Converte datas se presentes nos dados de atualização
    if "data_nascimento" in update_data and isinstance(update_data["data_nascimento"], str):
         try:
            update_data["data_nascimento"] = datetime.strptime(update_data["data_nascimento"], "%Y-%m-%d").date()
         except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de data de nascimento inválido. Use YYYY-MM-DD")
            
    if "data_contratacao" in update_data and isinstance(update_data["data_contratacao"], str):
         try:
            update_data["data_contratacao"] = datetime.strptime(update_data["data_contratacao"], "%Y-%m-%d").date()
         except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de data de contratação inválido. Use YYYY-MM-DD")

    for key, value in update_data.items():
        setattr(db_professor, key, value)

    try:
        db.commit()
        db.refresh(db_professor)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Erro ao atualizar professor. Verifique os dados únicos (CPF/Email).")
        
    return db_professor

@router.post("/{professor_id}/foto", response_model=ProfessorRead)
def upload_professor_foto(
    professor_id: int,
    foto: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Faz upload ou atualiza a foto de um professor existente.
    """
    db_professor = db.query(Professor).filter(Professor.id == professor_id).first()
    if db_professor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professor não encontrado")

    # Remove foto anterior se existir - CORRIGIDO
    if db_professor.foto:
        old_foto_path = BASE_DIR / db_professor.foto.lstrip('/')
        if old_foto_path.exists():
            try:
                old_foto_path.unlink()
            except OSError as e:
                print(f"Erro ao remover foto antiga {old_foto_path}: {e}")

    # Salva a nova foto - CORRIGIDO
    base, ext = os.path.splitext(foto.filename)
    safe_base = "".join(c if c.isalnum() or c in ('_', '-') else '' for c in base)[:50]
    filename = f"{db_professor.id}_{safe_base}{ext}"
    file_location = UPLOAD_DIR_PROFESSORES / filename
    
    save_upload_file(foto, file_location)
    
    # Atualiza o caminho da foto no banco
    db_professor.foto = f"/static/uploads/professores/{filename}"
    db.commit()
    db.refresh(db_professor)
    
    return db_professor

@router.delete("/{professor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_professor(professor_id: int, db: Session = Depends(get_db)):
    """
    Exclui um professor.
    """
    db_professor = db.query(Professor).filter(Professor.id == professor_id).first()
    if db_professor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professor não encontrado")

    # Remove a foto se existir - CORRIGIDO
    if db_professor.foto:
        foto_path = BASE_DIR / db_professor.foto.lstrip('/')
        if foto_path.exists():
             try:
                foto_path.unlink()
             except OSError as e:
                print(f"Erro ao remover foto {foto_path}: {e}")

    db.delete(db_professor)
    db.commit()
    return None