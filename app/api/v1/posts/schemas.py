# Aquí van 
    # todas las validaciones que hicimos con Pydantic
    # todas las clases que usamos como base para
        # PostCreate
        # PostUpdate
        # PostSummary...

from typing import Optional, List, Union, Literal, Annotated
from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict
from fastapi import Form

from app.api.v1.auth.schemas import UserPublic
from app.api.v1.categories.schemas import CategoryPublic


    
class Tag(BaseModel):
    name: str = Field(..., min_length=2, max_length=30, description= "Nombre de la etiqueta")
    # Cada etiquetas es un objeto con estructura:
    # {
    #   "name": "Python"
    # }
    # Además, Pydantic valida que name tenga entre 2 y 30 caracteres.

    model_config = ConfigDict(from_attributes=True) 
    # Esta validación va a aceptar ORM. Si no lo ponemos, únicamente va a aceptar diccionarios

class Author(BaseModel):
    name: str 
    email: EmailStr
    
    model_config = ConfigDict(from_attributes=True) 
        # Esta validación va a aceptar ORM. Si no lo ponemos, únicamente va a aceptar diccionarios
    
class PostBase(BaseModel):
    title:str
    content: str
    tags: Optional[List[Tag]] = Field(default_factory=list)
    # crea una lista vacía por cada objeto que se cree
    # crea listas de forma independiente para no tener problemas en un futuro
        # post1 -> lista A
        # post2 -> lista B...
    # Porque una lista es mutable: puedes modificarla después de crearla. Y 
    # si varios objetos compartieran accidentalmente la misma lista, 
    # modificar la lista de uno modificaría también la del otro.
    user:Optional[UserPublic] = None
    image_url: Optional[str] = None
    category: Optional[CategoryPublic] = None
    
    model_config = ConfigDict(from_attributes=True) 
        # Esta validación va a aceptar ORM. Si no lo ponemos, únicamente va a aceptar diccionarios
    
class PostCreate(BaseModel): # validará las creaciones de posts y hereda de BaseModel
    title: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Título del post (mínimo 3 caracteres, máximo 100)",
        examples= ["Mi primer post con FastAPI"]
    )
    content: Optional[str] = Field(
        default="Contenido no disponible",
        min_length=10,
        description="Contenido del post (mínimo 10 caracteres)",
        examples=["Este es un contenido válido porque tiene 10 caracteres o más"]
    )
    category_id: Optional[int]
    tags: List[Tag]= Field(default_factory=list)#[]
    # tags debe ser una lista de objetos Tag y, 
    # si el usuario no proporciona tags, Pydantic crea una lista vacía nueva [].
    # author:Optional[Author] = None
    # IMPORTANTE:
        # content -> tipo básico de Python -> str
        # tags-> lista de objetos Tag (Pydantic)
        # Author -> Objeto Author (Pydantic) 
    
    @field_validator("title") 
    # decorador field_validator de Pydantic para el campo "title"
    # Dice Cuando vayas a validar el campo title, ejecuta también esta función
    @classmethod 
    # decorador classmethod -> # La función recibe la clase (cls) en lugar de una instancia (self)
    # Decorador incorporado en Python
    # Hace que el primer argumento de la función sea la clase (cls), 
    # en lugar de una instancia (self)-> Un objeto concreto
    def not_allowed_title(cls, value:str) -> str:
        # cls -> La clase -> Post
        # value -> El valor concreto de Title que Pydantic está validando
        # -> str: Si la validación sale bien, devuelve un str
        if "spam" in value.lower():
            raise ValueError("El título no puede contener la palabra: 'spam'")
        return value
    @classmethod
    def as_form(
        cls,
        title: Annotated[str, Form(min_length=3)], 
        # str recibido como campo de formulario; mínimo 3 caracteres
        content: Annotated[str, Form(min_length=10)],
        category_id: Annotated[int, Form(ge=1)],
        tags: Annotated[Optional[List[str]], Form()] = None, 
        
    ):
        tag_objs = [Tag(name=t) for t in (tags or [])]
        return cls(title=title, content= content, category_id= category_id,tags=tag_objs)
        # Con los valores recibidos construye el postcreate`
        
    
class PostUpdate(BaseModel):# validará las actualizaciones de posts y hereda de BaseModel
    title: Optional[str] = Field(None, min_length=3, max_length=100)
    content: Optional[str] = None 
    # hacemos este campo opcional
    # = None -> No queremos un valor por defecto -> Se conserva lo que ya tenía

class PostPublic(PostBase): 
    # Clase que hereda de PostBase donde hay title y content es opcional y predefinido
    # Por lo tanto no es necesario definir title y content
    id: int
    slug: str
    model_config= ConfigDict(from_attributes=True)
    # Config_Dict viene de Pydantic
    # Permite a Pydantic construir PostPublic leyendo atributos
    # de un objeto (por ejemplo, un PostORM de SQLAlchemy).
    # Sirve para que Pydantic entienda que está recibiendo un objeto de SQLAlchemy -> del PostORM
    # Significa: Puedes construir este modelo leyendo los datos desde los atributos de un objeto, 
    # no solamente desde un diccionario.
    # 
    # Sabrá por ejemplo que 
    #   ya no tengo necesariamente un post["title]" sino un post.title
    # En teoría, no sería necesario poner luego from_attribute=True
    
    

class PostSummary(BaseModel):
    id: int
    title: str
    model_config = ConfigDict(from_attributes=True) 
    # queremos aceptar objetos, no sólo diccionarios

class PaginatedPost(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int
    has_prev: bool
    has_next: bool
    order_by: Literal["id", "title"]
    direction: Literal["asc","desc"]
    search: Optional[str]=None
    # limit: int
    # offset: int
    items: List[PostPublic] # lista de items de PostPublic
    



