# src/routes/conteudos_fastapi.py
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from src.database import get_db
from src import auth
from src.models.usuario import Usuario
from src.models.conteudo import Conteudo

router = APIRouter(
    prefix="/api/v1/conteudos",
    tags=["Conteúdos (Aulas)"]
)

# --- SCHEMAS (Validação de Dados) ---
class ConteudoCreate(BaseModel):
    modulo: str = "Jiu-Jitsu Básico"
    semana: int
    ordem: int = 1
    titulo: str
    descricao: Optional[str] = None
    video_url: str

class ConteudoResponse(ConteudoCreate):
    id: int
    ativo: bool
    class Config:
        orm_mode = True

# --- ROTAS ---

@router.get("", response_model=List[ConteudoResponse])
def listar_conteudos(
    modulo: str = None, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(auth.get_current_active_user)
):
    """
    Lista todas as aulas ativas. 
    Se for Aluno, vê tudo. Se for Professor, vê tudo também.
    Ordenado por Semana e Ordem.
    """
    query = db.query(Conteudo).filter(Conteudo.ativo == True)
    
    if modulo:
        query = query.filter(Conteudo.modulo == modulo)
        
    return query.order_by(Conteudo.modulo, Conteudo.semana, Conteudo.ordem).all()

@router.post("", response_model=ConteudoResponse)
def criar_conteudo(
    aula: ConteudoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(auth.get_current_active_user) # Ideal: checar se é professor/admin
):
    # Verifica permissão (apenas staff pode postar)
    if current_user.role not in ['administrador', 'professor', 'gerente']:
        raise HTTPException(status_code=403, detail="Apenas professores podem postar aulas.")

    novo_conteudo = Conteudo(
        modulo=aula.modulo,
        semana=aula.semana,
        ordem=aula.ordem,
        titulo=aula.titulo,
        descricao=aula.descricao,
        video_url=aula.video_url,
        autor_id=current_user.id
    )
    
    db.add(novo_conteudo)
    db.commit()
    db.refresh(novo_conteudo)
    return novo_conteudo

@router.delete("/{id}")
def deletar_conteudo(
    id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(auth.get_current_active_user)
):
    if current_user.role not in ['administrador', 'professor', 'gerente']:
        raise HTTPException(status_code=403, detail="Sem permissão.")
        
    conteudo = db.query(Conteudo).filter(Conteudo.id == id).first()
    if not conteudo:
        raise HTTPException(status_code=404, detail="Aula não encontrada")
        
    db.delete(conteudo)
    db.commit()
    return {"message": "Aula removida com sucesso"}