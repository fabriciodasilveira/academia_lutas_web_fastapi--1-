# src/routes/eventos_fastapi.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from datetime import datetime

from src.database import get_db
from src.models.evento import Evento
from src.schemas.evento import EventoCreate, EventoRead, EventoUpdate

router = APIRouter(
    tags=["Eventos"],
    prefix="/eventos"
)

@router.post("", response_model=EventoRead, status_code=status.HTTP_201_CREATED)
def create_evento(evento: EventoCreate, db: Session = Depends(get_db)):
    db_evento = Evento(**evento.dict())
    db.add(db_evento)
    db.commit()
    db.refresh(db_evento)
    return db_evento

@router.get("", response_model=List[EventoRead])
def read_eventos(db: Session = Depends(get_db)):
    eventos = db.query(Evento).options(joinedload(Evento.inscricoes)).order_by(Evento.data_evento.desc()).all()
    return eventos

@router.get("/{evento_id}", response_model=EventoRead)
def read_evento(evento_id: int, db: Session = Depends(get_db)):
    db_evento = db.query(Evento).options(joinedload(Evento.inscricoes)).filter(Evento.id == evento_id).first()
    if db_evento is None:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    return db_evento

@router.put("/{evento_id}", response_model=EventoRead)
def update_evento(evento_id: int, evento: EventoUpdate, db: Session = Depends(get_db)):
    db_evento = db.query(Evento).filter(Evento.id == evento_id).first()
    if db_evento is None:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    
    update_data = evento.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_evento, key, value)
        
    db.commit()
    db.refresh(db_evento)
    return db_evento

@router.delete("/{evento_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evento(evento_id: int, db: Session = Depends(get_db)):
    db_evento = db.query(Evento).filter(Evento.id == evento_id).first()
    if db_evento is None:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    db.delete(db_evento)
    db.commit()
    return None