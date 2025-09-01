# -*- coding: utf-8 -*-
"""
Rotas FastAPI para o CRUD de Alunos.
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

from src.database import get_db
from src.models.aluno import Aluno
from src.schemas.aluno import AlunoCreate, AlunoRead, AlunoUpdate

# Configuração de diretórios - CORRIGIDO
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads" / "alunos"

# Garante que o diretório existe - CORRIGIDO
try:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(f"Erro ao criar diretório de uploads: {e}")
    # Fallback para diretório temporário
    UPLOAD_DIR = Path("/tmp/academia_uploads/alunos")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(
    tags=["Alunos"],
    responses={404: {"description": "Aluno não encontrado"}},
)

# --- Helper Function --- 
def save_upload_file(upload_file: UploadFile, destination: Path) -> None:
    """Salva um arquivo de upload no destino especificado."""
    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
            logging.info(f"Arquivo salvo em: {destination}")
    finally:
        upload_file.file.close()

# --- CRUD Endpoints --- 

@router.post("", response_model=AlunoRead, status_code=status.HTTP_201_CREATED)
def create_aluno(
    nome: str = Form(...),
    data_nascimento: Optional[str] = Form(None),
    cpf: Optional[str] = Form(None),
    telefone: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    endereco: Optional[str] = Form(None),
    observacoes: Optional[str] = Form(None),
    foto: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Cria um novo aluno.
    Permite upload de foto opcional.
    """
    # Validação de CPF/Email único (se fornecido)
    if cpf:
        db_aluno_cpf = db.query(Aluno).filter(Aluno.cpf == cpf).first()
        if db_aluno_cpf:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="CPF já cadastrado"
            )
    if email:
        db_aluno_email = db.query(Aluno).filter(Aluno.email == email).first()
        if db_aluno_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Email já cadastrado"
            )

    # Converte data de nascimento se fornecida
    parsed_data_nascimento = None
    if data_nascimento:
        try:
            parsed_data_nascimento = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Formato de data inválido. Use YYYY-MM-DD"
            )

    aluno_data = AlunoCreate(
        nome=nome,
        data_nascimento=parsed_data_nascimento,
        cpf=cpf,
        telefone=telefone,
        email=email,
        endereco=endereco,
        observacoes=observacoes
    )

    db_aluno = Aluno(**aluno_data.dict(exclude_unset=True))
    db.add(db_aluno)
    db.commit()
    db.refresh(db_aluno)

    # Processa upload de foto se houver
    if foto:
        # Define um nome de arquivo seguro
        base, ext = os.path.splitext(foto.filename)
        safe_base = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in base)[:50]
        filename = f"{db_aluno.id}_{safe_base}{ext}"
        file_location = UPLOAD_DIR / filename
        
        save_upload_file(foto, file_location)
        
        # Atualiza o caminho da foto no banco
        db_aluno.foto = f"/static/uploads/alunos/{filename}"
        db.commit()
        db.refresh(db_aluno)

    return db_aluno

@router.get("", response_model=List[AlunoRead])
def read_alunos(
    skip: int = 0,
    limit: int = 100,
    nome: Optional[str] = None,
    cpf: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Lista alunos com filtros opcionais por nome e CPF.
    """
    query = db.query(Aluno)
    if nome:
        query = query.filter(Aluno.nome.ilike(f"%{nome}%"))
    if cpf:
        query = query.filter(Aluno.cpf == cpf)
    
    return query.order_by(Aluno.nome).offset(skip).limit(limit).all()

@router.get("/{aluno_id}", response_model=AlunoRead)
def read_aluno(aluno_id: int, db: Session = Depends(get_db)):
    """
    Obtém os detalhes de um aluno específico pelo ID.
    """
    db_aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
    if db_aluno is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Aluno não encontrado"
        )
    return db_aluno

@router.put("/{aluno_id}", response_model=AlunoRead)
def update_aluno(
    aluno_id: int,
    nome: Optional[str] = Form(None),
    data_nascimento: Optional[str] = Form(None),
    cpf: Optional[str] = Form(None),
    telefone: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    endereco: Optional[str] = Form(None),
    observacoes: Optional[str] = Form(None),
    foto: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Atualiza os dados de um aluno existente.
    Permite upload de foto opcional.
    """
    db_aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
    if db_aluno is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Aluno não encontrado"
        )

    # Validação de CPF/Email único (se alterado)
    if cpf is not None:
        db_aluno_cpf = db.query(Aluno).filter(
            Aluno.cpf == cpf, 
            Aluno.id != aluno_id
        ).first()
        if db_aluno_cpf:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="CPF já cadastrado para outro aluno"
            )
        db_aluno.cpf = cpf
    
    if email is not None:
        db_aluno_email = db.query(Aluno).filter(
            Aluno.email == email, 
            Aluno.id != aluno_id
        ).first()
        if db_aluno_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Email já cadastrado para outro aluno"
            )
        db_aluno.email = email

    # Atualiza outros campos
    if nome is not None:
        db_aluno.nome = nome
    if telefone is not None:
        db_aluno.telefone = telefone
    if endereco is not None:
        db_aluno.endereco = endereco
    if observacoes is not None:
        db_aluno.observacoes = observacoes

    # Converte e atualiza data de nascimento se fornecida
    if data_nascimento is not None:
        try:
            db_aluno.data_nascimento = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Formato de data inválido. Use YYYY-MM-DD"
            )

    # Processa upload de foto se houver
    if foto:
        # Valida se é uma imagem
        if not foto.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O arquivo deve ser uma imagem"
            )

        # Remove foto anterior se existir
        if db_aluno.foto:
            old_foto_path = BASE_DIR / db_aluno.foto.lstrip('/')
            if old_foto_path.exists():
                try:
                    old_foto_path.unlink()
                except OSError as e:
                    logging.warning(f"Erro ao remover foto antiga {old_foto_path}: {e}")

        # Salva a nova foto
        base, ext = os.path.splitext(foto.filename)
        safe_base = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in base)[:50]
        filename = f"{db_aluno.id}_{safe_base}{ext}"
        file_location = UPLOAD_DIR / filename
        
        save_upload_file(foto, file_location)
        
        # Atualiza o caminho da foto no banco
        db_aluno.foto = f"/static/uploads/alunos/{filename}"

    try:
        db.commit()
        db.refresh(db_aluno)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro ao atualizar aluno. Verifique os dados únicos (CPF/Email)."
        )
        
    return db_aluno

@router.post("/{aluno_id}/foto", response_model=AlunoRead)
def upload_aluno_foto(
    aluno_id: int,
    foto: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Faz upload ou atualiza a foto de um aluno existente.
    """
    try:
        db_aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
        if db_aluno is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Aluno não encontrado"
            )

        # Valida se é uma imagem
        if not foto.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O arquivo deve ser uma imagem"
            )

        # Remove foto anterior se existir
        if db_aluno.foto:
            old_foto_path = BASE_DIR / db_aluno.foto.lstrip('/')
            if old_foto_path.exists():
                try:
                    old_foto_path.unlink()
                except OSError as e:
                    logging.warning(f"Erro ao remover foto antiga {old_foto_path}: {e}")

        # Salva a nova foto
        base, ext = os.path.splitext(foto.filename)
        safe_base = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in base)[:50]
        filename = f"{db_aluno.id}_{safe_base}{ext}"
        file_location = UPLOAD_DIR / filename
        
        save_upload_file(foto, file_location)
        
        # Atualiza o caminho da foto no banco
        db_aluno.foto = f"/static/uploads/alunos/{filename}"
        db.commit()
        db.refresh(db_aluno)
        
        return db_aluno
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Erro ao processar upload de foto: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar a foto"
        )

@router.delete("/{aluno_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_aluno(aluno_id: int, db: Session = Depends(get_db)):
    """
    Exclui um aluno.
    """
    db_aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
    if db_aluno is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Aluno não encontrado"
        )

    # Remove a foto se existir - CORRIGIDO
    if db_aluno.foto:
        foto_path = BASE_DIR / db_aluno.foto.lstrip('/')
        if foto_path.exists():
            try:
                foto_path.unlink()
            except OSError as e:
                print(f"Erro ao remover foto {foto_path}: {e}")

    db.delete(db_aluno)
    db.commit()
    return None

# # -*- coding: utf-8 -*-
# """
# Rotas FastAPI para o CRUD de Alunos.
# """

# import os
# import shutil
# from typing import List, Optional
# from pathlib import Path
# from datetime import datetime
# from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
# from sqlalchemy.orm import Session
# from sqlalchemy.exc import IntegrityError
# import logging

# from src.database import get_db
# from src.models.aluno import Aluno
# from src.schemas.aluno import AlunoCreate, AlunoRead, AlunoUpdate

# # Configuração de diretórios - CORRIGIDO
# BASE_DIR = Path(__file__).resolve().parent.parent
# UPLOAD_DIR = BASE_DIR / "static" / "uploads" / "alunos"

# # Garante que o diretório existe - CORRIGIDO
# try:
#     UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
# except Exception as e:
#     print(f"Erro ao criar diretório de uploads: {e}")
#     # Fallback para diretório temporário
#     UPLOAD_DIR = Path("/tmp/academia_uploads/alunos")
#     UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# router = APIRouter(
#     tags=["Alunos"],
#     responses={404: {"description": "Aluno não encontrado"}},
# )

# # --- Helper Function --- 
# def save_upload_file(upload_file: UploadFile, destination: Path) -> None:
#     """Salva um arquivo de upload no destino especificado."""
#     try:
#         with destination.open("wb") as buffer:
#             shutil.copyfileobj(upload_file.file, buffer)
#             logging.info(f"Arquivo salvo em: {destination}")
#     finally:
#         upload_file.file.close()

# # --- CRUD Endpoints --- 

# @router.post("", response_model=AlunoRead, status_code=status.HTTP_201_CREATED)
# def create_aluno(
#     nome: str = Form(...),
#     data_nascimento: Optional[str] = Form(None),
#     cpf: Optional[str] = Form(None),
#     telefone: Optional[str] = Form(None),
#     email: Optional[str] = Form(None),
#     endereco: Optional[str] = Form(None),
#     observacoes: Optional[str] = Form(None),
#     foto: Optional[UploadFile] = File(None),
#     db: Session = Depends(get_db)
# ):
#     """
#     Cria um novo aluno.
#     Permite upload de foto opcional.
#     """
#     # Validação de CPF/Email único (se fornecido)
#     if cpf:
#         db_aluno_cpf = db.query(Aluno).filter(Aluno.cpf == cpf).first()
#         if db_aluno_cpf:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST, 
#                 detail="CPF já cadastrado"
#             )
#     if email:
#         db_aluno_email = db.query(Aluno).filter(Aluno.email == email).first()
#         if db_aluno_email:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST, 
#                 detail="Email já cadastrado"
#             )

#     # Converte data de nascimento se fornecida
#     parsed_data_nascimento = None
#     if data_nascimento:
#         try:
#             parsed_data_nascimento = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
#         except ValueError:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST, 
#                 detail="Formato de data inválido. Use YYYY-MM-DD"
#             )

#     aluno_data = AlunoCreate(
#         nome=nome,
#         data_nascimento=parsed_data_nascimento,
#         cpf=cpf,
#         telefone=telefone,
#         email=email,
#         endereco=endereco,
#         observacoes=observacoes
#     )

#     db_aluno = Aluno(**aluno_data.dict(exclude_unset=True))
#     db.add(db_aluno)
#     db.commit()
#     db.refresh(db_aluno)

#     # Processa upload de foto se houver
#     if foto:
#         # Define um nome de arquivo seguro
#         base, ext = os.path.splitext(foto.filename)
#         safe_base = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in base)[:50]
#         filename = f"{db_aluno.id}_{safe_base}{ext}"
#         file_location = UPLOAD_DIR / filename
        
#         save_upload_file(foto, file_location)
        
#         # Atualiza o caminho da foto no banco
#         db_aluno.foto = f"/static/uploads/alunos/{filename}"
#         db.commit()
#         db.refresh(db_aluno)

#     return db_aluno

# @router.get("", response_model=List[AlunoRead])
# def read_alunos(
#     skip: int = 0,
#     limit: int = 100,
#     nome: Optional[str] = None,
#     cpf: Optional[str] = None,
#     db: Session = Depends(get_db)
# ):
#     """
#     Lista alunos com filtros opcionais por nome e CPF.
#     """
#     query = db.query(Aluno)
#     if nome:
#         query = query.filter(Aluno.nome.ilike(f"%{nome}%"))
#     if cpf:
#         query = query.filter(Aluno.cpf == cpf)
    
#     return query.order_by(Aluno.nome).offset(skip).limit(limit).all()

# @router.get("/{aluno_id}", response_model=AlunoRead)
# def read_aluno(aluno_id: int, db: Session = Depends(get_db)):
#     """
#     Obtém os detalhes de um aluno específico pelo ID.
#     """
#     db_aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
#     if db_aluno is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, 
#             detail="Aluno não encontrado"
#         )
#     return db_aluno

# @router.put("/{aluno_id}", response_model=AlunoRead)
# def update_aluno(
#     aluno_id: int,
#     aluno_update: AlunoUpdate,
#     db: Session = Depends(get_db)
# ):
#     """
#     Atualiza os dados de um aluno existente.
#     """
#     db_aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
#     if db_aluno is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, 
#             detail="Aluno não encontrado"
#         )

#     update_data = aluno_update.dict(exclude_unset=True)

#     # Validação de CPF/Email único (se alterado)
#     if 'cpf' in update_data and update_data['cpf'] is not None:
#         db_aluno_cpf = db.query(Aluno).filter(
#             Aluno.cpf == update_data['cpf'], 
#             Aluno.id != aluno_id
#         ).first()
#         if db_aluno_cpf:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST, 
#                 detail="CPF já cadastrado para outro aluno"
#             )
#     if 'email' in update_data and update_data['email'] is not None:
#         db_aluno_email = db.query(Aluno).filter(
#             Aluno.email == update_data['email'], 
#             Aluno.id != aluno_id
#         ).first()
#         if db_aluno_email:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST, 
#                 detail="Email já cadastrado para outro aluno"
#             )

#     for key, value in update_data.items():
#         setattr(db_aluno, key, value)

#     try:
#         db.commit()
#         db.refresh(db_aluno)
#     except IntegrityError:
#         db.rollback()
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Erro ao atualizar aluno. Verifique os dados únicos (CPF/Email)."
#         )
        
#     return db_aluno

# @router.post("/{aluno_id}/foto", response_model=AlunoRead)
# def upload_aluno_foto(
#     aluno_id: int,
#     foto: UploadFile = File(...),
#     db: Session = Depends(get_db)
# ):
#     """
#     Faz upload ou atualiza a foto de um aluno existente.
#     """
#     try:
#         db_aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
#         if db_aluno is None:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND, 
#                 detail="Aluno não encontrado"
#             )

#         # Valida se é uma imagem
#         if not foto.content_type.startswith('image/'):
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="O arquivo deve ser uma imagem"
#             )

#         # Remove foto anterior se existir
#         if db_aluno.foto:
#             old_foto_path = BASE_DIR / db_aluno.foto.lstrip('/')
#             if old_foto_path.exists():
#                 try:
#                     old_foto_path.unlink()
#                 except OSError as e:
#                     logging.warning(f"Erro ao remover foto antiga {old_foto_path}: {e}")

#         # Salva a nova foto
#         base, ext = os.path.splitext(foto.filename)
#         safe_base = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in base)[:50]
#         filename = f"{db_aluno.id}_{safe_base}{ext}"
#         file_location = UPLOAD_DIR / filename
        
#         save_upload_file(foto, file_location)
        
#         # Atualiza o caminho da foto no banco
#         db_aluno.foto = f"/static/uploads/alunos/{filename}"
#         db.commit()
#         db.refresh(db_aluno)
        
#         return db_aluno
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logging.error(f"Erro ao processar upload de foto: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Erro interno ao processar a foto"
#         )

# # @router.post("/{aluno_id}/foto", response_model=AlunoRead)
# # def upload_aluno_foto(
# #     aluno_id: int,
# #     foto: UploadFile = File(...),
# #     db: Session = Depends(get_db)
# # ):
# #     """
# #     Faz upload ou atualiza a foto de um aluno existente.
# #     """
# #     db_aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
# #     if db_aluno is None:
# #         raise HTTPException(
# #             status_code=status.HTTP_404_NOT_FOUND, 
# #             detail="Aluno não encontrado"
# #         )

# #     # Remove foto anterior se existir - CORRIGIDO
# #     if db_aluno.foto:
# #         old_foto_path = BASE_DIR / db_aluno.foto.lstrip('/')
# #         if old_foto_path.exists():
# #             try:
# #                 old_foto_path.unlink()
# #             except OSError as e:
# #                 print(f"Erro ao remover foto antiga {old_foto_path}: {e}")

#     # Salva a nova foto - CORRIGIDO
#     base, ext = os.path.splitext(foto.filename)
#     safe_base = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in base)[:50]
#     filename = f"{db_aluno.id}_{safe_base}{ext}"
#     file_location = UPLOAD_DIR / filename
    
#     save_upload_file(foto, file_location)
    
#     # Atualiza o caminho da foto no banco
#     db_aluno.foto = f"/static/uploads/alunos/{filename}"
#     db.commit()
#     db.refresh(db_aluno)
    
#     return db_aluno

# @router.delete("/{aluno_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_aluno(aluno_id: int, db: Session = Depends(get_db)):
#     """
#     Exclui um aluno.
#     """
#     db_aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
#     if db_aluno is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, 
#             detail="Aluno não encontrado"
#         )

#     # Remove a foto se existir - CORRIGIDO
#     if db_aluno.foto:
#         foto_path = BASE_DIR / db_aluno.foto.lstrip('/')
#         if foto_path.exists():
#             try:
#                 foto_path.unlink()
#             except OSError as e:
#                 print(f"Erro ao remover foto {foto_path}: {e}")

#     db.delete(db_aluno)
#     db.commit()
#     return None

