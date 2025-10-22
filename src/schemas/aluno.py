# src/schemas/aluno.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List # Adicione List
from datetime import date, datetime

# --- NOVO: Schema Mínimo para Listar Dependentes ---
class AlunoDependenteRead(BaseModel):
    id: int
    nome: str
    foto: Optional[str] = None

    class Config:
        from_attributes = True
# --- FIM DO NOVO SCHEMA ---

class AlunoBase(BaseModel):
    nome: str = Field(..., max_length=100)
    data_nascimento: Optional[date] = None
    cpf: Optional[str] = Field(None, max_length=14)
    telefone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None # Permitir None
    endereco: Optional[str] = Field(None, max_length=255)
    observacoes: Optional[str] = Field(None, max_length=255)
    nome_responsavel: Optional[str] = Field(None, max_length=100)
    cpf_responsavel: Optional[str] = Field(None, max_length=14)
    parentesco_responsavel: Optional[str] = Field(None, max_length=50)
    telefone_responsavel: Optional[str] = Field(None, max_length=20)
    email_responsavel: Optional[EmailStr] = None
    responsavel_aluno_id: Optional[int] = None # Adiciona o campo para vínculo

class AlunoCreate(AlunoBase):
    # Opcional: Adicionar senha se a criação via API também criar o usuário
    # password: Optional[str] = None
    pass

class AlunoRead(AlunoBase):
    id: int
    data_cadastro: Optional[datetime] = None
    foto: Optional[str] = None
    idade: Optional[int] = None
    status_geral: str = "Inativo"

    # --- ADICIONA INFORMAÇÕES DE FAMÍLIA ---
    # Quem é o responsável por ESTE aluno (se houver)
    responsavel: Optional[AlunoDependenteRead] = None
    # Quem são os dependentes DESTE aluno (se houver)
    dependentes: List[AlunoDependenteRead] = []
    # --- FIM DAS ADIÇÕES ---

    class Config:
        from_attributes = True

class AlunoUpdate(BaseModel):
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
    responsavel_aluno_id: Optional[int] = None # Permite atualizar/remover vínculo

class AlunoPaginated(BaseModel):
    total: int
    alunos: List[AlunoRead] # Usa AlunoRead para ter os dados de família na lista

    class Config:
        from_attributes = True