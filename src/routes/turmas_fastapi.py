# -*- coding: utf-8 -*-
"""
Rotas FastAPI para o CRUD de Turmas.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from src.database import get_db
from src.models.turma import Turma
from src.models.professor import Professor # Importar para verificar existência do professor
# from src.models.matricula import Matricula # Importar se for verificar matrículas antes de excluir
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
    # Validação: Verifica se o professor_id existe (se fornecido)
    if turma.professor_id:
        db_professor = db.query(Professor).filter(Professor.id == turma.professor_id).first()
        if not db_professor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Professor com ID {turma.professor_id} não encontrado")
            # Alternativamente, poderia verificar se o usuário é professor, se o modelo fosse unificado.

    db_turma = Turma(**turma.dict())
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
    Lista turmas com filtros opcionais.
    """
    query = db.query(Turma)
    if modalidade:
        query = query.filter(Turma.modalidade.ilike(f"%{modalidade}%"))
    if professor_id:
        query = query.filter(Turma.professor_id == professor_id)
    if nivel:
        query = query.filter(Turma.nivel.ilike(f"%{nivel}%"))
        
    turmas = query.order_by(Turma.modalidade, Turma.horario).offset(skip).limit(limit).all()
    return turmas

@router.get("/{turma_id}", response_model=TurmaRead)
def read_turma(turma_id: int, db: Session = Depends(get_db)):
    """
    Obtém os detalhes de uma turma específica pelo ID.
    """
    db_turma = db.query(Turma).filter(Turma.id == turma_id).first()
    if db_turma is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turma não encontrada")
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

    # Validação: Verifica se o novo professor_id existe (se fornecido e diferente do atual)
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
    TODO: Adicionar verificação de dependências (ex: matrículas) antes de excluir.
    """
    db_turma = db.query(Turma).filter(Turma.id == turma_id).first()
    if db_turma is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turma não encontrada")

    # TODO: Verificar se a turma possui matrículas ativas
    # Exemplo: if db.query(Matricula).filter(Matricula.turma_id == turma_id).first():
    #             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Não é possível excluir turma com matrículas ativas")

    db.delete(db_turma)
    db.commit()
    return None

# Endpoint adicional (exemplo do Flask original)
@router.get("/utils/modalidades", response_model=List[str])
def list_modalidades():
    """Retorna uma lista fixa de modalidades."""
    # Em uma aplicação real, isso poderia vir do banco de dados
    return ["Jiu-Jitsu", "Judô", "Muay Thai", "Boxe", "MMA"]

# Endpoint adicional (exemplo do Flask original, adaptado)
# Poderia retornar um schema mais completo do professor se necessário
@router.get("/utils/professores", response_model=List[dict]) # Retorna dict simples por enquanto
def list_professores_ativos(db: Session = Depends(get_db)):
    """Retorna uma lista simplificada de professores ativos."""
    # Assume que existe um campo 'ativo' no modelo Professor ou que todos listados são ativos
    professores = db.query(Professor).order_by(Professor.nome).all() # Adicionar filtro de ativo se existir
    return [
        {"id": prof.id, "nome": prof.nome} for prof in professores
    ]

