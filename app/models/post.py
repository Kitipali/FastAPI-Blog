from __future__ import annotations
from datetime import datetime

# hace que Python posponga la evaluación de las anotaciones de tipo
from typing import List, TYPE_CHECKING, Optional

from sqlalchemy import Integer, String, Text, DateTime, UniqueConstraint, ForeignKey, Table, Column
from sqlalchemy.orm import  Mapped, mapped_column, relationship
from app.core.db import Base

if TYPE_CHECKING:
    from .user import User
    from .tag import TagORM
    from .category import  CategoryORM
# TYPE_CHECKING es una constante del módulo typing que permite importar clases únicamente
# para comprobar tipos, sin ejecutar esas importaciones cuando funciona el programa.
    


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
    slug: Mapped[str] = mapped_column(String(160), unique=True, index= True)
    content: Mapped[str] = mapped_column(Text,nullable= False) # contenido del post puede ser mucho más largo y no quieres limitarlo a 100 caracteres. No puede ser Null
    image_url= mapped_column(String(300), nullable=True)
    # Crea conceptualmente una nueva columna
    # Lo que se guarda en PostgreSQL NO es la imagen sino una cadena de texto
    # por ejemplo /media/a83f.jpeg 
    # mientras que el real está en  app/media/a83f.jpeg
    # gracias a que en main.py hicimos -> app.mount("/media", StaticFiles(directory= MEDIA_DIR), name="media")
    # nullable=True -> Puede haber post sin imagen
    created_at: Mapped[datetime] = mapped_column(DateTime, default= datetime.utcnow)
    
    
    # PostORM -> Modelo ORM q representa la tabla SQL posts
    # id es un atributo mapeado por SQLAlchemy cuyo valor será un int
    # mapped_column() describe como será su columna en la base de datos
        # Integer -> entero
        # primaryKey =true -> clave primaria
        # index=True -> crea un índice
    # Mapped -> Propiedad con tipo
    # mapped_column -> configurador
    
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    # ForeignKey("users.id") -> El valor almacenado en posts.users_id hace referencia a users.id
    # se crea una columna real de users_id en la tabla posts y tiene un ForeignKey en users.id
    user: Mapped[Optional["User"]] = relationship(back_populates="posts")
    # user no es otra columna de la tabla. Es una relación ORM que te permite trabajar cómodamente
    # Podemos hacer posts.users.name aunque no exista la columna author en posts.
    # Relación 1(user) a muchos n(posts)
    
    category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    # ondelete="SET NULL" -> Significa que, si se elimina una categoría, la base de datos
    # debe poner category_id = NULL en los posts asociados, en lugar de eliminarlos.
    
    category = relationship("CategoryORM", back_populates="posts")
    
    tags: Mapped[List["TagORM"]] = relationship(
        secondary=post_tags, # Para relacionar PostORM con TagORM, utiliza post_tags como tabla intermedia
        back_populates="posts", # se refiere al atributo del otro lado -> tag.posts -> todos los post c/ ese tag
        lazy="selectin", # técnica de carga de los datos relacionados, especialmente cuando obtienes varios objetos padre: select-in loading
        passive_deletes=True # Para respetar el ON DELETE CASCADE de la base de datos
    )
    # Cada objeto PostORM tendrá un atributo .tags que será una lista de objetos TagORM. 
    # SQLAlchemy obtiene esa lista utilizando la tabla intermedia post_tags.

# SQL alchemy se encargará de introducir los valores de esta clase en una tabla de sql



