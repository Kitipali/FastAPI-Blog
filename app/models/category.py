

from sqlalchemy import Integer, String

from app.core.db import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship


class CategoryORM(Base):
    __tablename__= "categories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    # id ->	Identificador único de la categoría
    # name ->	Nombre de la categoría, por ejemplo, "Python"
    # slug ->	Identificador legible para URLs, por ejemplo, "python"
    # unique=True -> impide que se repita el valor de la columna correspondiente.
    # index=True -> crea un índice para facilitar las búsquedas.
    
    
    
    
    posts= relationship("PostORM", back_populates ="category", cascade= "all, delete", passive_deletes=True)
    # back_populates -> Vincula dos atributos de relación definidos en modelos diferentes.
    # cómo se va a acceder a las categorías a través de post
    # cascade="all, delete" -> Indica a SQLAlchemy que determinadas operaciones sobre 
    # una categoría se propaguen a sus posts relacionados, incluida la eliminación.
    # passive_deletes=True -> Cuando se elimina un objeto principal (categoría) al 
    # eliminar una categoría, SQLAlchemy evita cargar las colecciones de posts que 
    # todavía no estén cargadas y confía en que la base de datos gestione esas eliminaciones.
    
    
                        