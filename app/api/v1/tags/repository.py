from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.v1.tags.schemas import TagPublic
from app.models.post import PostORM, post_tags
from app.models.tag import TagORM
from app.services.pagination import paginate_query

class TagRepository: # Hará consultas a la BD sobre las etiquetas
    def __init__(self, db: Session): #constructor para crear la sesión a la BD 
        self.db = db
    def get(self, tag_id: int)-> Optional[TagORM]:
        tag_find = select(TagORM).where(TagORM.id == tag_id)
        return self.db.execute(tag_find).scalar_one_or_none() # ejecutamos la consulta
    def list_tags(
        self,
        search: Optional[str], 
        order_by: str="id", 
        direction: str ="asc", 
        page: int =1, 
        per_page: int=10
    ):
        query = select(TagORM)
        if search:
            query = query.where(func.lower(
                TagORM.name).ilike(f"%{search.lower()}%"))
        allowed_order = {
            "id": TagORM.id,
            "name": func.lower(TagORM.name)
        }
        # Definimos las columnas permitidas para ordenar
        
        # llamamos al servicio de paginación
        result = paginate_query(
            db = self.db,
            model = TagORM,
            base_query = query,
            page = page,
            per_page = per_page,
            order_by = order_by,
            direction = direction,
            allowed_order = allowed_order     
        )
        # esto devuelve 
            #{
            # "total": 25,
            # "pages": 3,
            # "page": 1,
            # "per_page": 10,
            # "items": [tag_1, tag_2, ...]
            #}
        # Pero los elementos de "items" (results["items"]) todavía son objetos TagORM
        result["items"] = [TagPublic.model_validate(item) for item in result["items"]]
        # TagPublic.model_validate(item) -> Convierte y valida cada objeto TagORM como 
        # un objeto Pydantic TagPublic aprovechando que lo configuramos como
        # model_config = ConfigDict(from_attributes=True)
        # si no hacemos esto nos va a dar un serialization error
        
        return result
            
    def create_tag(self, name:str):
        normalized = name.strip().lower()
        # con el objeto post de Postcreate creamos un objeto ORM
        tag_obj = self.db.execute(
            select(TagORM).where(func.lower(TagORM.name) == normalized)
        ).scalar_one_or_none()
        # select(TagORM).where(TagORM.name.ilike(name)) -> Para postgre
        # Busca en tagORM un TagORM con el mismo nombre que name  y lo selecciona
        # trae algo o nada
        if tag_obj:
            return tag_obj
            
        tag_obj =TagORM(name=name) #lo crea con el nombre de tag
        self.db.add(tag_obj) # lo añade a la base de datos
        self.db.flush() # Envía los cambios pendientes a la BD sin confirmar todavía la transacción. 
        # Obtengo el tag_id pero todavía no hemos hecho commit()
        return tag_obj
    
    def update_tag(self, tag_id:int, name= str)-> Optional[TagORM]:
        tag = self.get(tag_id)
        if not tag:
            return None
        if name is not None:
            tag.name = name.strip().lower()
        self.db.add(tag) # redudnante porque tag ya está asociado a la sesión
        self.db.flush()
        self.db.refresh(tag)
        return tag
        
            
            
        
    def delete_tag(self, tag_id:int) -> bool:
        tag = self.get(tag_id)
        if not tag:
            return False
        self.db.delete(tag)
        return True

    def most_popular(self) -> dict | None:
        # Creamos una súper variable
        row = (
            self.db.execute(
                select( # qué columnas queremos obtener
                    TagORM.id.label("id"),
                    # .label() -> asignar un nombre al resultado de una expresión SQL
                    TagORM.name.label("name"),
                    func.count(PostORM.id).label ("uses")
                ) # Quiero obtener el identificador de la etiqueta, su nombre y contar identificaciones de publicaciones
                .join(post_tags, post_tags.c.tag_id == TagORM.id)
                # Relaciona las etiquetas con la tabla intermedia(post_tags)
                # .join(tabla_destino, condición_de_unión)
                # el tag_id de la tabla intermedia debe coincidir con el id de la etiqueta
                # .c -> la forma de acceder a las columnas de un objeto Table de SQLAlchemy
                .join(PostORM, PostORM.id == post_tags.c.post_id)
                # Relaciona esa tabla intermedia con las publicaciones
                .group_by(TagORM.id, TagORM.name)
                # Agrupa por las filas que correspondan a la mis etiqueta
                .order_by(func.count(PostORM.id).desc(), func.lower(TagORM.name).asc())
                # Hay 2 criterios de ordenación:
                    # 1) func.count(PostORM.id).desc() -> Ordena por número de usos, de mayor a menor.
                    # 2) func.lower(TagORM.name).asc() -> Si dos etiquetas tienen los mismos usos, las ordena alfabéticamente de la A a la Z.
                .limit(1) 
                # Nos quedamos con una sola 
                
            )
            .mappings()
            # convertimos a algo parecido a un diccionario -> un objeto RowMapping
            # self.db.execute(...) .> ejecuta consulta SQL contra la BD y ubtiene un objeto Result
            # .mappings() -> queremos acceder a los resultados como estructuras con claves, en lugar de tuplas ordinarias.
            .first()
            # obtenemos el primer elemento
            # recupera esa primera fila
        )
        
        return dict(row) if row else None
        # Para convertir de objeto RowMapping a diccionario