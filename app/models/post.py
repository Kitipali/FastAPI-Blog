from __future__ import annotations
from datetime import datetime

# hace que Python posponga la evaluación de las anotaciones de tipo
from typing import List, TYPE_CHECKING, Optional

from sqlalchemy import Integer, String, Text, DateTime, UniqueConstraint, ForeignKey, Table, Column
from sqlalchemy.orm import  Mapped, mapped_column, relationship
from app.core.db import Base

if TYPE_CHECKING:
    from .author import AuthorORM
    from .tag import TagORM


post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True ),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True )
    
)
# Aquí se crea la tabla intermedia que comentamos en TagORM
# No la creamos como una clase -> por ejempño PostTagORM
# Creamos una tabla de SQLAlchemy directamnete con Table()
# La llamamos "post_tags" y le decimos que pertence al conjunto de tablas que conocen Base
# ondelete=cascade -> si se elimina, por ejemplo, un Post de la BD, sus correspondientes relaciones
# en post_tags pueden eliminarse automáticamente
# Cada columna es primary key -> evita asociar dos veces el mismo tag al mismo post




class PostORM(Base): # Nuestra primera tabla
    __tablename__= "posts" # Esta clase corresponde a una tabla llamada posts.
    __table_args__ = (UniqueConstraint("title", name="unique_post_title"),)
    # añade una restricción de unicidad a la tabla: no podrá haber dos posts con el mismo title
        # "title" -> columna sobre la que se aplica Unique
        # "unique_post_title" -> nombre que tú das a la restricción
    # Ojo! es una tupla Porque __table_args__ está pensado para poder contener varias 
    # reglas/configuraciones de la tabla, no solamente una.
    # Una tupla puede recibir varios elementos pero si solo tiene 1 -> "," al final
    # Si intentas guardar un dato que viola esa restricción UNIQUE, 
    # SQLAlchemy normalmente lanza IntegrityError
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable= False, index=True)
    content: Mapped[str] = mapped_column(Text,nullable= False) # contenido del post puede ser mucho más largo y no quieres limitarlo a 100 caracteres. No puede ser Null
    created_at: Mapped[datetime] = mapped_column(DateTime, default= datetime.utcnow)
    
    
    # PostORM -> Modelo ORM q representa la tabla SQL posts
    # id es un atributo mapeado por SQLAlchemy cuyo valor será un int
    # mapped_column() describe como será su columna en la base de datos
        # Integer -> entero
        # primaryKey =true -> clave primaria
        # index=True -> crea un índice
    # Mapped -> Propiedad con tipo
    # mapped_column -> configurador
    author_id: Mapped[Optional[int]] = mapped_column(ForeignKey("authors.id"))
    # ForeignKey("authors.id") -> El valor almacenado en posts.author_id hace referencia a authors.id
    # se crea una columna real de author_id en la tabla osts y tiene un ForeignKey en authors.id
    author: Mapped[Optional["AuthorORM"]] = relationship(back_populates="posts")
    # author no es otra columna de la tabla. Es una relación ORM que te permite trabajar cómodamente
    # Podemos hacer posts.author.name aunque no exista la columna author en posts.
    # Relación 1(autor) a muchos n(posts)
    tags: Mapped[List["TagORM"]] = relationship(
        secondary=post_tags, # Para relacionar PostORM con TagORM, utiliza post_tags como tabla intermedia
        back_populates="posts", # se refiere al atributo del otro lado -> tag.posts -> todos los post c/ ese tag
        lazy="selectin", # técnica de carga de los datos relacionados, especialmente cuando obtienes varios objetos padre: select-in loading
        passive_deletes=True # Para respetar el ON DELETE CASCADE de la base de datos
    )
    # Cada objeto PostORM tendrá un atributo .tags que será una lista de objetos TagORM. 
    # SQLAlchemy obtiene esa lista utilizando la tabla intermedia post_tags.

# SQL alchemy se encargará de introducir los valores de esta clase en una tabla de sql



