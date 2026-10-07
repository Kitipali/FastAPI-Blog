from __future__ import annotations
# hace que Python posponga la evaluación de las anotaciones de tipo
from typing import List, TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import  Mapped, mapped_column, relationship
from app.core.db import Base

if TYPE_CHECKING:
    from .post import PostORM

class TagORM(Base):
    __tablename__= "tags"
    id: Mapped[int]=mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str]= mapped_column(String(30), unique=True, index=True)
    
    # Como un post puede tener varias tags y cada tag puede estar en varios posts 
    # no podemos añadir un post_id en tags ni un tag_id en posts -> Relación de Muchos a Muchos
    # Necesitamos una tabla intermedoa
    posts: Mapped[List["PostORM"]] = relationship(
        secondary= "post_tags",
        back_populates= "tags", # posts.tags
        lazy="selectin"
        
    )
    

