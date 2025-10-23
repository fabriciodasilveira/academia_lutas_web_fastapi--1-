# -*- coding: utf-8 -*-
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from datetime import date, timedelta, datetime # Adicionado datetime

from src.database import get_db
from src.models.matricula import Matricula
from src.models.aluno import Aluno # Importa Aluno
from src.models.turma import Turma # Importa Turma
from src.models.professor import Professor # Importa Professor para nested joinload
from src.models.plano import Plano
from src.models.mensalidade import Mensalidade
from src.models.historico_matricula import HistoricoMatricula
from src.schemas.matricula import MatriculaCreate, MatriculaRead, MatriculaUpdate

router = APIRouter(
    tags=["Matrículas"],
    prefix="/matriculas",
    responses={404: {"description": "Não encontrado"}},
)

def gerar_primeira_mensalidade(db: Session, matricula: Matricula, commit: bool = False) -> Optional[Mensalidade]:
    """ Gera a primeira mensalidade para uma nova matrícula. """
    if not matricula.plano or matricula.plano.valor <= 0: return None
    hoje = date.today(); data_vencimento = hoje + timedelta(days=7) # Vencimento em 7 dias
    nova_mensalidade = Mensalidade( aluno_id=matricula.aluno_id, plano_id=matricula.plano_id, valor=matricula.plano.valor, data_vencimento=data_vencimento, status='pendente', matricula_id=matricula.id )
    db.add(nova_mensalidade)
    if commit: 
        try: 
            db.commit(); db.refresh(nova_mensalidade); 
        except Exception as e: 
            db.rollback(); 
        raise e
    return nova_mensalidade

@router.post("", response_model=MatriculaRead, status_code=status.HTTP_201_CREATED)
def create_matricula(matricula: MatriculaCreate, db: Session = Depends(get_db)):
    db_aluno = db.query(Aluno).filter(Aluno.id == matricula.aluno_id).first();
    if not db_aluno: raise HTTPException(status_code=404, detail="Aluno não encontrado")
    db_turma = db.query(Turma).filter(Turma.id == matricula.turma_id).first();
    if not db_turma: raise HTTPException(status_code=404, detail="Turma não encontrada")
    db_plano = db.query(Plano).filter(Plano.id == matricula.plano_id).first();
    if not db_plano: raise HTTPException(status_code=404, detail="Plano não encontrado")
    matricula_existente_ativa = db.query(Matricula).filter(Matricula.aluno_id == matricula.aluno_id, Matricula.ativa == True).first() # Simplificado para verificar só aluno
    if matricula_existente_ativa: raise HTTPException(status_code=400, detail="Aluno já possui matrícula ativa.")
    db_matricula = Matricula(**matricula.dict()); primeira_mensalidade = None
    try:
        db.add(db_matricula); db.flush(); db.refresh(db_matricula) # Obtém ID
        primeira_mensalidade = gerar_primeira_mensalidade(db=db, matricula=db_matricula, commit=False)
        historico_evento = HistoricoMatricula(matricula_id=db_matricula.id, descricao=f"Matrícula realizada na turma '{db_turma.nome}' com plano '{db_plano.nome}'.")
        db.add(historico_evento); db.commit() # Salva tudo
        db.refresh(db_matricula)
    except Exception as e: db.rollback(); raise HTTPException(status_code=500, detail=f"Erro ao salvar/gerar mensalidade: {e}")
    return db_matricula

# --- FUNÇÃO READ_MATRICULAS CORRIGIDA ---
@router.get("", response_model=List[MatriculaRead])
def read_matriculas(
    skip: int = 0, limit: int = 100,
    busca: Optional[str] = None, # Busca por nome do aluno
    status: Optional[str] = None, # 'ativa' ou 'inativa'
    db: Session = Depends(get_db)
):
    """ Lista matrículas com filtros e ordenação por nome do aluno. """
    query = db.query(Matricula).options(
        joinedload(Matricula.aluno),
        joinedload(Matricula.turma).joinedload(Turma.professor),
        joinedload(Matricula.plano)
    )

    # --- CORREÇÃO: JOIN Explícito com Aluno ANTES de filtrar ou ordenar ---
    # Sempre faz o JOIN com Aluno para garantir que a tabela esteja disponível
    query = query.join(Aluno, Matricula.aluno_id == Aluno.id)
    # ----------------------------------------------------------------------

    if busca:
        query = query.filter(Aluno.nome.ilike(f"%{busca}%")) # Agora o JOIN já foi feito
    if status == 'ativa':
        query = query.filter(Matricula.ativa == True)
    elif status == 'inativa':
        query = query.filter(Matricula.ativa == False)

    # Ordena pelo nome do aluno (ascendente)
    matriculas = query.order_by(Aluno.nome.asc()).offset(skip).limit(limit).all()

    # FastAPI converte para List[MatriculaRead] automaticamente
    return matriculas

# --- RESTANTE DAS FUNÇÕES (read_matricula, update, delete, toggle) SEM ALTERAÇÃO ---
@router.get("/{matricula_id}", response_model=MatriculaRead)
def read_matricula(matricula_id: int, db: Session = Depends(get_db)):
    db_matricula = db.query(Matricula).options( joinedload(Matricula.aluno), joinedload(Matricula.turma).joinedload(Turma.professor), joinedload(Matricula.plano), joinedload(Matricula.historico) ).filter(Matricula.id == matricula_id).first()
    if db_matricula is None: raise HTTPException(status_code=404, detail="Matrícula não encontrada")
    return db_matricula

@router.put("/{matricula_id}", response_model=MatriculaRead)
def update_matricula( matricula_id: int, matricula_update: MatriculaUpdate, db: Session = Depends(get_db) ):
    db_matricula = db.query(Matricula).filter(Matricula.id == matricula_id).first()
    if not db_matricula: raise HTTPException(status_code=404, detail="Matrícula não encontrada")
    update_data = matricula_update.dict(exclude_unset=True)
    if 'turma_id' in update_data and update_data['turma_id'] != db_matricula.turma_id:
        db_turma = db.query(Turma).filter(Turma.id == update_data['turma_id']).first();
        if not db_turma: raise HTTPException(status_code=404, detail="Nova turma não encontrada")
    if 'plano_id' in update_data and update_data['plano_id'] != db_matricula.plano_id:
        db_plano = db.query(Plano).filter(Plano.id == update_data['plano_id']).first();
        if not db_plano: raise HTTPException(status_code=404, detail="Novo plano não encontrado")
    if 'ativa' in update_data and update_data['ativa'] != db_matricula.ativa:
        action = "reativada" if update_data['ativa'] else "trancada"
        historico_evento = HistoricoMatricula( matricula_id=matricula_id, descricao=f"Matrícula {action}.")
        db.add(historico_evento)
    for key, value in update_data.items(): setattr(db_matricula, key, value)
    try: db.commit(); db.refresh(db_matricula)
    except Exception as e: db.rollback(); raise HTTPException(status_code=500, detail=f"Erro ao atualizar: {e}")
    return db_matricula

@router.delete("/{matricula_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_matricula(matricula_id: int, db: Session = Depends(get_db)):
    db_matricula = db.query(Matricula).filter(Matricula.id == matricula_id).first()
    if db_matricula is None: raise HTTPException(status_code=404, detail="Matrícula não encontrada")
    try: db.delete(db_matricula); db.commit()
    except Exception as e:
        db.rollback()
        if "violates foreign key constraint" in str(e).lower() and "mensalidades_matricula_id_fkey" in str(e).lower(): raise HTTPException(status_code=400, detail="Existem mensalidades associadas.")
        raise HTTPException(status_code=500, detail=f"Erro ao excluir: {e}")
    return None

@router.post("/{matricula_id}/toggle-status", response_model=MatriculaRead)
def toggle_matricula_status(matricula_id: int, db: Session = Depends(get_db)):
    db_matricula = db.query(Matricula).options(joinedload(Matricula.turma), joinedload(Matricula.plano)).filter(Matricula.id == matricula_id).first()
    if not db_matricula: raise HTTPException(status_code=404, detail="Matrícula não encontrada")
    db_matricula.ativa = not db_matricula.ativa; action = "reativada" if db_matricula.ativa else "trancada"
    descricao_hist = f"Matrícula {action}";
    if db_matricula.turma: descricao_hist += f" na turma '{db_matricula.turma.nome}'"
    if db_matricula.plano: descricao_hist += f" (Plano: {db_matricula.plano.nome})"
    descricao_hist += "."; historico_evento = HistoricoMatricula( matricula_id=matricula_id, descricao=descricao_hist )
    db.add(historico_evento)
    try: db.commit(); db.refresh(db_matricula)
    except Exception as e: db.rollback(); raise HTTPException(status_code=500, detail=f"Erro ao alterar status: {e}")
    return db_matricula