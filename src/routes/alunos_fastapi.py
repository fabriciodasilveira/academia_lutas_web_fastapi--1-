# -*- coding: utf-8 -*-
import os
from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session, joinedload, selectinload # Adicionado selectinload
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

# --- CREATE ALUNO (ajustado para responsavel_aluno_id) ---
@router.post("", response_model=AlunoRead, status_code=status.HTTP_201_CREATED)
def create_aluno(
    # ... (outros Forms iguais) ...
    nome: str = Form(...),
    email: Optional[str] = Form(None), # Email pode ser None para dependentes
    data_nascimento: Optional[str] = Form(None),
    cpf: Optional[str] = Form(None),
    telefone: Optional[str] = Form(None),
    endereco: Optional[str] = Form(None),
    observacoes: Optional[str] = Form(None),
    foto: Optional[UploadFile] = File(None),
    nome_responsavel: Optional[str] = Form(None),
    cpf_responsavel: Optional[str] = Form(None),
    parentesco_responsavel: Optional[str] = Form(None),
    telefone_responsavel: Optional[str] = Form(None),
    email_responsavel: Optional[str] = Form(None),
    responsavel_aluno_id: Optional[int] = Form(None), # Campo para ID do responsável
    # ...
    db: Session = Depends(get_db)
):
    """ Cria um novo Aluno. Se email for fornecido, cria Usuario associado. """
    new_user = None
    hashed_password = None
    default_password = None

    # Verifica se o responsável existe, se fornecido
    if responsavel_aluno_id:
        db_responsavel = db.query(Aluno).filter(Aluno.id == responsavel_aluno_id).first()
        if not db_responsavel:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Aluno responsável com ID {responsavel_aluno_id} não encontrado.")
        if db_responsavel.responsavel_aluno_id: # Impede aninhamento
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Um aluno dependente não pode ser responsável por outro.")

    # Só cria usuário se tiver email e NÃO for dependente
    if email and not responsavel_aluno_id:
        db_user_check = auth.get_user(db, email=email)
        if db_user_check:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Email {email} já está em uso.")

        try:
            partes_nome = nome.strip().split(); ano_atual = datetime.now().year
            ultimo_sobrenome = partes_nome[-1] if len(partes_nome) > 1 else partes_nome[0]
            default_password = f"{ultimo_sobrenome.lower()}@{ano_atual}"
        except: default_password = f"senha@{ano_atual}"
        hashed_password = auth.get_password_hash(default_password)

        new_user = Usuario(email=email, nome=nome, hashed_password=hashed_password, role="aluno")

    # Prepara dados do Aluno
    parsed_data_nascimento = None
    if data_nascimento:
        try: parsed_data_nascimento = date.fromisoformat(data_nascimento)
        except ValueError: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato data inválido (YYYY-MM-DD)")

    # Cria o objeto Aluno
    db_aluno = Aluno(
        nome=nome, email=email, data_nascimento=parsed_data_nascimento, cpf=cpf,
        telefone=telefone, endereco=endereco, observacoes=observacoes,
        nome_responsavel=nome_responsavel, cpf_responsavel=cpf_responsavel,
        parentesco_responsavel=parentesco_responsavel, telefone_responsavel=telefone_responsavel,
        email_responsavel=email_responsavel,
        responsavel_aluno_id=responsavel_aluno_id, # Associa o responsável
        usuario=new_user # Associa o usuário (será None se email não foi dado ou se é dependente)
    )

    # Salva
    try:
        if new_user: db.add(new_user)
        db.add(db_aluno)
        db.commit()
        if new_user: db.refresh(new_user); logging.info(f"Usuário {new_user.id} criado.")
        db.refresh(db_aluno)
        logging.info(f"Aluno {db_aluno.id} criado. Responsável ID: {responsavel_aluno_id}. Senha Padrão: {default_password if default_password else 'N/A'}")

    except IntegrityError as e: db.rollback(); logging.error(f"Erro Integridade aluno/usuário: {e}"); raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Erro DB: Verifique dados únicos.")
    except Exception as e: db.rollback(); logging.error(f"Erro inesperado aluno/usuário: {e}"); raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno.")

    # Processa foto (após ter ID)
    if foto and foto.filename:
        # ... (lógica de upload S3/R2 existente, usando db_aluno.id) ...
        processed_image, mime_type = process_avatar_image(foto.file)
        if processed_image:
            # ... (config S3) ...
            s3_endpoint_url=os.getenv("..."); s3_access_key_id=os.getenv("..."); # etc
            if not all([...]): logging.warning(f"Aluno {db_aluno.id} criado, foto não salva (config S3).")
            else:
                try:
                    # ... (upload) ...
                    db_aluno.foto = f"{public_bucket_url.rstrip('/')}/{safe_filename}"
                    db.commit(); db.refresh(db_aluno); logging.info(f"Foto aluno {db_aluno.id} salva.")
                except Exception as e: logging.error(f"Erro upload R2 (create aluno {db_aluno.id}): {e}")

    # Recarrega o aluno com as relações para retornar no formato AlunoRead
    db_aluno_loaded = db.query(Aluno).options(
        selectinload(Aluno.dependentes), # Usa selectinload para carregar lista
        joinedload(Aluno.responsavel)   # Usa joinedload para carregar objeto único
    ).filter(Aluno.id == db_aluno.id).first()

    return db_aluno_loaded


# --- UPDATE ALUNO (ajustado para responsavel_aluno_id) ---
@router.put("/{aluno_id}", response_model=AlunoRead)
def update_aluno(
    aluno_id: int,
    db: Session = Depends(get_db),
    # ... (Forms iguais a create_aluno) ...
    nome: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    data_nascimento: Optional[str] = Form(None),
    cpf: Optional[str] = Form(None),
    telefone: Optional[str] = Form(None),
    endereco: Optional[str] = Form(None),
    observacoes: Optional[str] = Form(None),
    foto: Optional[UploadFile] = File(None),
    nome_responsavel: Optional[str] = Form(None),
    cpf_responsavel: Optional[str] = Form(None),
    parentesco_responsavel: Optional[str] = Form(None),
    telefone_responsavel: Optional[str] = Form(None),
    email_responsavel: Optional[str] = Form(None),
    responsavel_aluno_id: Optional[int] = Form(None) # Permite alterar/remover
):
    db_aluno = db.query(Aluno).options(joinedload(Aluno.usuario)).filter(Aluno.id == aluno_id).first()
    if not db_aluno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado")

    # Verifica novo responsável se fornecido
    if responsavel_aluno_id is not None and responsavel_aluno_id != db_aluno.responsavel_aluno_id:
         if responsavel_aluno_id == db_aluno.id: # Auto-referência
              raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Aluno não pode ser responsável por si mesmo.")
         db_responsavel = db.query(Aluno).filter(Aluno.id == responsavel_aluno_id).first()
         if not db_responsavel:
              raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Aluno responsável ID {responsavel_aluno_id} não encontrado.")
         if db_responsavel.responsavel_aluno_id:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Um dependente não pode ser responsável.")
         db_aluno.responsavel_aluno_id = responsavel_aluno_id
    elif responsavel_aluno_id is None and db_aluno.responsavel_aluno_id is not None:
         # Permite remover o responsável (setar para None)
         db_aluno.responsavel_aluno_id = None


    # Atualiza campos texto
    update_data = { "nome": nome, "cpf": cpf, "telefone": telefone, "endereco": endereco, "observacoes": observacoes, "nome_responsavel": nome_responsavel, "cpf_responsavel": cpf_responsavel, "parentesco_responsavel": parentesco_responsavel, "telefone_responsavel": telefone_responsavel, "email_responsavel": email_responsavel }
    for key, value in update_data.items():
        if value is not None: setattr(db_aluno, key, value)
    
    # Atualiza data nascimento
    if data_nascimento:
        try: db_aluno.data_nascimento = date.fromisoformat(data_nascimento)
        except: pass

    # Atualiza email (com validação e atualização no Usuario)
    if email is not None and db_aluno.email != email:
        # Se o aluno JÁ tem usuário, atualiza o email do usuário também
        if db_aluno.usuario:
             existing_user = auth.get_user(db, email=email)
             if existing_user and existing_user.id != db_aluno.usuario_id:
                  raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Email {email} já em uso.")
             db_aluno.email = email
             db_aluno.usuario.email = email
             logging.warning(f"Email aluno/usuário {aluno_id} alterado para {email}.")
        # Se o aluno NÃO tem usuário (era dependente) e está recebendo um email,
        # seria necessário CRIAR um usuário aqui (lógica mais complexa, omitida por enquanto)
        elif not db_aluno.usuario:
             # Apenas atualiza o email no Aluno, ele continuará sem login direto
             db_aluno.email = email
             logging.info(f"Email do aluno dependente {aluno_id} atualizado para {email}.")


    # Atualiza nome no Usuario associado
    if nome is not None and db_aluno.usuario and db_aluno.usuario.nome != nome:
         db_aluno.usuario.nome = nome

    # Processa foto
    if foto and foto.filename:
        # ... (lógica de upload S3/R2 idêntica à de create_aluno) ...
        processed_image, mime_type = process_avatar_image(foto.file)
        if processed_image:
             # ... (config S3) ...
             if not all([...]): logging.warning(f"Aluno {aluno_id} atualizado, foto não salva (config S3).")
             else:
                  try: # ... (upload) ... ; db_aluno.foto = ... ; logging.info(...)
                      pass # Placeholder
                  except Exception as e: logging.error(f"Erro upload R2 (update aluno {aluno_id}): {e}")


    try:
        db.commit()
        db.refresh(db_aluno)
    except Exception as e: db.rollback(); logging.error(f"Erro commit update aluno {aluno_id}: {e}"); raise HTTPException(status_code=500, detail="Erro ao salvar.")

    # Recarrega com relações para retornar
    db_aluno_loaded = db.query(Aluno).options(
        selectinload(Aluno.dependentes), joinedload(Aluno.responsavel)
    ).filter(Aluno.id == db_aluno.id).first()
    return db_aluno_loaded

# --- READ ALUNOS (ajustado para carregar relações de família) ---
@router.get("", response_model=AlunoPaginated)
def read_alunos(
    skip: int = 0, limit: int = 20, nome: Optional[str] = None, cpf: Optional[str] = None,
    status: Optional[str] = None, db: Session = Depends(get_db)
):
    query = db.query(Aluno).options(
        joinedload(Aluno.matriculas),
        selectinload(Aluno.dependentes), # Carrega lista de dependentes
        joinedload(Aluno.responsavel)   # Carrega o responsável
    )
    if nome: query = query.filter(Aluno.nome.ilike(f"%{nome}%"))
    if cpf: query = query.filter(Aluno.cpf == cpf)
    if status:
        subquery = db.query(Matricula.aluno_id).filter(Matricula.ativa == True).distinct()
        if status == 'ativo': query = query.filter(Aluno.id.in_(subquery))
        elif status == 'inativo': query = query.filter(Aluno.id.notin_(subquery))
    total = query.count()
    alunos_paginados = query.order_by(Aluno.nome).offset(skip).limit(limit).all()

    # Monta a resposta usando o schema AlunoRead que já inclui dependentes/responsavel
    response_alunos = [AlunoRead.from_orm(aluno) for aluno in alunos_paginados]
    # Calcula status_geral separadamente
    for i, aluno in enumerate(alunos_paginados):
        response_alunos[i].status_geral = "Ativo" if any(m.ativa for m in aluno.matriculas) else "Inativo"

    return {"total": total, "alunos": response_alunos}


# --- READ ALUNO (ajustado para carregar relações de família) ---
@router.get("/{aluno_id}", response_model=AlunoRead)
def read_aluno(aluno_id: int, db: Session = Depends(get_db)):
    db_aluno = db.query(Aluno).options(
        selectinload(Aluno.dependentes), # Usa selectinload para listas
        joinedload(Aluno.responsavel),
        joinedload(Aluno.matriculas) # Necessário para status_geral
    ).filter(Aluno.id == aluno_id).first()
    if db_aluno is None: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado")

    # Calcula status_geral
    aluno_data = AlunoRead.from_orm(db_aluno)
    aluno_data.status_geral = "Ativo" if any(m.ativa for m in db_aluno.matriculas) else "Inativo"
    
    return aluno_data # Retorna o objeto Pydantic


# --- DELETE ALUNO (sem mudanças na lógica principal) ---
@router.delete("/{aluno_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_aluno(aluno_id: int, db: Session = Depends(get_db)):
    # ... (código existente, lembrando que o cascade deleta o usuário) ...
    db_aluno = db.query(Aluno).options(joinedload(Aluno.usuario)).filter(Aluno.id == aluno_id).first()
    if db_aluno is None: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado")
    # Lógica S3 delete (opcional)
    try:
        db.delete(db_aluno)
        db.commit()
        logging.info(f"Aluno {aluno_id} excluído.")
    except Exception as e: db.rollback(); logging.error(f"Erro excluir aluno {aluno_id}: {e}"); raise HTTPException(status_code=500, detail=f"Erro excluir: {e}")
    return None

# --- OUTRAS ROTAS (histórico, status-detalhado) ---
# (código existente)
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