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

# Imports necessários para a nova lógica de data
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta # <--- Import Adicionado

from src.models.mensalidade import Mensalidade
from sqlalchemy.orm import Session, joinedload
from src.models.historico_matricula import HistoricoMatricula


router = APIRouter(
    tags=["Matrículas"],
    responses={404: {"description": "Matrícula não encontrada"}},
)

# --- CRUD Endpoints --- 

@router.post("", response_model=MatriculaRead, status_code=status.HTTP_201_CREATED)
def create_matricula(matricula: MatriculaCreate, db: Session = Depends(get_db)):
    """
    Cria uma nova matrícula de um aluno em uma turma e GERA A PRIMEIRA MENSALIDADE
    com cálculo pro-rata e vencimento no dia 10.
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
    
    # --- NOVA LÓGICA DE CÁLCULO PRO-RATA ---
    
    DIA_VENCIMENTO_PADRAO = 10
    today = date.today()
    valor_plano = db_plano.valor

    # 1. Encontra a data do próximo vencimento (próximo dia 10)
    data_vencimento_alvo = today.replace(day=DIA_VENCIMENTO_PADRAO)
    if today.day > DIA_VENCIMENTO_PADRAO:
        # Se hoje já passou do dia 10, o vencimento é no próximo mês
        data_vencimento_alvo = data_vencimento_alvo + relativedelta(months=1)
    
    # 2. Encontra o início do ciclo de faturamento (vencimento anterior)
    data_inicio_ciclo = data_vencimento_alvo + relativedelta(months=-1)
    
    # 3. Calcula os dias totais no ciclo (ex: 30, 31, 28)
    dias_totais_no_ciclo = (data_vencimento_alvo - data_inicio_ciclo).days
    
    # 4. Calcula os dias que o aluno irá usar (contando o dia de hoje)
    # (Ex: Se matricula dia 23/11, venc. 10/12. Dias a cobrar = (10/12 - 23/11) = 17 dias)
    dias_a_cobrar = (data_vencimento_alvo - today).days
    
    # Garante que não cobre dias negativos se matricular no dia 10
    if dias_a_cobrar <= 0: 
        dias_a_cobrar = 0

    # 5. Calcula o valor proporcional
    if dias_totais_no_ciclo > 0:
        valor_diario = valor_plano / dias_totais_no_ciclo
        valor_proporcional = round(valor_diario * dias_a_cobrar, 2)
    else:
        valor_proporcional = valor_plano # Fallback para evitar divisão por zero

    # Se o valor proporcional for 0 (ex: matriculou no dia 10), 
    # a fatura é R$ 0.00 e o script do mês seguinte gera a fatura cheia.
    
    # --- FIM DA LÓGICA PRO-RATA ---

    try:
        # 1. Adiciona a matrícula à sessão
        db.add(db_matricula)
        
        # 2. FLUSH: Salva a matrícula no banco (sem comitar)
        #    Isso é crucial para que o db_matricula.id seja gerado.
        db.flush()
        
        # 3. Cria a primeira mensalidade (PROPORCIONAL)
        primeira_mensalidade = Mensalidade(
            aluno_id=db_matricula.aluno_id,
            plano_id=db_matricula.plano_id,
            valor=valor_proporcional,           # <-- Valor Proporcional
            data_vencimento=data_vencimento_alvo, # <-- Data Alvo (Próximo dia 10)
            status="pendente",
            matricula_id=db_matricula.id  # <-- Vínculo explícito
        )
        
        # 4. Adiciona a nova mensalidade à sessão
        db.add(primeira_mensalidade)
        
        # 5. COMMIT: Salva as duas transações
        db.commit()
        
        # 6. Atualiza o objeto db_matricula
        db.refresh(db_matricula)
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Erro de integridade ao criar a matrícula.")

    return db_matricula

# Em src/routes/matriculas_fastapi.py

# ... (outros imports) ...

@router.get("", response_model=List[MatriculaRead])
def read_matriculas(
    skip: int = 0,
    limit: int = 100,
    busca: Optional[str] = None, # Parâmetro de busca
    status: Optional[str] = None, # Parâmetro para filtrar por status (ativa/inativa)
    db: Session = Depends(get_db)
):
    """
    Lista matrículas com filtros por termo de busca e status.
    """
    query = db.query(Matricula).options(
        joinedload(Matricula.aluno),
        joinedload(Matricula.turma),
        joinedload(Matricula.plano)
    )

    if busca:
        # Filtra pelo nome do aluno OU nome da turma
        query = query.join(Aluno).join(Turma).filter(
            (Aluno.nome.ilike(f"%{busca}%")) |
            (Turma.nome.ilike(f"%{busca}%"))
        )
    
    if status:
        if status == 'ativa':
            query = query.filter(Matricula.ativa == True)
        elif status == 'inativa':
            query = query.filter(Matricula.ativa == False)
        
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

# Substitua a função toggle_matricula_status inteira por esta:
@router.post("/{matricula_id}/toggle-status", response_model=MatriculaRead)
def toggle_matricula_status(matricula_id: int, db: Session = Depends(get_db)):
    """
    Alterna o status de uma matrícula (ativa/inativa) e registra no histórico.
    """
    # CORREÇÃO: Usar joinedload para carregar a turma junto com a matrícula
    db_matricula = db.query(Matricula).options(
        joinedload(Matricula.turma)
    ).filter(Matricula.id == matricula_id).first()
    
    if db_matricula is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matrícula não encontrada")

    # Inverte o status atual
    db_matricula.ativa = not db_matricula.ativa
    
    # Cria a descrição para o histórico
    descricao = "Matrícula reativada" if db_matricula.ativa else "Matrícula trancada"
    
    # Cria o registro no histórico
    novo_historico = HistoricoMatricula(
        matricula_id=matricula_id,
        descricao=f"{descricao} na turma '{db_matricula.turma.nome}'"
    )
    db.add(novo_historico)
    
    db.commit()
    db.refresh(db_matricula)
    return db_matricula