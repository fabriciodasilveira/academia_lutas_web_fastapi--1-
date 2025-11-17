from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from src.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    
    # 1. NOVO CAMPO PARA LOGIN (OBRIGATÓRIO E ÚNICO)
    username = Column(String, unique=True, index=True, nullable=False)
    
    # 2. E-mail continua sendo único, mas não é mais a chave de login
    email = Column(String, unique=True, index=True, nullable=False)
    
    nome = Column(String)
    hashed_password = Column(String, nullable=True) 
    role = Column(String, nullable=False, default="pendente")

    # 3. Relação revertida para "um-para-um" (aluno, singular)
    aluno = relationship("Aluno", back_populates="usuario", uselist=False)