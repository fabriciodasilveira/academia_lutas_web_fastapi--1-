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
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
import logging


# Imports para o Armazenamento Externo
import boto3
from botocore.client import Config

from src.database import get_db
from src.models.aluno import Aluno
from src.schemas.aluno import AlunoCreate, AlunoRead, AlunoUpdate, AlunoPaginated
from src.models.matricula import Matricula
from src.models.historico_matricula import HistoricoMatricula
from sqlalchemy import func
from src.models.mensalidade import Mensalidade
from src.image_utils import process_avatar_image
from src.models import usuario as models_usuario
from src import auth


router = APIRouter(
    tags=["Alunos"],
    responses={404: {"description": "Aluno não encontrado"}},
)


@router.post("", response_model=AlunoRead, status_code=status.HTTP_201_CREATED)
def create_aluno(
    nome: str = Form(...),
    data_nascimento: Optional[str] = Form(None),
    cpf: Optional[str] = Form(None),
    telefone: Optional[str] = Form(None),
    email: Optional[str] = Form(None), # <--- Este campo é a chave
    endereco: Optional[str] = Form(None),
    observacoes: Optional[str] = Form(None),
    foto: Optional[UploadFile] = File(None),
    nome_responsavel: Optional[str] = Form(None),
    cpf_responsavel: Optional[str] = Form(None),
    parentesco_responsavel: Optional[str] = Form(None),
    telefone_responsavel: Optional[str] = Form(None),
    email_responsavel: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Cria um novo aluno.
    Se um email for fornecido, cria também uma conta de usuário (Usuario)
    para o portal do aluno.
    """
    
    # --- NOVA LÓGICA DE CRIAÇÃO DE USUÁRIO ---
    db_user = None
    if email:
        # Verifica se o e-mail já está em uso na tabela de usuários
        db_user = db.query(models_usuario.Usuario).filter(models_usuario.Usuario.email == email).first()
        if db_user:
            # Se o e-mail já existe, não podemos criar o aluno
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este email já está cadastrado em outro usuário."
            )
        
        # Cria o novo usuário, sem senha (permitido pelo modelo)
        # O aluno usará o "Entrar com Google" ou "Esqueci a Senha" (se implementado)
        db_user = models_usuario.Usuario(
            email=email,
            nome=nome,
            role="aluno" # Define a permissão como 'aluno'
        )
        db.add(db_user)
    # --- FIM DA NOVA LÓGICA ---

    # Processa a data de nascimento
    parsed_data_nascimento = None
    if data_nascimento:
        try:
            parsed_data_nascimento = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de data inválido. Use YYYY-MM-DD")

    # Prepara os dados do aluno
    aluno_data = AlunoCreate(
        nome=nome, data_nascimento=parsed_data_nascimento, cpf=cpf, telefone=telefone,
        email=email, endereco=endereco, observacoes=observacoes,
        nome_responsavel=nome_responsavel, cpf_responsavel=cpf_responsavel,
        parentesco_responsavel=parentesco_responsavel, telefone_responsavel=telefone_responsavel,
        email_responsavel=email_responsavel
    )

    db_aluno = Aluno(**aluno_data.dict(exclude_unset=True))

    # --- NOVA LÓGICA DE VÍNCULO ---
    if db_user:
        db_aluno.usuario = db_user # Vincula o aluno ao usuário criado
    # --- FIM DA NOVA LÓGICA ---

    db.add(db_aluno)
    
    try:
        # Faz o commit para salvar Aluno (e Usuário, se houver)
        # Isso é necessário para que db_aluno.id seja gerado ANTES do upload da foto
        db.commit()
    except IntegrityError as e:
        db.rollback()
        logging.error(f"Erro de integridade ao salvar aluno: {e}")
        # Verifica se o erro é de CPF ou Email duplicado (que são UNIQUE)
        if "cpf" in str(e).lower():
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este CPF já está cadastrado.")
        if "email" in str(e).lower():
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este Email já está cadastrado.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno ao salvar dados.")

    db.refresh(db_aluno)
    if db_user:
        db.refresh(db_user) # Atualiza o usuário também

    # Lógica de Upload de Foto (permanece a mesma)
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
                db.commit() # Salva a URL da foto no aluno
                db.refresh(db_aluno)
            except Exception as e: 
                logging.error(f"Erro no upload para o R2 (aluno): {e}")
                # Não lança exceção, pois o aluno já foi criado

    return db_aluno

@router.put("/{aluno_id}", response_model=AlunoRead)
def update_aluno(
    aluno_id: int,
    db: Session = Depends(get_db),
    # Formulário de dados
    nome: Optional[str] = Form(None),
    data_nascimento: Optional[str] = Form(None),
    cpf: Optional[str] = Form(None),
    telefone: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    endereco: Optional[str] = Form(None),
    observacoes: Optional[str] = Form(None),
    foto: Optional[UploadFile] = File(None),
    nome_responsavel: Optional[str] = Form(None),
    cpf_responsavel: Optional[str] = Form(None),
    parentesco_responsavel: Optional[str] = Form(None),
    telefone_responsavel: Optional[str] = Form(None),
    email_responsavel: Optional[str] = Form(None)
):
    """
    Atualiza um aluno existente, com upload de foto para o R2.
    """
    db_aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
    if not db_aluno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado")

    # Atualiza campos de texto
    update_data = {
        "nome": nome, "cpf": cpf, "telefone": telefone, "email": email, "endereco": endereco, "observacoes": observacoes,
        "nome_responsavel": nome_responsavel, "cpf_responsavel": cpf_responsavel,
        "parentesco_responsavel": parentesco_responsavel, "telefone_responsavel": telefone_responsavel,
        "email_responsavel": email_responsavel
    }
    for key, value in update_data.items():
        if value is not None:
            setattr(db_aluno, key, value)
    
    if data_nascimento:
        try:
            db_aluno.data_nascimento = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            pass

    if foto and foto.filename:
        # Processa a imagem antes do upload
        processed_image, mime_type = process_avatar_image(foto.file)
        
        if processed_image:
            # Pega as credenciais do ambiente
            s3_endpoint_url = os.getenv("S3_ENDPOINT_URL")
            s3_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
            s3_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
            s3_bucket_name = os.getenv("S3_BUCKET_NAME")
            public_bucket_url = os.getenv("PUBLIC_BUCKET_URL")

            if not all([s3_endpoint_url, s3_access_key_id, s3_secret_access_key, s3_bucket_name, public_bucket_url]):
                raise HTTPException(status_code=500, detail="Configuração de armazenamento na nuvem incompleta.")

            try:
                s3_client = boto3.client('s3', endpoint_url=s3_endpoint_url, aws_access_key_id=s3_access_key_id, aws_secret_access_key=s3_secret_access_key, region_name="auto")
                
                # Garante um nome de arquivo .jpg, já que convertemos para JPEG
                base_filename, _ = os.path.splitext(foto.filename)
                safe_filename = f"aluno_{db_aluno.id}_{datetime.utcnow().timestamp()}_{base_filename.replace(' ', '_')}.jpg"

                # Faz o upload do arquivo processado (em memória)
                s3_client.upload_fileobj(processed_image, s3_bucket_name, safe_filename, ExtraArgs={'ContentType': mime_type})
                
                db_aluno.foto = f"{public_bucket_url.rstrip('/')}/{safe_filename}"
                db.commit()
                db.refresh(db_aluno)
            except Exception as e:
                logging.error(f"Erro no upload para o R2 (aluno): {e}")
                # Não lança exceção para não quebrar o cadastro do aluno
                logging.error(f"Erro no upload para o R2 (aluno): {e}")

    db.commit()
    db.refresh(db_aluno)
    return db_aluno
    
# --- SUAS OUTRAS ROTAS DE ALUNO (read_alunos, read_aluno, etc.) PERMANECEM AQUI SEM ALTERAÇÃO ---
# ... (deixe o resto das funções como estão)
@router.get("", response_model=AlunoPaginated)
def read_alunos(
    skip: int = 0,
    limit: int = 20,
    nome: Optional[str] = None,
    cpf: Optional[str] = None,
    status: Optional[str] = None, # NOVO PARÂMETRO DE FILTRO
    db: Session = Depends(get_db)
):
    """
    Lista alunos com filtros (incluindo status) e paginação.
    """
    query = db.query(Aluno).options(joinedload(Aluno.matriculas))
    
    if nome:
        query = query.filter(Aluno.nome.ilike(f"%{nome}%"))
    if cpf:
        query = query.filter(Aluno.cpf == cpf)
    
    # --- NOVA LÓGICA DE FILTRO POR STATUS ---
    if status:
        # Subconsulta para encontrar todos os IDs de alunos que têm pelo menos uma matrícula ativa.
        subquery_alunos_ativos = db.query(Matricula.aluno_id).filter(Matricula.ativa == True).distinct()
        
        if status == 'ativo':
            query = query.filter(Aluno.id.in_(subquery_alunos_ativos))
        elif status == 'inativo':
            query = query.filter(Aluno.id.notin_(subquery_alunos_ativos))
    # --- FIM DA LÓGICA ---

    total = query.count()
    alunos_paginados = query.order_by(Aluno.nome).offset(skip).limit(limit).all()

    response_alunos = []
    for aluno in alunos_paginados:
        aluno_read = AlunoRead.from_orm(aluno)
        if any(matricula.ativa for matricula in aluno.matriculas):
            aluno_read.status_geral = "Ativo"
        else:
            aluno_read.status_geral = "Inativo"
        response_alunos.append(aluno_read)
        
    return {"total": total, "alunos": response_alunos}

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
        foto_path = Path(str(BASE_DIR) + db_aluno.foto)
        if foto_path.exists():
            try:
                foto_path.unlink()
            except OSError as e:
                print(f"Erro ao remover foto {foto_path}: {e}")

    db.delete(db_aluno)
    db.commit()
    return None

# Em src/routes/alunos_fastapi.py

# ... (outros imports) ...

@router.get("/{aluno_id}/historico")
def get_aluno_historico(aluno_id: int, db: Session = Depends(get_db)):
    """
    Retorna um histórico de atividades para um aluno específico, incluindo status de matrícula.
    """
    aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    historico = []

    if aluno.data_cadastro:
        historico.append({
            "data": aluno.data_cadastro.isoformat(),
            "descricao": "Aluno cadastrado no sistema",
            "tipo": "cadastro"
        })

    matriculas = db.query(Matricula).options(
        joinedload(Matricula.turma), 
        joinedload(Matricula.historico) # Carrega o histórico junto
    ).filter(Matricula.aluno_id == aluno_id).all()
    
    for m in matriculas:
        historico.append({
            "data": m.data_matricula.isoformat(),
            "descricao": f"Matriculado na turma '{m.turma.nome}'",
            "tipo": "matricula"
        })
        # Adiciona os eventos de trancamento/reativação
        for evento_historico in m.historico:
            historico.append({
                "data": evento_historico.data_alteracao.isoformat(),
                "descricao": evento_historico.descricao,
                "tipo": "status_change" # Um novo tipo para o frontend
            })

    historico.sort(key=lambda x: x['data'])

    return historico

@router.get("/{aluno_id}/status-detalhado")
def get_aluno_status_detalhado(aluno_id: int, db: Session = Depends(get_db)):
    """
    Retorna a situação geral e o status financeiro de um aluno.
    """
    aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    # 1. Verifica a Situação Geral (se tem alguma matrícula ativa)
    matricula_ativa = db.query(Matricula).filter(
        Matricula.aluno_id == aluno_id,
        Matricula.ativa == True
    ).first()
    
    situacao_geral = "Ativo" if matricula_ativa else "Inativo"

    # 2. Verifica o Status da Mensalidade
    mensalidades_pendentes = db.query(func.sum(Mensalidade.valor)).filter(
        Mensalidade.aluno_id == aluno_id,
        Mensalidade.status == 'pendente'
    ).scalar() or 0.0

    status_mensalidade = "Em dia" if mensalidades_pendentes == 0 else "Pendente"

    return {
        "situacao_geral": situacao_geral,
        "status_mensalidade": status_mensalidade,
        "valor_pendente": mensalidades_pendentes
    }