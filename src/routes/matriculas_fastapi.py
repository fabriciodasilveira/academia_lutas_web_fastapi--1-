# -*- coding: utf-8 -*-
"""
Rotas FastAPI para o CRUD de Matrículas.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

from src.database import get_db
from src.models.matricula import Matricula
from src.models.aluno import Aluno
from src.models.turma import Turma
from src.schemas.matricula import MatriculaCreate, MatriculaRead, MatriculaUpdate
from src.models.plano import Plano
from datetime import date, timedelta
from src.models.mensalidade import Mensalidade
from sqlalchemy.orm import Session, joinedload



router = APIRouter(
    tags=["Matrículas"],
    responses={404: {"description": "Matrícula não encontrada"}},
)

# --- CRUD Endpoints --- 

@router.post("", response_model=MatriculaRead, status_code=status.HTTP_201_CREATED)
def create_matricula(matricula: MatriculaCreate, db: Session = Depends(get_db)):
    """
    Cria uma nova matrícula de um aluno em uma turma e GERA A PRIMEIRA MENSALIDADE.
    """
    db_aluno = db.query(Aluno).filter(Aluno.id == matricula.aluno_id).first()
    if not db_aluno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado")

    db_turma = db.query(Turma).filter(Turma.id == matricula.turma_id).first()
    if not db_turma:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turma não encontrada")

    db_plano = db.query(Plano).filter(Plano.id == matricula.plano_id).first()
    if not db_plano:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plano não encontrado")

    db_matricula_existente = db.query(Matricula).filter(
        Matricula.aluno_id == matricula.aluno_id,
        Matricula.turma_id == matricula.turma_id
    ).first()
    if db_matricula_existente and db_matricula_existente.ativa:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Aluno já está matriculado e ativo nesta turma")

    db_matricula = Matricula(**matricula.dict())
    
    try:
        db.add(db_matricula)
        
        # --- LÓGICA PARA CRIAR A PRIMEIRA MENSALIDADE ---
        primeira_mensalidade = Mensalidade(
            aluno_id=db_matricula.aluno_id,
            plano_id=db_matricula.plano_id,
            valor=db_plano.valor,
            # Define o vencimento para 7 dias a partir da data da matrícula
            data_vencimento=date.today() + timedelta(days=7),
            status="pendente"
        )
        db.add(primeira_mensalidade)
        # --- FIM DA LÓGICA ---
        
        db.commit()
        db.refresh(db_matricula)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Erro de integridade ao criar a matrícula.")

    return db_matricula

@router.get("", response_model=List[MatriculaRead])
def read_matriculas(
    skip: int = 0,
    limit: int = 100,
    aluno_id: Optional[int] = None,
    turma_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Lista matrículas com filtros opcionais por aluno e turma.
    """
    # A consulta agora carrega os dados relacionados (aluno, turma, plano) de forma otimizada
    query = db.query(Matricula).options(
        joinedload(Matricula.aluno),
        joinedload(Matricula.turma),
        joinedload(Matricula.plano)
    )

    if aluno_id:
        query = query.filter(Matricula.aluno_id == aluno_id)
    if turma_id:
        query = query.filter(Matricula.turma_id == turma_id)
        
    matriculas = query.order_by(Matricula.data_matricula.desc()).offset(skip).limit(limit).all()
    return matriculas

@router.put("/{matricula_id}", response_model=MatriculaRead)
def update_matricula(
    matricula_id: int,
    matricula_update: MatriculaUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza os dados de uma matrícula existente (ex: status ativa/inativa).
    """
    db_matricula = db.query(Matricula).filter(Matricula.id == matricula_id).first()
    if db_matricula is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matrícula não encontrada")

    update_data = matricula_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_matricula, key, value)

    db.commit()
    db.refresh(db_matricula)
    return db_matricula

@router.delete("/{matricula_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_matricula(matricula_id: int, db: Session = Depends(get_db)):
    """
    Exclui uma matrícula.
    """
    db_matricula = db.query(Matricula).filter(Matricula.id == matricula_id).first()
    if db_matricula is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matrícula não encontrada")

    db.delete(db_matricula)
    db.commit()
    return None