from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date
from typing import Union
from .mensalidade import MensalidadeRead
from .inscricao import InscricaoRead

class AlunoRegistration(BaseModel):
    nome: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    telefone: Optional[str] = None
    data_nascimento: Optional[date] = None
    
class PendenciaFinanceira(BaseModel):
    tipo: str # 'mensalidade' ou 'inscricao'
    id: int
    descricao: str
    data_vencimento: date
    valor: float
    status: str
    
    class Config:
        orm_mode = True

class PendenciaFinanceiraResponse(BaseModel):
    items: List[PendenciaFinanceira]