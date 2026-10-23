
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from app.api.v1.tags import repository
from app.api.v1.tags.repository import TagRepository
from app.core.db import get_db
from app.core.security import get_current_user, require_admin, require_editor, require_user
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.tags.schemas import TagCreate, TagPublic, TagUpdate
from app.models.user import User


router = APIRouter(prefix="/tags", tags=["tags"])

@router.get("", response_model=dict)
def list_tags(
    page: int = Query(1, ge=1),
    per_page: int = Query (10, ge=1, le=100),
    order_by: str = Query("id", pattern="^(id|name)$"),
    direction: str = Query("asc", pattern="(asc|desc)$"),
    search: str | None = Query(None),
    db: Session = Depends (get_db)
    # pattern -> para validar el texto que introduce el usuario mediante una 
    # expresión regular (regex).
    # ^ -> el texto debe comenzar aquí
    # (agrupa varias alternativas): Id y Nem
    # | -> o
    # $ -> el texto termsina aquí
):
    repository = TagRepository(db)
    return repository.list_tags(page=page, per_page=per_page,order_by=order_by, direction=direction, search=search)
    

# Creamos la routa para nuestro post
@router.post("", response_model=TagPublic, response_description="Post creado (OK)", status_code= status.HTTP_201_CREATED)
def create_tag(tag:TagCreate, db: Session = Depends(get_db), _editor: User = Depends(require_editor)):
    repository = TagRepository(db)
    try:
        tag_created = repository.create_tag(name=tag.name)
        db.commit()
        db.refresh(tag_created)
        return tag_created
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al crear el tag")
    
@router.put("/{tag_id}", response_model=TagPublic, response_description= "Tag modificada (OK)", status_code= status.HTTP_200_OK)
def update_tag(tag: TagUpdate,db: Session = Depends(get_db), _editor: User = Depends(require_editor), tag_id: int = Path(
        ...,
        ge=1, # greater or equal -> Mayor o igual que
        title = "ID del tag",
        description= "Identificador entero del tag. Debe ser mayor o igual a 1",
        example = 1), 
    ):
    repository = TagRepository(db)
    try:
            tag_updated = repository.update_tag(tag_id=tag_id,name=tag.name)
            if tag_updated is None:
                raise HTTPException(
                status_code=404,
                detail="Etiqueta no encontrada")   
            db.commit()
            return TagPublic.model_validate(tag_updated)
            # model.validate() -> Crea un objeto Pydantic a partir de ls datos dl ORM
    except SQLAlchemyError:
            db.rollback()
            raise HTTPException(status_code=500, detail="Error al modificar el tag")
    
    
@router.delete("/{tag_id}", status_code= status.HTTP_204_NO_CONTENT)
def eliminate_tag(db: Session = Depends(get_db), _admin: User = Depends(require_admin), tag_id: int = Path(
    ...,
    ge=1, # greater or equal -> Mayor o igual que
    title = "ID del tag",
    description= "Identificador entero del tag. Debe ser mayor o igual a 1",
    example = 1), 
):
    
    repository = TagRepository(db)
    try:
            tag_deleted = repository.delete_tag(tag_id)
            if not tag_deleted :
                raise HTTPException(
                status_code=404,
                detail="Etiqueta no encontrada")   
            db.commit()
            return None # estamos poniendo status no content
    except SQLAlchemyError:
            db.rollback()
            raise HTTPException(status_code=500, detail="Error al eliminar el tag")

@router.get("/popular/top") 
def get_most_popular_tag(
    db: Session = Depends(get_db),
    _user: User = Depends(require_user)
):
    repository =  TagRepository(db)
    row = repository.most_popular()
    if not row:
        raise HTTPException(status_code=404, detail ="No hay tags en uso")
    return row
    