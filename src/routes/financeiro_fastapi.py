# src/routes/financeiro_fastapi.py
# -*- coding: utf-8 -*-
import os
import boto3 # Import necessário para o upload
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from datetime import datetime
from pydantic import BaseModel

from src.database import get_db
from src.models.financeiro import Financeiro
from src.schemas.financeiro import FinanceiroCreate, FinanceiroRead, FinanceiroUpdate
from src.models.mensalidade import Mensalidade
from src.models.usuario import Usuario
from src import auth
from src import image_utils 

router = APIRouter(
    tags=["Financeiro"],
    responses={404: {"description": "Não encontrado"}},
)

# --- SCHEMA AUXILIAR PARA O DROPDOWN ---
class StaffSelect(BaseModel):
    id: int
    nome: str
    role: str

    class Config:
        orm_mode = True

# --- Endpoint para preencher o Dropdown ---
@router.get("/staff", response_model=List[StaffSelect])
def get_staff_users(db: Session = Depends(get_db)):
    """Retorna lista de usuários com perfil de staff."""
    staff = db.query(Usuario).filter(
        or_(
            func.lower(Usuario.role) == 'professor',
            func.lower(Usuario.role) == 'administrador',
            func.lower(Usuario.role) == 'gerente',
            func.lower(Usuario.role) == 'atendente'
        )
    ).order_by(Usuario.nome).all()
    return staff

# --- CRUD Endpoints --- 

@router.post("/transacoes", response_model=FinanceiroRead, status_code=status.HTTP_201_CREATED)
def create_transacao(
    transacao: FinanceiroCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(auth.get_current_active_user)
):
    if transacao.tipo not in ['receita', 'despesa']:
        raise HTTPException(status_code=400, detail="Tipo inválido.")
    
    if not transacao.data:
        transacao.data = datetime.utcnow()
    
    transacao_data = transacao.dict()
    transacao_data['responsavel_id'] = current_user.id 
    
    db_transacao = Financeiro(**transacao_data)
    db.add(db_transacao)
    db.commit()
    db.refresh(db_transacao)
    return db_transacao


@router.post("/lancar-despesa", response_model=FinanceiroRead, status_code=status.HTTP_201_CREATED)
async def create_despesa_com_comprovante(
    descricao: str = Form(...),
    valor: float = Form(...),
    categoria: str = Form(...),
    data: Optional[str] = Form(None),
    forma_pagamento: str = Form(...),
    observacoes: Optional[str] = Form(None),
    arquivo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(auth.get_current_active_user)
):
    # Processa a data
    data_final = datetime.utcnow()
    if data:
        try:
            data_final = datetime.strptime(data, "%Y-%m-%d")
        except:
            pass

    url_comprovante = None

    # --- LÓGICA DE UPLOAD (CÓPIA IDÊNTICA AO ALUNOS_FASTAPI.PY) ---
    if arquivo and arquivo.filename:
        # 1. Processa a imagem (Redimensiona)
        # Usamos um tamanho maior (800x1200) pois recibos precisam de leitura
        processed_image, mime_type = image_utils.process_avatar_image(
            arquivo.file, 
            max_size=(800, 1200)
        )
        
        if processed_image:
            # 2. Pega as credenciais do ambiente
            s3_endpoint_url = os.getenv("S3_ENDPOINT_URL")
            s3_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
            s3_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
            s3_bucket_name = os.getenv("S3_BUCKET_NAME")
            public_bucket_url = os.getenv("PUBLIC_BUCKET_URL")

            # Valida configuração
            if all([s3_endpoint_url, s3_access_key_id, s3_secret_access_key, s3_bucket_name, public_bucket_url]):
                try:
                    # 3. Conecta ao S3/R2
                    s3_client = boto3.client(
                        's3', 
                        endpoint_url=s3_endpoint_url, 
                        aws_access_key_id=s3_access_key_id, 
                        aws_secret_access_key=s3_secret_access_key, 
                        region_name="auto"
                    )
                    
                    # 4. Gera nome seguro e faz Upload
                    base_filename, _ = os.path.splitext(arquivo.filename)
                    # Ex: despesa_1_17200000_nomearquivo.jpg
                    safe_filename = f"despesa_{current_user.id}_{int(datetime.utcnow().timestamp())}_{base_filename.replace(' ', '_')}.jpg"

                    s3_client.upload_fileobj(
                        processed_image, 
                        s3_bucket_name, 
                        safe_filename, 
                        ExtraArgs={'ContentType': mime_type}
                    )
                    
                    # 5. Define a URL final
                    url_comprovante = f"{public_bucket_url.rstrip('/')}/{safe_filename}"
                    print(f"Upload Sucesso: {url_comprovante}")
                    
                except Exception as e:
                    print(f"Erro no upload para o R2 (financeiro): {e}")
            else:
                print("Configuração de nuvem incompleta. Imagem não enviada.")
    # --- FIM DA LÓGICA DE UPLOAD ---

    nova_despesa = Financeiro(
        tipo='despesa',
        categoria=categoria,
        valor=valor,
        descricao=descricao,
        data=data_final,
        forma_pagamento=forma_pagamento,
        observacoes=observacoes,
        responsavel_id=current_user.id,
        comprovante_url=url_comprovante
    )
    
    db.add(nova_despesa)
    db.commit()
    db.refresh(nova_despesa)
    
    return nova_despesa

@router.get("/transacoes", response_model=List[FinanceiroRead])
def read_transacoes(skip: int = 0, limit: int = 100, tipo: Optional[str] = None, categoria: Optional[str] = None, busca: Optional[str] = None, data_inicio: Optional[str] = None, data_fim: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Financeiro)
    if tipo: query = query.filter(Financeiro.tipo == tipo)
    if categoria: query = query.filter(Financeiro.categoria == categoria)
    if busca: query = query.filter((Financeiro.descricao.ilike(f"%{busca}%")) | (Financeiro.observacoes.ilike(f"%{busca}%")))
    
    if data_inicio:
        try: query = query.filter(Financeiro.data >= datetime.strptime(data_inicio, "%Y-%m-%d"))
        except: pass
    if data_fim:
        try: query = query.filter(Financeiro.data <= datetime.strptime(data_fim, "%Y-%m-%d"))
        except: pass
    
    return query.order_by(Financeiro.data.desc()).offset(skip).limit(limit).all()

@router.get("/transacoes/{transacao_id}", response_model=FinanceiroRead)
def read_transacao(transacao_id: int, db: Session = Depends(get_db)):
    db_transacao = db.query(Financeiro).filter(Financeiro.id == transacao_id).first()
    if not db_transacao: raise HTTPException(status_code=404, detail="Não encontrado")
    return db_transacao

@router.put("/transacoes/{transacao_id}", response_model=FinanceiroRead)
def update_transacao(transacao_id: int, dados: FinanceiroUpdate, db: Session = Depends(get_db)):
    db_transacao = db.query(Financeiro).filter(Financeiro.id == transacao_id).first()
    if not db_transacao: raise HTTPException(status_code=404, detail="Não encontrado")
    
    for key, value in dados.dict(exclude_unset=True).items():
        setattr(db_transacao, key, value)
    
    db.commit()
    db.refresh(db_transacao)
    return db_transacao

@router.delete("/transacoes/{transacao_id}", status_code=204)
def delete_transacao(transacao_id: int, db: Session = Depends(get_db)):
    db_transacao = db.query(Financeiro).filter(Financeiro.id == transacao_id).first()
    if not db_transacao: raise HTTPException(status_code=404, detail="Não encontrado")
    
    # (Opcional) Poderíamos deletar a imagem do S3 aqui também, similar ao delete_aluno
    
    db.delete(db_transacao)
    db.commit()

@router.get("/balanco", response_model=dict)
def get_balanco(data_inicio: Optional[str] = None, data_fim: Optional[str] = None, db: Session = Depends(get_db)):
    hoje = datetime.utcnow().date()
    primeiro_dia = hoje.replace(day=1)
    
    try:
        d_ini = datetime.strptime(data_inicio, "%Y-%m-%d").date() if data_inicio else primeiro_dia
        d_fim = datetime.strptime(data_fim, "%Y-%m-%d").date() if data_fim else hoje
    except:
        d_ini = primeiro_dia
        d_fim = hoje

    receitas = db.query(func.sum(Financeiro.valor)).filter(Financeiro.tipo == 'receita', func.date(Financeiro.data) >= d_ini, func.date(Financeiro.data) <= d_fim).scalar() or 0.0
    despesas = db.query(func.sum(Financeiro.valor)).filter(Financeiro.tipo == 'despesa', func.date(Financeiro.data) >= d_ini, func.date(Financeiro.data) <= d_fim).scalar() or 0.0
    total_trans = db.query(func.count(Financeiro.id)).filter(func.date(Financeiro.data) >= d_ini, func.date(Financeiro.data) <= d_fim).scalar() or 0
    pendentes = db.query(Mensalidade).filter(Mensalidade.status == 'pendente', Mensalidade.data_vencimento <= hoje).count()
    
    cats = db.query(Financeiro.categoria, func.sum(Financeiro.valor)).filter(Financeiro.tipo == 'despesa', func.date(Financeiro.data) >= d_ini, func.date(Financeiro.data) <= d_fim).group_by(Financeiro.categoria).all()
    grafico_data = {c: v for c, v in cats}

    equipe = db.query(Usuario).filter(
        or_(func.lower(Usuario.role) == 'professor', func.lower(Usuario.role) == 'administrador', func.lower(Usuario.role) == 'gerente')
    ).order_by(Usuario.nome).all()

    entradas_query = db.query(Financeiro.responsavel_id, func.sum(Financeiro.valor)).filter(
        Financeiro.tipo == 'receita', 
        Financeiro.forma_pagamento == 'Dinheiro'
    ).group_by(Financeiro.responsavel_id).all()
    map_entradas = {uid: val for uid, val in entradas_query}

    saidas_query = db.query(Financeiro.beneficiario_id, func.sum(Financeiro.valor_abatido_caixa)).filter(
        Financeiro.valor_abatido_caixa > 0
    ).group_by(Financeiro.beneficiario_id).all()
    map_saidas = {uid: val for uid, val in saidas_query}

    caixas = []
    total_caixas_virtuais = 0.0
    
    for membro in equipe:
        entrada = map_entradas.get(membro.id, 0.0)
        saida = map_saidas.get(membro.id, 0.0)
        saldo = (entrada or 0.0) - (saida or 0.0)
        
        caixas.append({
            "id": membro.id,
            "nome": membro.nome,
            "total": saldo
        })
        total_caixas_virtuais += saldo

    return {
        "receitas": receitas, "despesas": despesas, "saldo": receitas - despesas,
        "total_transacoes": total_trans, "mensalidades_pendentes": pendentes,
        "graficos": {"categorias": grafico_data},
        "caixas_virtuais": caixas, "total_caixas_virtuais": total_caixas_virtuais
    }