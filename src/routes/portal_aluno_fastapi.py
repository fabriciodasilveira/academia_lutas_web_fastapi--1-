from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src import database, models, auth
from src.schemas import portal_aluno as schemas_portal
from src.schemas import aluno as schemas_aluno

router = APIRouter(
    prefix="/api/v1/portal",
    tags=["Portal do Aluno"]
)

@router.post("/register", response_model=schemas_aluno.AlunoRead, status_code=status.HTTP_201_CREATED)
def register_aluno(aluno_data: schemas_portal.AlunoRegistration, db: Session = Depends(database.get_db)):
    db_user = auth.get_user(db, email=aluno_data.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este email já está cadastrado no sistema."
        )

    hashed_password = auth.get_password_hash(aluno_data.password)
    new_user = models.usuario.Usuario(
        email=aluno_data.email,
        nome=aluno_data.nome,
        hashed_password=hashed_password,
        role="aluno"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    new_aluno = models.aluno.Aluno(
        usuario_id=new_user.id,
        nome=aluno_data.nome,
        email=aluno_data.email,
        telefone=aluno_data.telefone,
        data_nascimento=aluno_data.data_nascimento
    )
    db.add(new_aluno)
    db.commit()
    db.refresh(new_aluno)
    
    return new_aluno


@router.get("/me", response_model=schemas_aluno.AlunoRead)
def get_current_aluno_profile(
    current_user: models.usuario.Usuario = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != "aluno":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")

    aluno_profile = db.query(models.aluno.Aluno).filter(models.aluno.Aluno.usuario_id == current_user.id).first()
    if not aluno_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de aluno não encontrado.")
        
    return aluno_profile


@router.put("/me", response_model=schemas_aluno.AlunoRead)
def update_current_aluno_profile(
    aluno_update: schemas_aluno.AlunoUpdate,
    current_user: models.usuario.Usuario = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != "aluno":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")

    db_aluno = db.query(models.aluno.Aluno).filter(models.aluno.Aluno.usuario_id == current_user.id).first()
    if not db_aluno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de aluno não encontrado.")

    update_data = aluno_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_aluno, key, value)
    
    db.commit()
    db.refresh(db_aluno)
    return db_aluno