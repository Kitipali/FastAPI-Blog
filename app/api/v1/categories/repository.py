from __future__ import annotations
# annotations Retrasa la evaluación de las anotaciones de tipo

from typing import Iterable, Sequence
# Sequence -> Representa una secuencia, como una lista o una tupla
from collections.abc import Iterable as IterableABC

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.category import CategoryORM


class CategoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db



    def list_many(self, *, skip: int = 0, limit: int = 50) -> Sequence[CategoryORM]:
    # * -> No vamos a recibir ningún argumento posicional sino los keyword arguments (explicar esto)
        query = (select(CategoryORM).offset(skip).limit(limit))
        return self.db.execute(query).scalars().all()

    def list_with_total(self, *, page: int = 1, per_page: int = 50) -> tuple[int, list[CategoryORM]]:
         # 1. Contar todas las categorías
        total_query = select(func.count()).select_from(CategoryORM)
        # .select_from(CategoryORM)-> indica sobre qué tabla queremos contar.
        total = self.db.execute(total_query).scalar_one()
        # Por qué .scalar_one() y no .scalars().all()?
        # Porque COUNT() devuelve una sola fila con un único número. No necesitamos 1 lista.

        # 2. Calcular cuántos registros debemos omitir
        skip = (page - 1) * per_page

        # 3. Obtener las categorías de la página solicitada
        query = (
            select(CategoryORM)
            .order_by(CategoryORM.id)
            .offset(skip)
            .limit(per_page)
        )

        categories = self.db.execute(query).scalars().all()
        # scalars().all(), porque queremos recuperar varios objetos CategoryORM.

        # 4. Devolver el total y la lista de categorías
        return total, list(categories)

    def get(self, category_id: int) -> CategoryORM | None:
        return self.db.get(CategoryORM, category_id) # busca por clave primaria

    def get_by_slug(self, slug: str) -> CategoryORM | None:
        query = select(CategoryORM).where(CategoryORM.slug == slug)
        return self.db.execute(query).scalars().first()

    def create(self, *, name: str, slug: str) -> CategoryORM:
       category = CategoryORM(name=name, slug=slug)
       self.db.add(category)
       self.db.flush() # obtenemos llave primaria sin necesidad de commit
       return category

    def update(self, category: CategoryORM, updates: dict) -> CategoryORM:
        #allowed_items = {"name", "slug"} : ejemplo de meter una validación, pero cómio seguiría?
        for key, value in updates.items():
            # if key not in  allowed_items
               # raise ValueError(f"Campo no permitido: {key}") 
            setattr(category, key, value)
        self.db.add(category)
        self.db.flush()
        return category
            

    def delete(self, category: CategoryORM) -> None:
        self.db.delete(category) 

