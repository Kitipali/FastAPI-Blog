from math import ceil
from fastapi import APIRouter, Query, Depends, Path, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session 
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import List, Optional, Literal, Union, Annotated
from app.core.db import get_db
from .schemas import (PostPublic, PaginatedPost, PostCreate, PostUpdate, PostSummary)
from .repository import PostRepository
from app.core.security import oauth2_scheme, get_current_user
from app.services.file_storage import save_uploaded_image
import time
import asyncio
import threading

router = APIRouter(prefix="/posts", tags=["posts"])


# @router.get("/sync")
# def sync_endpoint():
#     print("SYNC thread: ", threading.current_thread().name)
#     time.sleep(8)
#     return{"message": "Función síncrona terminó"}
    
# @router.get("/async") 
# async def async_endpoint():
#     print("ASYNC thread: ", threading.current_thread().name)
#     await asyncio.sleep(8)
#     return{"message": "Función asíncrona terminó"}
     
# # tags-> para la documentación para que lo englobe todo en un mismo bloque
@router.get("", response_model=PaginatedPost)
# "" -> vacío porque aquí va el prefix

def list_posts(
    text: Optional[str] = Query(
        default=None,
        deprecated=True,
        description="Parámetro obsoleto, usa query o search en su lugar."),
    query: Optional[str] = Query(
        default=None,
        description= "Texto para buscar por título",
        alias="search", # para darle un nombre distinto a "query" en la url sin cambiar todo el código
        min_length = 3,
        max_length = 50,
        pattern = r"^[\w\sáéíóúÁÉÍÓÚüÜ-]+$" # > expresión regular q limita q caracteres puede contener el parámetro de búsqueda.
),
    per_page: int = Query(
        10, ge=1, le=50,
        description="Número de resultados (1-50)"
), # con esto limitamos la cantidad de respuestas que vamos a tener
    page: int = Query(
        1, ge=1,
        description="Número de página (>=1)"
), # decimos desde qué número vamos a empezar
    order_by: Literal["id","title"] = Query(
        "id", description="Campo de orden"
        # Literal -> Solo acepto exactamente uno de estos valores
        # y el valor por defecto es "id"
),
    direction: Literal["asc", "desc"]=Query(
        "asc", description="Dirección de orden" # valor por defecto es "asc" 
),
    db: Session = Depends(get_db)
):
    repository = PostRepository(db) 
    # accedemos a PostRepository conectando con la sesión
    
    query = query or text
    
    total, items = repository.search(query, order_by, direction, page, per_page)
    # el resultado es una tupla (total, ítems)
    # Los items son los posts concretos que corresponden a la página solicitada
    
    total_pages= ceil(total/per_page) if total > 0 else 0
    
    current_page = 1 if total_pages == 0 else min(page, total_pages)       
        
    has_prev = current_page >1
    has_next = current_page <total_pages if total_pages > 0 else False
    return PaginatedPost(
        page= current_page, 
        per_page= per_page,
        total= total, 
        total_pages=total_pages,
        has_prev= has_prev,
        has_next= has_next,
        order_by= order_by, 
        direction= direction,
        search= query, 
        items=items
    )

@router.get("/by-tags", response_model=List[PostPublic])   
def filter_by_tags( 
                   
    tags: List[str] = Query(
        ...,
        min_length=1, # cada string de la lista tiene q tener al menos 1 caracter
        description= "Una o más etiquetas. Ejemplo: ?tags=python&tags=fastapi"
    ),
    db: Session = Depends(get_db)
    
):  
    repository = PostRepository(db)
  
    return repository.by_tags(tags)

@router.get("/{post_id}", response_model=Union[PostPublic, PostSummary])

# aquí hay que evaluar si la respuesta es PostPublic o PostSummary
# Es como un switch para que FastAPI decida el tipo de respuesta


def get_post(post_id: int = Path(
        ...,
        ge=1, #greater or equal -> Mayor o igual que
        title = "ID del post",
        description= "Identificador entero del post. Debe ser mayor a 1",
        example = 1), 
    include_content: bool = Query(default =True, description = "Incluir o no el contenido?"), 
    db: Session = Depends(get_db)):
    
    repository = PostRepository(db)
    post = repository.get(post_id)
    
    if not post:
        raise HTTPException(status_code=404, detail= "Post no encontrado")
    if include_content:
        return PostPublic.model_validate(post, from_attributes= True)
        # model_validate(...) es de Pydantic
            # PostPublic.model_validate -> Pydnatic, coge este objeto, conviértelo/valídalo según este modelo (PostPublic)
            # Crea un objeto PostPublic usando los datos de PostORM y valida esos datos s/ reglas de PostPublic:
                # PostPublic(
                #         id=post.id,
                #         title=post.title,
                #         content=post.content
                # )
        # from_attributes=True -> Pydantic trabaja cómodo con diccionario pero post es un objeto PostORM
        #  esto le dice a Pydantic los datos que estoy pasando están en los atributos del objeto. Léelos ahí

    return PostSummary.model_validate(post, from_attributes=True)
        

# Método Post
@router.post("", response_model=PostPublic, response_description= "Post creado (OK)", status_code= status.HTTP_201_CREATED)
# Porque PostPublic es el que tiene id + title + content
def create_posts(post: Annotated[PostCreate, Depends(PostCreate.as_form)], image: Optional[UploadFile]=File(None), db: Session = Depends(get_db), user=Depends(get_current_user)): # PostCreate es la clase de Pydantic    
    # Para ejecutar create_post, necesito una sesión de base de datos. FastAPI, consíguemela utilizando get_db()
    # db -> nombre de la variable que vas a utilizar dentro del endpoint
    # Session -> el tipo de variable -> Objeto Session de SQLAlchemy
    # Depends(gt_db) -> El valor de db depende de lo que proporcione get_db()
    # post → viene DE FUERA, del cliente
    # db   → viene DE DENTRO, FastAPI lo obtiene con Depends()
    # user=Depends(get_current_user) -> le decimos al endpoint que tb debe resolver el get_current_user
    # es decir el usuario tiene que estar logueado -> Hemos protegido el endpoint
    # FastAPI ejecuta PostCreate.as_form como dependencia.
    # Obtiene title, content y tags del formulario HTTP,
    # construye un objeto PostCreate y lo asigna a post.
    # Swagger muestra los campos gracias a Form().
        #Annotated[
        #PostCreate,                  ← tipo de dato que recibirá post
        #Depends(PostCreate.as_form)]  ← cómo obtiene FastAPI ese dato
    repository = PostRepository(db)
    saved = None
          
   
    try:
        if image is not None:
            saved = save_uploaded_image(image)
        image_url = saved["url"] if saved else None
        post= repository.create_post( # Ahora post es un objeto PostORM, no un objeto Pydantic. Reutilizamos la variable
            title=post.title,
            content=post.content,
            author= user, # recordar que user = FAKE_USERS.get(form_data.username)
            category_id=post.category_id,
            tags= [tag.model_dump() for tag in post.tags], # convierto en diccionario cada uno de los tags y guardo en lista      
            image_url=image_url
        )
        db.commit() # guardamos el cambio en la BD -> Se guardan todos los valores a los que le hicimos flush()
        db.refresh(post) 
        # Vuelve a consultar en la base de datos esta fila y actualiza post con los valores q tiene allí
        # Trae tb los datos no introducidos por el cliente: el id y el created_at -> deinidos en PostORM
        return post
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail= "El título ya existe, prueba con otro")
    except SQLAlchemyError: # si hay un error de SQLAlchemy
        db.rollback() # deshaz toda la operación
        raise HTTPException(status_code=500, detail="Error al crear el post") # notificamos el error
   
  

# Ahora queremos actualizar un post existente con PUT
@router.put("/{post_id}",response_model=PostPublic, response_description= "Post actualizado", response_model_exclude_none=True)    
# response_model_exclude_none=True -> excluye los valores que sean None
def update_post(post_id: int, data: PostUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    
    repository = PostRepository(db)
    post = repository.get(post_id)
    if not post:
        raise HTTPException(status_code=404, detail= "Post no encontrado")
    try:
        updates = data.model_dump(exclude_unset= True) # convierte el PostUpdate de Pydantic en un diccionario.
        # Convierte PostUpdate en un diccionario.
        # exclude_unset=True -> excluye los campos que el cliente NO ha enviado.
        post = repository.update_post(post, updates) # llamamos al método q hace la actualizacón en el repository
        db.commit() 
        # Confirma en la BD todos los cambios pendientes de la sesión
        db.refresh(post) 
        return post
    except SQLAlchemyError: # si hay un error de SQLAlchemy
        db.rollback() # deshaz toda la operación
        raise HTTPException(status_code=500, detail="Error al modificar el post") # notificamos el error
        
 
    

    # SQLAlchemy genera el UPDATE correspondiente.

    # raise HTTPException(status_code=404, detail="Post no encontrado")
    # Entonces para qué lo convierte Pydantic en PostUpdate si inmediatamente 
    # lo volvemos a convertir en diccionario?"
    # Porque entre medias ha hecho algo muy importante: validarlo.


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
# Como decimos que nos devuelva un 204 - Sin contenido -> No necesitamos un return
def delete_post(post_id:int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    repository = PostRepository(db)
    post = repository.get(post_id)
    if not post:
        raise HTTPException(status_code=404, detail= "Post no encontrado")
    
    try:
        repository.delete_post(post)
        db.commit() # confirmamos la transacción
    except SQLAlchemyError: # si hay un error de SQLAlchemy
        db.rollback() # deshaz toda la operación
        raise HTTPException(status_code=500, detail="Error al eliminar el post") # notificamos el error
 
 
        
 
@router.get("/secure")                   
def secure_endpoint(token: str = Depends(oauth2_scheme)): 
    # añadimos la dependencia 
    # Antes de ejecutar secure_endpoint, ejecuta la dependencia oauth2_scheme y 
    # mete el resultado en la variable token
    return {"message":"Acceso con token", "token_recibido": token}
    
@router.get("/post/{slug}", response_model=Union[PostPublic, PostSummary])  
def get_post_by_slug(slug: str, include_content: bool = Query(default =True, description = "Incluir o no el contenido?"), db: Session = Depends(get_db)):
    repository = PostRepository(db)
    post = repository.get_by_slug(slug)
    if not post:
        raise HTTPException(404, "Post no encontrado")
    if include_content:
        return PostPublic. model_validate(post, from_attributes=True)
    return PostSummary.model_validate(post, from_attributes=True)
        
    
    
    
    