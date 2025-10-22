from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile, Query # Adicionado Query
from sqlalchemy.orm import Session, joinedload, selectinload
from typing import Optional, List
from datetime import datetime, date
import logging
import os
import boto3
from botocore.client import Config

from src.image_utils import process_avatar_image
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

router = APIRouter(
    prefix="/api/v1/portal",
    tags=["Portal do Aluno"]
)

# --- Rota /register (sem alterações) ---
@router.post("/register", response_model=schemas_aluno.AlunoRead, status_code=status.HTTP_201_CREATED)
def register_aluno(aluno_data: schemas_portal.AlunoRegistration, db: Session = Depends(database.get_db)):
    # ... (código existente) ...
    db_user = auth.get_user(db, email=aluno_data.email)
    if db_user: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email já cadastrado.")
    hashed_password = auth.get_password_hash(aluno_data.password)
    new_user = models.usuario.Usuario(email=aluno_data.email, nome=aluno_data.nome, hashed_password=hashed_password, role="aluno")
    new_aluno = models.aluno.Aluno(nome=aluno_data.nome, email=aluno_data.email, telefone=aluno_data.telefone, data_nascimento=aluno_data.data_nascimento, usuario=new_user)
    try: db.add(new_user); db.add(new_aluno); db.commit(); db.refresh(new_user); db.refresh(new_aluno)
    except Exception as e: db.rollback(); raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao criar usuário: {e}")
    return new_aluno


# --- Rota /me ATUALIZADA para incluir dependentes ---
@router.get("/me", response_model=schemas_aluno.AlunoRead)
def get_current_aluno_profile(
    current_user: models.usuario.Usuario = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    """ Retorna o perfil do aluno logado E a lista de seus dependentes. """
    if current_user.role != "aluno":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")

    # Carrega o aluno, suas matrículas E seus dependentes
    aluno_profile = db.query(models.aluno.Aluno).options(
        joinedload(models.aluno.Aluno.matriculas),
        selectinload(models.aluno.Aluno.dependentes) # Carrega a lista de dependentes
    ).filter(models.aluno.Aluno.usuario_id == current_user.id).first()

    if not aluno_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de aluno não encontrado.")

    # Calcula status
    status_geral = "Ativo" if any(m.ativa for m in aluno_profile.matriculas) else "Inativo"
    
    # Monta a resposta Pydantic
    aluno_data = schemas_aluno.AlunoRead.from_orm(aluno_profile)
    aluno_data.status_geral = status_geral

    return aluno_data


# --- Rota /me (PUT) ATUALIZADA (sem mudanças lógicas grandes, só confirmação) ---
@router.put("/me", response_model=schemas_aluno.AlunoRead)
def update_current_aluno_profile(
    # ... (código existente, já deve estar correto com upload S3) ...
    db: Session = Depends(database.get_db), current_user: models.usuario.Usuario = Depends(auth.get_current_active_user),
    nome: str = Form(...), cpf: Optional[str] = Form(None), telefone: Optional[str] = Form(None),
    data_nascimento: Optional[str] = Form(None), endereco: Optional[str] = Form(None), observacoes: Optional[str] = Form(None),
    foto: Optional[UploadFile] = File(None), nome_responsavel: Optional[str] = Form(None), cpf_responsavel: Optional[str] = Form(None),
    parentesco_responsavel: Optional[str] = Form(None), telefone_responsavel: Optional[str] = Form(None), email_responsavel: Optional[str] = Form(None)
):
    if current_user.role != "aluno": raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")
    db_aluno = db.query(models.aluno.Aluno).filter(models.aluno.Aluno.usuario_id == current_user.id).first()
    if not db_aluno: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil não encontrado.")
    update_data = { "nome": nome, "cpf": cpf, "telefone": telefone, "endereco": endereco, "observacoes": observacoes, "nome_responsavel": nome_responsavel, "cpf_responsavel": cpf_responsavel, "parentesco_responsavel": parentesco_responsavel, "telefone_responsavel": telefone_responsavel, "email_responsavel": email_responsavel }
    for key, value in update_data.items(): setattr(db_aluno, key, value)
    if data_nascimento: 
        try: 
            db_aluno.data_nascimento = date.fromisoformat(data_nascimento); 
        except: pass
        
    if foto and foto.filename:
        processed_image, mime_type = process_avatar_image(foto.file)
        if processed_image:
            s3_endpoint_url=os.getenv("..."); s3_access_key_id=os.getenv("..."); s3_secret_access_key=os.getenv("..."); s3_bucket_name=os.getenv("..."); public_bucket_url=os.getenv("...")
            if not all([...]): logging.warning(f"Aluno {db_aluno.id} atualizado, foto não salva (config S3).")
            else:
                try: s3_client = boto3.client(...); base_filename, _ = os.path.splitext(foto.filename); safe_filename = f"aluno_{db_aluno.id}_{datetime.utcnow().timestamp()}_{base_filename.replace(' ', '_')}.jpg"; s3_client.upload_fileobj(processed_image, s3_bucket_name, safe_filename, ExtraArgs={'ContentType': mime_type}); db_aluno.foto = f"{public_bucket_url.rstrip('/')}/{safe_filename}"
                except Exception as e: logging.error(f"Erro upload R2 (portal {db_aluno.id}): {e}"); raise HTTPException(status_code=500, detail="Falha upload foto.")
    db.commit(); db.refresh(db_aluno)
    # Recarrega com dependentes para retornar tudo
    db_aluno_loaded = db.query(models.aluno.Aluno).options(selectinload(models.aluno.Aluno.dependentes)).filter(models.aluno.Aluno.id == db_aluno.id).first()
    return db_aluno_loaded


# --- NOVA ROTA para buscar dados de um dependente específico ---
@router.get("/aluno/{aluno_id}", response_model=schemas_aluno.AlunoRead)
def get_specific_aluno_profile(
    aluno_id: int,
    current_user: models.usuario.Usuario = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    """ Busca o perfil de um aluno específico, verificando se o usuário logado é o responsável. """
    # Busca o perfil do usuário logado
    responsavel_profile = db.query(models.aluno.Aluno).filter(models.aluno.Aluno.usuario_id == current_user.id).first()
    if not responsavel_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil do responsável não encontrado.")

    # Busca o perfil do aluno solicitado (dependente)
    dependente_profile = db.query(models.aluno.Aluno).options(
        joinedload(models.aluno.Aluno.matriculas) # Carrega matrículas para status
    ).filter(
        models.aluno.Aluno.id == aluno_id,
        models.aluno.Aluno.responsavel_aluno_id == responsavel_profile.id # Garante que é dependente do logado
    ).first()

    if not dependente_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno dependente não encontrado ou acesso não autorizado.")

    # Calcula status
    status_geral = "Ativo" if any(m.ativa for m in dependente_profile.matriculas) else "Inativo"
    aluno_data = schemas_aluno.AlunoRead.from_orm(dependente_profile)
    aluno_data.status_geral = status_geral

    return aluno_data


# --- ROTAS EXISTENTES ADAPTADAS para aceitar aluno_id opcional ---

# Função auxiliar para obter o ID do aluno alvo (logado ou dependente)
def get_target_aluno_id(
    aluno_id_param: Optional[int], # ID vindo do query parameter
    current_user: models.usuario.Usuario,
    db: Session
) -> int:
    """ Determina o ID do aluno a ser consultado (logado ou dependente válido). """
    user_aluno_profile = db.query(models.aluno.Aluno).options(selectinload(models.aluno.Aluno.dependentes))\
                           .filter(models.aluno.Aluno.usuario_id == current_user.id).first()
    if not user_aluno_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil do aluno logado não encontrado.")

    if aluno_id_param is None or aluno_id_param == user_aluno_profile.id:
        return user_aluno_profile.id # Retorna o ID do próprio usuário logado
    else:
        # Verifica se o aluno_id_param é um dependente válido do usuário logado
        is_dependent = any(dep.id == aluno_id_param for dep in user_aluno_profile.dependentes)
        if not is_dependent:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado aos dados deste aluno.")
        return aluno_id_param # Retorna o ID do dependente

@router.get("/matriculas", response_model=List[MatriculaRead])
def get_aluno_matriculas(
    aluno_id: Optional[int] = Query(None, description="ID do aluno (para responsáveis consultarem dependentes)"),
    current_user: models.usuario.Usuario = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    target_aluno_id = get_target_aluno_id(aluno_id, current_user, db)
    
    matriculas = db.query(Matricula).options(
        joinedload(Matricula.turma), # Carrega a turma junto
        joinedload(Matricula.plano)  # Carrega o plano junto
    ).filter(
        Matricula.aluno_id == target_aluno_id,
        Matricula.ativa == True
    ).order_by(Matricula.data_matricula.desc()).all()
    return matriculas

@router.get("/pendencias", response_model=List[PendenciaFinanceira])
def get_aluno_pendencias_financeiras(
    aluno_id: Optional[int] = Query(None, description="ID do aluno (para responsáveis consultarem dependentes)"),
    current_user: models.usuario.Usuario = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    target_aluno_id = get_target_aluno_id(aluno_id, current_user, db)
    
    pendencias = []
    # Busca mensalidades do aluno alvo
    mensalidades = db.query(Mensalidade).options(joinedload(Mensalidade.plano))\
                     .filter(Mensalidade.aluno_id == target_aluno_id).all()
    for m in mensalidades:
        pendencias.append(PendenciaFinanceira(tipo='mensalidade', id=m.id, descricao=f"Mensalidade - {m.plano.nome if m.plano else 'N/A'}", data_vencimento=m.data_vencimento, valor=m.valor, status=m.status))
    
    # Busca inscrições do aluno alvo
    inscricoes = db.query(Inscricao).options(joinedload(Inscricao.evento))\
                   .filter(Inscricao.aluno_id == target_aluno_id).all()
    for i in inscricoes:
        pendencias.append(PendenciaFinanceira(tipo='inscricao', id=i.id, descricao=f"Inscrição - {i.evento.nome if i.evento else 'N/A'}", data_vencimento=i.evento.data_evento.date() if i.evento else date.today(), valor=i.evento.valor_inscricao if i.evento else 0, status=i.status))
        
    pendencias.sort(key=lambda x: x.data_vencimento, reverse=True)
    return pendencias

@router.get("/eventos", response_model=List[SchemasEventoRead])
def get_portal_eventos(
    aluno_id: Optional[int] = Query(None, description="ID do aluno (para responsáveis consultarem dependentes)"),
    current_user: models.usuario.Usuario = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    target_aluno_id = get_target_aluno_id(aluno_id, current_user, db)
    
    todos_eventos = db.query(Evento).order_by(Evento.data_evento.desc()).all()
    # Verifica inscrições do aluno alvo
    inscricoes_aluno = db.query(Inscricao.evento_id).filter(Inscricao.aluno_id == target_aluno_id).all()
    eventos_inscritos_ids = {inscricao.evento_id for inscricao in inscricoes_aluno}

    eventos_com_status = []
    for evento in todos_eventos:
        evento_data = SchemasEventoRead.from_orm(evento)
        evento_data.is_inscrito = evento.id in eventos_inscritos_ids
        eventos_com_status.append(evento_data)
    return eventos_com_status

# A rota de inscrever continua sendo para o aluno logado (o responsável inscreve o filho)
@router.post("/eventos/{evento_id}/inscrever", response_model=InscricaoRead)
def inscrever_aluno_evento(
    evento_id: int,
    # Opcional: Permitir que responsável inscreva dependente?
    # aluno_id: Optional[int] = Body(None), # Receberia ID do dependente no corpo
    current_user: models.usuario.Usuario = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    # Por enquanto, inscreve apenas o aluno logado (ou o responsável por si mesmo)
    target_aluno_id = get_target_aluno_id(None, current_user, db) # ID do logado

    db_evento = db.query(Evento).filter(Evento.id == evento_id).first()
    if not db_evento: raise HTTPException(status_code=404, detail="Evento não encontrado")
    
    db_inscricao_existente = db.query(Inscricao).filter(Inscricao.aluno_id == target_aluno_id, Inscricao.evento_id == evento_id).first()
    if db_inscricao_existente: raise HTTPException(status_code=400, detail="Você já está inscrito neste evento.")

    # Verifica capacidade
    inscricoes_count = db.query(Inscricao).filter(Inscricao.evento_id == evento_id).count()
    if db_evento.capacidade > 0 and inscricoes_count >= db_evento.capacidade:
        raise HTTPException(status_code=400, detail="Evento lotado")

    db_inscricao = Inscricao(aluno_id=target_aluno_id, evento_id=evento_id)
    if db_evento.valor_inscricao == 0: db_inscricao.status = "pago"; db_inscricao.metodo_pagamento = "Gratuito"

    db.add(db_inscricao); db.commit(); db.refresh(db_inscricao)
    return db_inscricao