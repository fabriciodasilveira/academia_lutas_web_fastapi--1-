# -*- coding: utf-8 -*-
"""
Rotas FastAPI para o CRUD de Turmas.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session,joinedload
import logging


from src.database import get_db
from src.models.turma import Turma
from src.models.professor import Professor
from src.schemas.turma import TurmaCreate, TurmaRead, TurmaUpdate

router = APIRouter(
    tags=["Turmas"],
    responses={404: {"description": "Não encontrado"}},
)

# --- CRUD Endpoints --- 

@router.post("", response_model=TurmaRead, status_code=status.HTTP_201_CREATED)
def create_turma(turma: TurmaCreate, db: Session = Depends(get_db)):
    """
    Cria uma nova turma.
    """
    if turma.professor_id:
        db_professor = db.query(Professor).filter(Professor.id == turma.professor_id).first()
        if not db_professor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Professor com ID {turma.professor_id} não encontrado")
    
    turma_data = turma.dict(exclude_unset=True)
    db_turma = Turma(**turma_data)
    db.add(db_turma)
    db.commit()
    db.refresh(db_turma)
    return db_turma

@router.get("", response_model=List[TurmaRead])
def read_turmas(
    skip: int = 0,
    limit: int = 100,
    modalidade: Optional[str] = None,
    professor_id: Optional[int] = None,
    nivel: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Lista turmas com filtros e contagem de alunos ativos.
    """
    query = db.query(Turma).options(
        joinedload(Turma.matriculas),  # Carrega as matrículas para contagem
        joinedload(Turma.professor)    # Carrega os dados do professor
    )
    if modalidade:
        query = query.filter(Turma.modalidade.ilike(f"%{modalidade}%"))
    if professor_id:
        query = query.filter(Turma.professor_id == professor_id)
    if nivel:
        query = query.filter(Turma.nivel.ilike(f"%{nivel}%"))
        
    turmas = query.order_by(Turma.modalidade, Turma.horario).offset(skip).limit(limit).all()

    # Calcula o total de alunos ativos para cada turma
    for turma in turmas:
        turma.total_alunos = sum(1 for m in turma.matriculas if m.ativa)

    return turmas

# Substitua a função read_turma inteira por esta:
@router.get("/{turma_id}", response_model=TurmaRead)
def read_turma(turma_id: int, db: Session = Depends(get_db)):
    """
    Obtém os detalhes de uma turma, incluindo a contagem de alunos ativos.
    """
    db_turma = db.query(Turma).options(
        joinedload(Turma.matriculas),
        joinedload(Turma.professor)
    ).filter(Turma.id == turma_id).first()

    if db_turma is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turma não encontrada")

    # Calcula o total de alunos ativos
    db_turma.total_alunos = sum(1 for m in db_turma.matriculas if m.ativa)
    
    return db_turma

@router.put("/{turma_id}", response_model=TurmaRead)
def update_turma(
    turma_id: int,
    turma_update: TurmaUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza os dados de uma turma existente.
    """
    db_turma = db.query(Turma).filter(Turma.id == turma_id).first()
    if db_turma is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turma não encontrada")

    update_data = turma_update.dict(exclude_unset=True)

    if "professor_id" in update_data and update_data["professor_id"] is not None:
        if update_data["professor_id"] != db_turma.professor_id:
            db_professor = db.query(Professor).filter(Professor.id == update_data["professor_id"]).first()
            if not db_professor:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Professor com ID {update_data['professor_id']} não encontrado")

    for key, value in update_data.items():
        setattr(db_turma, key, value)

    db.commit()
    db.refresh(db_turma)
    return db_turma

@router.delete("/{turma_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_turma(turma_id: int, db: Session = Depends(get_db)):
    """
    Exclui uma turma.
    """
    db_turma = db.query(Turma).filter(Turma.id == turma_id).first()
    if db_turma is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turma não encontrada")

    db.delete(db_turma)
    db.commit()
    return None

# Endpoints adicionais para o frontend
@router.get("/utils/modalidades", response_model=List[str])
def list_modalidades():
    return ["Jiu-Jitsu", "Judô", "Muay Thai", "Boxe", "MMA", "Karate", "Taekwondo", "Judo"]

@router.get("/utils/professores", response_model=List[dict])
def list_professores_ativos(db: Session = Depends(get_db)):
    professores = db.query(Professor).order_by(Professor.nome).all()
    return [
        {"id": prof.id, "nome": prof.nome, "especialidade": prof.especialidade} for prof in professores
    ]