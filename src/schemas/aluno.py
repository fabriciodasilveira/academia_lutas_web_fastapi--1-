# src/schemas/aluno.py
from pydantic import BaseModel, Field, EmailStr, validator # Importe validator
from typing import Optional, List
from datetime import date, datetime

class AlunoDependenteRead(BaseModel):
    id: int
    nome: str
    foto: Optional[str] = None
    class Config: from_attributes = True

class AlunoBase(BaseModel):
    nome: str = Field(..., max_length=100)
    data_nascimento: Optional[date] = None
    cpf: Optional[str] = Field(None, max_length=14)
    telefone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None # Permite None
    endereco: Optional[str] = Field(None, max_length=255)
    observacoes: Optional[str] = Field(None, max_length=255)
    nome_responsavel: Optional[str] = Field(None, max_length=100)
    cpf_responsavel: Optional[str] = Field(None, max_length=14)
    parentesco_responsavel: Optional[str] = Field(None, max_length=50)
    telefone_responsavel: Optional[str] = Field(None, max_length=20)
    email_responsavel: Optional[EmailStr] = None
    responsavel_aluno_id: Optional[int] = None

    # --- NOVO VALIDADOR ---
    @validator('email', 'email_responsavel', pre=True)
    def empty_str_to_none(cls, v):
        """Converte strings vazias para None antes da validação principal."""
        if isinstance(v, str) and v.strip() == '':
            return None
        return v
    # --- FIM DO VALIDADOR ---

class AlunoCreate(AlunoBase):
    pass

class AlunoRead(AlunoBase):
    id: int
    data_cadastro: Optional[datetime] = None
    foto: Optional[str] = None
    idade: Optional[int] = None
    status_geral: str = "Inativo"
    responsavel: Optional[AlunoDependenteRead] = None
    dependentes: List[AlunoDependenteRead] = []
    class Config: from_attributes = True

class AlunoUpdate(BaseModel):
    # Campos existentes para update
    nome: Optional[str] = Field(None, max_length=100)
    data_nascimento: Optional[date] = None
    cpf: Optional[str] = Field(None, max_length=14)
    telefone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    endereco: Optional[str] = Field(None, max_length=255)
    observacoes: Optional[str] = Field(None, max_length=255)
    nome_responsavel: Optional[str] = Field(None, max_length=100)
    cpf_responsavel: Optional[str] = Field(None, max_length=14)
    parentesco_responsavel: Optional[str] = Field(None, max_length=50)
    telefone_responsavel: Optional[str] = Field(None, max_length=20)
    email_responsavel: Optional[EmailStr] = None
    responsavel_aluno_id: Optional[int] = None # None significa remover responsável

    # --- Aplica o mesmo validador ao Update ---
    @validator('email', 'email_responsavel', pre=True)
    def empty_str_to_none_update(cls, v):
        if isinstance(v, str) and v.strip() == '':
            return None
        return v
    # --- Fim do validador ---

class AlunoPaginated(BaseModel):
    total: int
    alunos: List[AlunoRead]
    class Config: from_attributes = True