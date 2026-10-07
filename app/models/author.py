
from __future__ import annotations
# hace que Python posponga la evaluación de las anotaciones de tipo
from typing import List, TYPE_CHECKING
from sqlalchemy import Integer, String
from sqlalchemy.orm import  Mapped, mapped_column, relationship
from app.core.db import Base

if TYPE_CHECKING:
    from .post import PostORM
# para que el editor/type checker pueda conocer PostORM sin importar 
# realmente PostORM cuando se ejecuta el programa, evitando en este caso problemas de
# imports circulares.
# Junto con from __future__ import annotations -> Permiten tipar relaciones entre 
# modelos que se referencian mutuamente evitando imports circulares.


class AuthorORM(Base):
    __tablename__= "authors"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique= True)
    # tenemos que enlazar esta tabla con la tabla "posts"                                   
    posts: Mapped[List["PostORM"]] = relationship(back_populates="author")
    # posts va a ser una lista de objetos de tipo ORM -> Un autor puede tener muchos posts
    # Relación de 1 a muchos (N PostORM)
    # relationship(...)-> de SQLAlchemy -> Crea relación entre objetos Python
    # back_populates="author" -> Esta relación tiene su pareja en el atributo author de PostORM
