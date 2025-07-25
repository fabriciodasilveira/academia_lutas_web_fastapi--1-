# -*- coding: utf-8 -*-
"""
Rotas FastAPI para o CRUD de Eventos e Fotos.
"""

import os
import shutil
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import logging

from src.database import get_db
from src.models.evento import Evento, Foto
from src.schemas.evento import EventoCreate, EventoRead, EventoUpdate, FotoCreate, FotoRead, FotoUpdate

# Configuração de diretórios - CORRIGIDO
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR_EVENTOS = BASE_DIR / "src" / "static" / "uploads" / "eventos"

# Garante que o diretório existe - CORRIGIDO
try:
    UPLOAD_DIR_EVENTOS.mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(f"Erro ao criar diretório de uploads de eventos: {e}")
    # Fallback para diretório temporário
    UPLOAD_DIR_EVENTOS = Path("/tmp/academia_uploads/eventos")
    UPLOAD_DIR_EVENTOS.mkdir(parents=True, exist_ok=True)

router = APIRouter(
    prefix="/api/v1/eventos",
    tags=["Eventos"],
    responses={404: {"description": "Não encontrado"}},
)

# --- Helper Function --- 
def save_upload_file(upload_file: UploadFile, destination: Path) -> None:
    """Salva um arquivo de upload no destino especificado."""
    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()

# --- CRUD Endpoints para Eventos --- 

@router.post("", response_model=EventoRead, status_code=status.HTTP_201_CREATED)
def create_evento(
    titulo: str = Form(...),
    descricao: Optional[str] = Form(None),
    data_evento: str = Form(...),  # Recebe como string, converte depois
    local: Optional[str] = Form(None),
    modalidades: Optional[str] = Form(None),
    status: Optional[str] = Form("agendado"),
    fotos: List[UploadFile] = File([]),  # Lista de arquivos de fotos (opcional)
    db: Session = Depends(get_db)
):
    """
    Cria um novo evento com possibilidade de upload de múltiplas fotos.
    """
    # Converte data do evento
    try:
        parsed_data_evento = datetime.strptime(data_evento, "%Y-%m-%dT%H:%M")
    except ValueError:
        try:
            parsed_data_evento = datetime.strptime(data_evento, "%Y-%m-%d %H:%M")
        except ValueError:
            try:
                parsed_data_evento = datetime.strptime(data_evento, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Formato de data inválido. Use YYYY-MM-DDThh:mm, YYYY-MM-DD hh:mm ou YYYY-MM-DD"
                )

    # Cria o evento
    evento_data = {
        "titulo": titulo,
        "descricao": descricao,
        "data_evento": parsed_data_evento,
        "local": local,
        "modalidades": modalidades,
        "status": status
    }
    
    db_evento = Evento(**evento_data)
    db.add(db_evento)
    db.commit()
    db.refresh(db_evento)
    
    # Processa upload de fotos se houver
    fotos_ids = []
    for foto in fotos:
        if foto.filename:  # Verifica se o arquivo tem nome (não está vazio)
            # Cria diretório específico para o evento se não existir
            evento_dir = UPLOAD_DIR_EVENTOS / str(db_evento.id)
            evento_dir.mkdir(exist_ok=True)
            
            # Define um nome de arquivo seguro
            base, ext = os.path.splitext(foto.filename)
            safe_base = "".join(c if c.isalnum() or c in ('_', '-') else '' for c in base)[:50]
            filename = f"{safe_base}_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"
            file_location = evento_dir / filename
            
            # Salva o arquivo
            save_upload_file(foto, file_location)
            
            # Cria registro da foto no banco
            db_foto = Foto(
                evento_id=db_evento.id,
                caminho_arquivo=f"/static/uploads/eventos/{db_evento.id}/{filename}",
                legenda=None,
                destaque=False
            )
            
            db.add(db_foto)
            db.commit()
            db.refresh(db_foto)
            fotos_ids.append(db_foto.id)
    
    # Recarrega o evento para incluir as fotos na resposta
    db.refresh(db_evento)
    
    return db_evento

# ... (mantenha os outros endpoints como estão, mas substitua os caminhos hardcoded)

@router.delete("/{evento_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evento(evento_id: int, db: Session = Depends(get_db)):
    """
    Exclui um evento e todas as suas fotos.
    """
    db_evento = db.query(Evento).filter(Evento.id == evento_id).first()
    if db_evento is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento não encontrado")

    # Remove os arquivos físicos das fotos - CORRIGIDO
    evento_dir = UPLOAD_DIR_EVENTOS / str(evento_id)
    if evento_dir.exists():
        try:
            shutil.rmtree(evento_dir)
        except OSError as e:
            print(f"Erro ao remover diretório de fotos {evento_dir}: {e}")

    # O cascade="all, delete-orphan" no modelo Evento cuidará de excluir as fotos do banco
    db.delete(db_evento)
    db.commit()
    
    return None

@router.delete("/{evento_id}/fotos/{foto_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_foto(evento_id: int, foto_id: int, db: Session = Depends(get_db)):
    """
    Remove uma foto específica de um evento.
    """
    db_foto = db.query(Foto).filter(Foto.id == foto_id, Foto.evento_id == evento_id).first()
    if db_foto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Foto não encontrada ou não pertence ao evento especificado"
        )
    
    # Remove o arquivo físico - CORRIGIDO
    if db_foto.caminho_arquivo:
        foto_path = BASE_DIR / db_foto.caminho_arquivo.lstrip('/')
        if foto_path.exists():
            try:
                foto_path.unlink()
            except OSError as e:
                print(f"Erro ao remover foto {foto_path}: {e}")
    
    db.delete(db_foto)
    db.commit()
    
    return None