
from datetime import datetime
from typing import List, Literal

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.post import PostORM

Role = Literal["user", "editor", "admin"]


class User(Base): # este modelo representa la Tabla user de mi Base de Datos
    __tablename__ ="users"
    id: Mapped[int] = mapped_column(primary_key= True)
    # id: Mapped[int] -> id es un atributo ORM cuyo valor esperado es un entero
    # mapped_column(primary_key=True) -> Configura cómo se representa ese atributo en 
    # la tabla SQL: en este caso, como clave primaria.
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False)
    # String(255) -> La columna almacena textos de hasta 255 caracteres
    # unique=True -> No permite repetir el mismo email en dos registros
    # nullable=False -> No permite guardar null
    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum("user", "editor", "admin", name="role_enum"), default="user")
    # el atributo role tiene uno de los tres valores previstos más arriba
    # Enum -> es de SQLAlchemy y limita lo que puede ir en la columna
    # name="role_enum" -> establece el nombre del tipo enumerado
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    posts: Mapped[List["PostORM"]] = relationship(back_populates="user")
    