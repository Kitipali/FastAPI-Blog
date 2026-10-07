# Vamos a crear nuestras funciones para poder acceder a ellas a través del router


from fastapi import HTTPException
from math import ceil
from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload, joinedload
from app.models import PostORM, AuthorORM, TagORM
# Para Python, app.models se refiere al paquete models, y 
# lo que ese paquete expone directamente viene de su __init__.py.
class PostRepository:
    def __init__(self, db:Session):
        self.db= db
    # Cada instancia de PostRepository recibe una sesión y la guarda    
    def get(self, post_id:int)  -> Optional[PostORM]: # quiero devolver un PostORM
        post_find= select(PostORM).where(PostORM.id == post_id)
        return self.db.execute(post_find).scalar_one_or_none() # Obtenemos el valor de un solo post
    
    def search(self,
            query: Optional[str], 
            order_by: str, 
            direction: str, 
            page: int, 
            per_page: int
    ) -> Tuple[int,List[PostORM]]: # nos de vuelve un entero(el total) y una lista de PostORM (los ítems)
        results = select(PostORM)
        # Construye una consulta SQLAlchemy como -> SELECT * FROM posts
        
        if query: # si el usuario introduce un texto de búsqueda o añade un filtro a la consulta
            results = results.where(PostORM.title.ilike(f"%{query}%"))
        
        
        total = self.db.scalar(select(func.count()).select_from(results.subquery())) or 0
        if total == 0:
            return 0, []
        
        current_page = min(page, max(1,ceil(total/per_page)))
        
        order_col = PostORM.id if order_by == "id" else func.lower(
            PostORM.title)
        
        results = results.order_by(
            order_col.asc() if direction == "asc" else order_col.desc())
    
       
        start = (current_page - 1) * per_page
        items = self.db.execute(results.limit(per_page).offset(start)).scalars().all()
        # db.execute(...) -> ejecuta la consulta en la BD
        # limit(x) -> Como máximo dame x registros -> en SQL: LIMIT x
        # offset(start)-> nos saltamos los registros de las páginas anteiores
        # .scalars().all() -> extraemos los objetos del PostORM y no las filas completas
            # .scalars() -> SQLAlchemy devuelve inicialmente un objeto de resultados con filas de mi tabla (los PostORM)
            #   De cada fila del resultado, dame el objeto/primer elemento que he seleccionado
            #  .all() -> los reúne en una lista 
        return total, items   
    def by_tags(self, 
                tags : list[str],
                )->List[PostORM]:
        normalized_tag_names= [tag.strip().lower() for tag in tags if tag.strip()]
            
        if not normalized_tag_names:
            return[]
        
        # Si después de limpiar los tags no queda ninguno, 
        # no tiene sentido consultar la BD. Devuelve directamente una lista vacía.
        
        # Después construye la consulta
        post_list = (
            select(PostORM) # quiero seleccionar objetos PostORM
            .options( # Cómo quiero rcargar las relaciones de cada post
                selectinload(PostORM.tags), # consulata1: dame los post, consulta2: dame sus tags
                joinedload(PostORM.author), # carga author junto con el post mediante JOIN
            )
            .where(PostORM.tags.any(func.lower(TagORM.name).in_(normalized_tag_names)))
            #any -> Selecciona los posts que tengan al menos un tag cuyo nombre, 
            # en minúsculas, esté entre los tags solicitados.
            .order_by(PostORM.id.asc())
        )
        return self.db.execute(post_list).scalars().all()
        
    def ensure_author(self, name: str, email: str)-> AuthorORM:
        
        author_obj =self.db.execute(
            select(AuthorORM).where(AuthorORM.email == email)
        # Busca en la BD: ¿Ya existe un autor cuyo email sea el que acaba de llegar?
        ).scalar_one_or_none() # Da el AuthorORM o un None
        if author_obj: # si está el author_object
            return author_obj
        # si no está el autor de la búsqueda author_obj -> Lo creamos
        author_obj = AuthorORM(name=name, 
                                email=email)# la crea
        self.db.add(author_obj) # la añade en la BD
        self.db.flush() # Envía los cambios pendientes a la BD sin confirmar todavía la transacción. Falta el commit. Aseguramos el ID
    # cuando llega un nuevo post con un autor, comprobar si ese autor ya existe y, si no existe, crearlo.    
        return author_obj  
    def ensure_tag(self, name: str) -> TagORM:

        # con el objeto post de Postcreate creamos un objeto ORM
        tag_obj = self.db.execute(
            select(TagORM).where(TagORM.name.ilike(name))
        ).scalar_one_or_none()
        # Busca en tagORM un TagORM con el mismo nombre que name  y lo selecciona
        # trae algo o nada
        if tag_obj:
            return tag_obj
            
        tag_obj =TagORM(name=name) #lo crea con el nombre de tag
        self.db.add(tag_obj) # lo añade a la base de datos
        self.db.flush() # Envía los cambios pendientes a la BD sin confirmar todavía la transacción. 
        # Obtengo el tag_id pero todavía no hemos hecho commit()
        return tag_obj
        
        # Una vez creada la etiqueta hay que añadirla a la tabla intermedia:
        new_post.tags.append(tag_obj) 
        # Le dice a SQLAlchemy -> Este tag_obj pertenece a la colección .tags de 
        # este new_post
        # Recordar: Habíamos definido relationship entre tags y post_tags
        
    def create_post(self, title: str, content: str, author: Optional[dict], tags: List[dict]) ->PostORM :
        author_obj = None
        if author:
            author_obj = self.ensure_author(author['username'], author['email']) # username porque author viene de user que tiene username no name
        post = PostORM(title= title, content= content, author= author_obj)
        
        for tag in tags: # accedo a cada uno de los diccionarios
            tag_obj = self.ensure_tag(tag['name'])
            post.tags.append(tag_obj)
            # en PostORM (carpeta models) tags es uno de los atributos
            # añadimos tag_obj a esa lista (tagas estaba definido como lista - List(TargORM))
        self.db.add(post) # lo añadimos a la sesión
        self.db.flush() # aseguramos el id
        self.db.refresh(post) 
        # Vuelve a consultar en la base de datos esta fila y actualiza new_post con los valores q tiene allí
        # Trae tb los datos no introducidos por el cliente: el created_at -> deinidos en PostORM
        # No hacemos commit todavía
        return post
    def update_post(self, post: PostORM, updates: dict)-> PostORM: # hacerlo como lo hicimos antes
        
        
        for campo, valor in updates.items(): # saco el campo y valor de lo que me pedi el cliente
            setattr(post, campo, valor)
            #setattr() es una función normal de Python, no de SQLAlchemy.
            # Sirve para modificar un atributo de un objeto cuando el nombre del atributo lo tienes en una variable.
        # Si modifico post.title y post.content,  SQLAlchemy detecta que ese objeto ha cambiado. 
        # Al hacer después:
        
        
       
        return post
        # SQLAlchemy genera el UPDATE correspondiente.
    
        # raise HTTPException(status_code=404, detail="Post no encontrado")
        # Entonces para qué lo convierte Pydantic en PostUpdate si inmediatamente 
        # lo volvemos a convertir en diccionario?"
        # Porque entre medias ha hecho algo muy importante: validarlo.
    
    def delete_post(self, post:PostORM) -> None:
      
        self.db.delete(post)
        return # vacío porque el status es no content
    
            
        
        
