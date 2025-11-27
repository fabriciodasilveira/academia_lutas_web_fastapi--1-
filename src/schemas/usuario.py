from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UsuarioBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50) # Novo campo obrigatório
    nome: Optional[str] = None
    role: str

class UsuarioCreate(UsuarioBase):
    password: str

class UsuarioUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None # Novo campo opcional na edição
    nome: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None

class UsuarioRead(UsuarioBase):
    id: int
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user_info: UsuarioRead