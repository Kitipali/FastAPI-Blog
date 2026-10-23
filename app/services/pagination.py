from math import ceil
from typing import Any, Dict, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session
DEFAULT_PER_PAGE = 10
MAX_PER_PAGE =100

# Este servicio sirve para reutilizar la paginación n veces
# Para tags, posts o cualquier otra cosa

def sanitize_pagination(page: int =1, per_page: int = DEFAULT_PER_PAGE):
    page = max(1, int(page or 1)) # nos aseguramos de que la página sea al menos 1
    per_page = min(MAX_PER_PAGE, max(1, int(per_page or DEFAULT_PER_PAGE)))
    return page, per_page
    
def paginate_query(
    db: Session,
    model, # queremos q sirva para cualquier modelo
    base_query = None, # la base de mi query -> Lo que ya tengo para buscar
    page: int = 1,
    per_page: int = DEFAULT_PER_PAGE,
    order_by: Optional[str]= None,
    direction: str ="asc",
    allowed_order: Optional[Dict[str, Any]]= None 
    # este parámetro puede recibir un diccionario o None
    # allowed_order es un diccionario q indica p q columnas permitimos ordenar 
    # los resultados de una consulta.
    # Dict[str, Any] -> En el diccionario:
        # Las claves son string
        # Los valores pueden ser de cualquier tipo
    
    
):
    page, per_page = sanitize_pagination(page, per_page)
    query = base_query if base_query is not None else select(model)
    # Si ya has preparado una consulta, utiliza esa consulta.
    # Si no, crea una consulta para obtener todos los registros del modelo.
    # P. ej, si model = TagORM, la consulta predeterminada equivale a 
    # seleccionar todas las etiquetas.
    
    total = db.scalar(select(func.count()).select_from(model)) or 0
    # Cuenta cuántos registros hay en la tabla.
    
    if total ==0:
        return {"total": 0, "pages":0, "page": page, "per_page": per_page, "items": []}
    
    if allowed_order and order_by:
        col = allowed_order.get(order_by, allowed_order.get("id"))
        # diccionario.get(clave, valor_por_defecto)
        # 1er argumento -> la clave que queremos buscar.
        # 2o argumento -> qué devolver si esa clave no existe
        # col -> columna por la que queremos ordenar
        
        query = query.order_by(col.desc() if direction == "desc" 
                               else col.asc())
        # Añade a la consulta una ordenación por la columna seleccionada.
        # Si direction es "desc", ordena de forma descendente.
        # En cualquier otro caso, ordena de forma ascendente.
        # Todavía no ejecuta la consulta.
    
    items = db.execute(query.offset((page-1)*per_page). limit(per_page)).scalars().all()
    # Obtiene únicamente los registros correspondientes a la página solicitada.
    
    return {
        "total": total, 
        "pages":ceil(total/per_page), 
        "page": page, 
        "per_page": per_page, 
        "items": items
        }
        