# src/routes/portal_professor_fastapi.py
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from src.database import get_db
from src import auth, models
from src.models.mensalidade import Mensalidade
from src.models.financeiro import Financeiro
from src.models.aluno import Aluno
from src.models.usuario import Usuario
from src.schemas.aluno import AlunoCreate
from src.routes.alunos_fastapi import create_aluno as core_create_aluno # Reutiliza lógica core
from src.models.presenca import Presenca # <--- Novo Import
from src.models.matricula import Matricula # <--- Novo Import
from src.models.turma import Turma # <--- Novo Import
from datetime import date # <--- Novo Import

router = APIRouter(
    prefix="/api/v1/portal-professor",
    tags=["Portal Professor"]
)

# Dependência para garantir que é Staff (Professor ou Atendente)
async def get_current_staff(current_user: Usuario = Depends(auth.get_current_active_user)):
    if current_user.role not in ['administrador', 'gerente', 'atendente', 'professor']:
        raise HTTPException(status_code=403, detail="Acesso restrito a equipe.")
    return current_user

# --- 1. CADASTRAR ALUNO (Simplificado para o PWA) ---
# Vamos reutilizar a rota principal de alunos, mas criar um wrapper se necessário,
# ou o frontend pode chamar a rota /api/v1/alunos diretamente se o usuário tiver permissão.
# Vamos manter simples: O frontend chamará /api/v1/alunos diretamente.

# --- 2. FINANCEIRO: LISTAR MENSALIDADES PENDENTES ---
@router.get("/mensalidades-pendentes")
def list_mensalidades_pendentes(
    busca: str = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_staff)
):
    query = db.query(Mensalidade).options(
        joinedload(Mensalidade.aluno),
        joinedload(Mensalidade.plano)
    ).filter(Mensalidade.status == 'pendente')

    if busca:
        query = query.join(Aluno).filter(Aluno.nome.ilike(f"%{busca}%"))
    
    mensalidades = query.order_by(Mensalidade.data_vencimento).limit(50).all()
    return mensalidades

# --- 3. FINANCEIRO: RECEBER EM DINHEIRO (Caixa Virtual) ---
@router.post("/mensalidades/{id}/receber-dinheiro")
def receber_mensalidade_dinheiro(
    id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_staff)
):
    mensalidade = db.query(Mensalidade).filter(Mensalidade.id == id).first()
    if not mensalidade:
        raise HTTPException(status_code=404, detail="Mensalidade não encontrada")
    
    if mensalidade.status == 'pago':
        raise HTTPException(status_code=400, detail="Esta mensalidade já está paga.")

    # 1. Atualiza Mensalidade
    mensalidade.status = 'pago'
    mensalidade.data_pagamento = datetime.utcnow().date()

    # 2. Cria Transação Financeira (Receita)
    # IMPORTANTE: responsavel_id marca quem recebeu (Caixa Virtual do Professor)
    nova_transacao = Financeiro(
        tipo="receita",
        categoria="Mensalidade",
        descricao=f"Recebimento Manual (Portal): {mensalidade.aluno.nome} - Ref. Mensalidade #{mensalidade.id}",
        valor=mensalidade.valor,
        status="confirmado",
        data=datetime.utcnow(),
        forma_pagamento="Dinheiro",
        observacoes=f"Recebido via Portal do Professor por {current_user.nome}",
        responsavel_id=current_user.id 
    )
    
    db.add(nova_transacao)
    db.commit()
    
    return {"message": "Pagamento recebido com sucesso!", "valor": mensalidade.valor}


@router.get("/turmas/{turma_id}/alunos-chamada")
def get_alunos_para_chamada(turma_id: int, data: str = None, db: Session = Depends(get_db)):
    data_chamada = datetime.utcnow().date()
    if data:
        try: data_chamada = datetime.strptime(data, '%Y-%m-%d').date()
        except: pass

    matriculas = db.query(Matricula).filter(
        Matricula.turma_id == turma_id,
        Matricula.ativa == True
    ).all()

    presencas_hoje = db.query(Presenca).filter(
        Presenca.turma_id == turma_id,
        Presenca.data == data_chamada
    ).all()
    map_presenca = {p.aluno_id: p.presente for p in presencas_hoje}

    lista_alunos = []
    for m in matriculas:
        status = map_presenca.get(m.aluno_id, False) 
        lista_alunos.append({
            "aluno_id": m.aluno_id,
            "nome": m.aluno.nome,
            "foto": m.aluno.foto, 
            "presente": status
        })
    return lista_alunos

@router.post("/chamada")
def salvar_chamada(
    dados: dict, # Espera { "turma_id": 1, "data": "2023-10-27", "presencas": [ { "aluno_id": 1, "presente": true } ] }
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(auth.get_current_active_user)
):
    turma_id = dados.get("turma_id")
    data_str = dados.get("data")
    lista_presencas = dados.get("presencas", [])

    try:
        data_chamada = datetime.strptime(data_str, '%Y-%m-%d').date()
    except:
        data_chamada = datetime.utcnow().date()

    # Vamos usar a estratégia de "Apagar e Recriar" ou "Atualizar" para o dia.
    # Mais simples: Verifica um por um.
    
    for item in lista_presencas:
        aluno_id = item.get("aluno_id")
        veio = item.get("presente")

        # Busca se já existe registro
        registro = db.query(Presenca).filter(
            Presenca.turma_id == turma_id,
            Presenca.aluno_id == aluno_id,
            Presenca.data == data_chamada
        ).first()

        if registro:
            registro.presente = veio
        else:
            novo_registro = Presenca(
                turma_id=turma_id,
                aluno_id=aluno_id,
                data=data_chamada,
                presente=veio
            )
            db.add(novo_registro)
    
    db.commit()
    return {"status": "sucesso", "mensagem": "Chamada salva com sucesso!"}


@router.get("/turmas")
def list_turmas_professor(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_staff)
):
    """
    Lista todas as turmas ativas para preencher o dropdown da chamada.
    """
    # Importante: certifique-se que 'Turma' está importado no topo do arquivo
    return db.query(Turma).filter(Turma.ativa == True).order_by(Turma.nome).all()


@router.get("/alunos/buscar")
def buscar_alunos_global(nome: str, db: Session = Depends(get_db)):
    # Busca qualquer aluno ativo que contenha o nome digitado
    alunos = db.query(Aluno).filter(
        Aluno.nome.ilike(f"%{nome}%"),
        Aluno.status == 'Ativo'
    ).limit(10).all()
    
    return [{"id": a.id, "nome": a.nome, "foto": a.foto} for a in alunos]


@router.get("/alunos/buscar-global")
def buscar_alunos_chamada_extra(nome: str, db: Session = Depends(get_db)):
    try:
        # Busca alunos que contenham o nome e estejam ativos
        alunos = db.query(Aluno).filter(
            Aluno.nome.ilike(f"%{nome}%"),
            Aluno.status == 'Ativo'
        ).limit(10).all()
        
        return [{"id": a.id, "nome": a.nome, "foto": a.foto} for a in alunos]
    except Exception as e:
        print(f"Erro na busca: {e}")
        return []
# ------------------------------------