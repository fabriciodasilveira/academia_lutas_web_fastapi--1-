# Crie o arquivo: src/models/usuario.py
from sqlalchemy import Column, Integer, String
from src.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    nome = Column(String)
    hashed_password = Column(String, nullable=True) # Nulo para logins sociais
    role = Column(String, nullable=False, default="pendente") # Define 'pendente' como padrão
