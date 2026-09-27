
import os # # Para acceder, entre otras cosas, a las variables de entorno
from datetime import datetime
from fastapi import FastAPI, Query, Body, HTTPException, Path, status, Depends
from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict
from typing import Optional, List, Union, Literal
from math import ceil
from sqlalchemy import create_engine, Integer, String, Text, DateTime, select, func, UniqueConstraint, ForeignKey, Table, Column
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase, Mapped, mapped_column, relationship, selectinload, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./blog.db")
# print("Conectado a: ", DATABASE_URL)
# borramos esto porque es innecesario y peligroso
# Reconocemos un archivo .env
# si no hay variable de entono toma el valor por defecto en sqlite:///./blog.db
# sqlite:///(protocolo)   +  ./blog.db (ruta del archivo) donde . es directorio actual


engine_kwargs = {} # sólo en sqlight
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"]={"check_same_thread": False} # configuración específica  de sql lite
#Comprueba si la base de datos es SQLite

engine = create_engine(DATABASE_URL, echo=True, future=True, **engine_kwargs)
# Creamos una conexión
# el motor de SQLAlchemy: el objeto que sabe dónde está mi base de datos y cómo debo comunicarme con ella
# echo=True -> para ver en terminal qué comandos sql se están ejecutando
# future=True -> queremos ocupar la sintaxis moderna de sql alchemy 2
# **engine_kwargs sólo par sqlite con postegresql no
# autocommit=False -> Tenemos un control explícito en el commit


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
# Creamos una "fábrica se sesiones", no una sesión
# class_=Session -> le dice a sessionmaker qué clase debe utilizar para fabricar las sesiones.
# después haremos:
    # db = Sessionlocal() ->se crea una sesión y la pregunta será: de que clase es db? -> class_=Session
# autoflush=False -> No envía cambios hasta hacer el commit


# DeclarativeBase -> Hace que SQLAlchemy pueda reconocer las clases que heredan de Base como 
# modelos ORM y recopilar información sobre las tablas que representan.

class Base(DeclarativeBase):
    pass


# Necesitamos ahora clases para representar los modelos en la Base de Datos
# Son distintas a las clases que usamos para validar (pydantic)
# Pueden trabajar conjuntamente

### Clases para representar modelos ORM de SQLAlchemy
# Son clases Python que representan las tablas de la base de datos y 
# permiten trabajar con sus filas como objetos Python


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

class AuthorORM(Base):
    __tablename__= "authors"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique= True)
    # tenemos que enlazar esta tabla con la tabla "posts"                                   
    posts: Mapped[List["PostORM"]] = relationship(back_populates="author")
    # posts va a ser una lista de objetos de tipo ORM -> Un autor puede tener muchos posts
    # Relación de 1 a muchos (N PostORM)
    # relationship(...)-> de SQLAlchemy -> Crea relación entre objetos Python
    # back_populates="author" -> Esta relación tiene su pareja en el atributo author de PostORM


class TagORM(Base):
    __tablename__= "tags"
    id: Mapped[int]=mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str]= mapped_column(String(30), unique=True, index=True)
    
    # Como un post puede tener varias tags y cada tag puede estar en varios posts 
    # no podemos añadir un post_id en tags ni un tag_id en posts -> Relación de Muchos a Muchos
    # Necesitamos una tabla intermedoa
    posts: Mapped[List["PostORM"]] = relationship(
        secondary= post_tags,
        back_populates= "tags", # posts.tags
        lazy="selectin"
        
    )
    


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
def get_db():
# función para crear la sesión cada vez que entre en cada uno de los endpoints y 
# que la cirre al salir cuando no la ocupe
    db = SessionLocal() # inicializamos una sesión
    try:
        yield db 
        # fastapi espera una dependencia generadora. Es como una "pausa"
        #yield db entrega db al endpoint ->get_db se queda "pausada"
        # si fuera return -> finalizaría la función
        # cuando el endpoint utiliza db -> termina el endpoint -> gt_db continúa después del yield
    finally:
        db.close() # se cierra la sesión

# Necesitamos ahora clases para representar los modelos en la Base de Datos
# Son distintas a las clases que usamos para validar (pydantic)
# Pueden trabajar conjuntamente

Base.metadata.create_all(bind=engine) # dev -> sólo para entorno de desarrollo. 
# Va a crear las tablas en caso de que no existan, en producción haríamos migraciones
# Como PostORM hereda de Base -> SQLAlchemy registra la estructura de PostORM en Base.metadata
# metadata -> catálogo de las tablas qye SQLAlchemy conoce
# .create_all() -> Crea en la base de datos todas las tablas registradas en Base.metadata que todavía no existan.
# bind=engine Hazlo utilizando este engine, es decir, sobre la base de datos a la que este engine está conectado.



# Lo inicializamos
# Creamos un objeto de la clase FastAPI
app = FastAPI(title="Mini Blog")

# Le pasamos el método get y qué ruta va a tener este método
# "/" -> Ruta raíz de la aplicación
# GET -> Cuando alguien haga una petición HTTP GET...


### Clases para validar datos -> Pydantic

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
    author:Optional[Author] = None
    
    model_config = ConfigDict(from_attributes=True) 
        # Esta validación va a aceptar ORM. Si no lo ponemos, únicamente va a aceptar diccionarios
    
class PostCreate(PostBase): # validará las creaciones de posts y hereda de BaseModel
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
    tags: List[Tag]= Field(default_factory=list)#[]
    # tags debe ser una lista de objetos Tag y, 
    # si el usuario no proporciona tags, Pydantic crea una lista vacía nueva [].
    author:Optional[Author] = None
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
    
class PostUpdate(BaseModel):# validará las actualizaciones de posts y hereda de BaseModel
    title: Optional[str] = Field(None, min_length=3, max_length=100)
    content: Optional[str] = None 
    # hacemos este campo opcional
    # = None -> No queremos un valor por defecto -> Se conserva lo que ya tenía

class PostPublic(PostBase): 
    # Clase que hereda de PostBase donde hay title y content es opcional y predefinido
    # Por lo tanto no es necesario definir title y content
    id: int
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

@app.get("/") #...a la ruta raíz de mi aplicación, ejecuta la función de abajo
def home():
    return {"message": "Bienvenido a Mini Blog por Juanfran Barragán!"}
    # ¿Qué significa GET?

    # GET es uno de los métodos de HTTP. Normalmente significa "quiero obtener informa
    # ción".
    # Hemos creado un endpoint-> Cuando accedemos con el navegador a la ruta,
    # el navegador hace una petición   HTTP GET a esa ruta. El servidor recibe la petición
    # y ejecuta la función home() que devuelve un diccionario. FastAPI convierte ese diccionario
    # en un JSON y lo devuelve al navegador. El navegador recibe el JSON y lo muestra en pantalla.

    # Creamos un endpoint nuevo al que daremos de nombre "post"
    # GET / ya está definido para home(), por eso creamos otro endpoint: GET /posts

@app.get("/posts", response_model=PaginatedPost)
    # la ruta es /posts y el modelo de respuesta (mi molde) va a ser una lista de PostPublic
    # Nos va a devolver una lista de muchos PostPublic
    # «FastAPI, yo te voy a devolver una lista (en el return) y quiero que trates 
    # cada elemento de esa lista como un PostPublic.»
def list_posts(
    text: Optional[str] = Query(default=None),
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
    results = select(PostORM)
    # Construye una consulta SQLAlchemy como -> SELECT * FROM posts
    query = query or text
    
    # de momento, mis resultados son todos mis posts
    
    if query: # si el usuario introduce un texto de búsqueda o añade un filtro a la consulta
        results = results.where(PostORM.title.ilike(f"%{query}%"))
        # como SELECT * FROM posts WHERE
        # PostORM.title.ilike(...) -> Busca títulos que coincidan con este patrón 
        # ignorando mayúsculas/minúsculas.
        # f"" -> genera un fstring
        # % comodín de SQL
            #fastapi%     → empieza por "fastapi"
            #%fastapi     → termina en "fastapi"
            #%fastapi%    → contiene "fastapi" en cualquier posición
    
    total = db.scalar(select(func.count()).select_from(results.subquery())) or 0
    # results.subquery() -> Convierte la consulta anterior en una subconsulta.
    # «Coge la consulta que ya he preparado y trátala como si fuese una tabla temporal
    # sobre la que puedo hacer otra consulta».
    # func.count = COUNT() en SQL
    # select(func.count() -> Quiero contar filas
    # scalar() -> esperamos un único valor
    total_pages= ceil(total/per_page) if total > 0 else 0
    
    current_page = 1 if total_pages == 0 else min(page, total_pages)
    
    # elegimos la columa por la que ordenar:
    if order_by == "id":
        order_col = PostORM.id
    else:
        order_col = func.lower(PostORM.title)
    results = results.order_by(order_col.asc() if direction == "asc" else order_col.desc())
    
    # results = sorted(
    #     results, key=lambda post: post[order_by], reverse=(direction == "desc"))
    
    if total_pages == 0:
        items = List[PostORM] = []
    else:    
        start = (current_page - 1) * per_page
        items = db.execute(results.limit(per_page).offset(start)).scalars().all()
        # db.execute(...) -> ejecuta la consulta en la BD
        # limit(x) -> Como máximo dame x registros -> en SQL: LIMIT x
        # offset(start)-> nos saltamos los registros de las páginas anteiores
        # .scalars().all() -> extraemos los objetos del PostORM y no las filas completas
            # .scalars() -> SQLAlchemy devuelve inicialmente un objeto de resultados con filas de mi tabla (los PostORM)
            #   De cada fila del resultado, dame el objeto/primer elemento que he seleccionado
            #  .all() -> los reúne en una lista       
        
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
    # Cuando alguien haga una petición GET a /posts, ejecuta list_posts().
    # query: str | None ->El parámetro query puede ser un texto o Ninguno.
    # Query(default=None,...) -> le dice a FastAPI que se trata de un parámetro de 
    # consulta y que es opcional porque su valor por defecto es None
    # description -> solo descripcion del signifivado del parámetro se puede ver en
    # http://127.0.0.1:8000/docs
    # Podemos hacer 
    #   GET /posts o
    #   GET /posts?query=FastAPI

    # Combinamos path parameter con query parameter
    # include_content dice en este caso, que si es True muestre el valor de la clave content
    # y si no sólo el valor de id y title
    # Por defecto está True y  el navegador lo cambiamos a False -> http://127.0.0.1:8000/posts/3?include_content=False


@app.get("/posts/by-tags", response_model=List[PostPublic])
def filter_by_tags( 
    # Crea esta función para que el decorador no se pegue al de abajo
    # Un decorador @app.get(...) debe ir asociado a una función. 
    # Si escribes varios decoradores consecutivos antes de una función, 
    # Python entiende que todos decoran esa misma función.
    tags: List[str] = Query(
        ...,
        min_length=1, # cada string de la lista tiene q tener al menos 2 caracteres
        description= "Una etiqueta. Ejemplo: ?tags=python&tags=fastapi"
    ),
    db: Session = Depends(get_db)
    
):  
    normalized_tag_names= [tag.strip().lower() for tag in tags if tag.strip()]
    
    if not normalized_tag_names:
        return[]
    
    # Si después de limpiar los tags no queda ninguno, 
    # no tiene sentido consultar la BD. Devuelve directamente una lista vacía.
    
    # Después construye la consulta
    post_list = (
        select(PostORM) # quiero seleccionar objetos PostORM
        .options(
            selectinload(PostORM.tags),
            joinedload(PostORM.author),
        )
        .where(PostORM.tags.any(func.lower(TagORM.name).in_(normalized_tag_names)))
        .order_by(PostORM.id.asc())
    )
    # .options(...) -> Instrucciones para SQLAlchemy de como cargar las relaciones
        # selectinload(PostORM.tags) -> carga los tags relacionados con los posts 
            # mediante la estrategia selectin.
        # joinedload(PostORM.author) ->carga también el AuthorORM relacionado con 
            # cada post, utilizando un JOIN
    
    # .where(PostORM.tags.any() -> Selecciona el PostORM si alguno de sus tags 
    # cumple esta condición
    # «Posts en los que alguno de sus tags tenga un nombre incluido en 
    # normalized_tag_names».  
    # .in_() -> método de SQLAlchemy que construye el IN de SQL 
    
      
        
    
    posts = db.execute(post_list).scalars().all()
    
    return posts




@app.get("/posts/{post_id}",response_model=Union[PostPublic, PostSummary], response_description="Post encontrado")
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
    
    post_find= select(PostORM).where(PostORM.id == post_id)
    # FORMA GENERAl-> Construimos explícitamente una consulta -> Buscar por cualquier columna
    post = db.execute(post_find).scalar_one_or_none() # búsqueda más flexible -> más control 
    #Ejecutamos la consulta.
    # scalar_one_or_none() -> devuelve un PostORM si encuentra uno
    # o None si no encuentra ninguno.
    
    # post = db.get(PostORM, post_id) # -> Para buscar por clave primaria
    # FORMA ESPECÍFICA PARA PRIMARY KEY:
    # SQLAlchemy sabe que la primary key de PostORM es id, porque la declaré
    # equivalente en SQL -> SELECT * FROM posts WHERE id=5 (si pidiésemos el id=5);
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
        
    
    # for post in BLOG_POST:
    #     if post["id"] == post_id:
    #        if not include_content:
    #            return {"id": post["id"], "title": post["title"]}
    #        return post
               
    return post
    # si no incluye content el return sólo puede puede ajustarse s PostSummary
    # si lo incluye, el return tiene q tener el formato de PostPublic
    # FastAPI/Pydantic recibe lo que tú has hecho en el return 
    # y determina con qué alternativa del Union encaja


    

# Método Post

@app.post("/posts", response_model=PostPublic, response_description= "Post creado (OK)", status_code= status.HTTP_201_CREATED)
# Porque PostPublic es el que tiene id + title + content
def create_posts(post: PostCreate, db: Session = Depends(get_db)): # PostCreate es la clase de Pydantic    
    # Para ejecutar create_post, necesito una sesión de base de datos. FastAPI, consíguemela utilizando get_db()
    # db -> nombre de la variable que vas a utilizar dentro del endpoint
    # Session -> el tipo de variable -> Objeto Session de SQLAlchemy
    # Depends(gt_db) -> El valor de db depende de lo que proporcione get_db()
    # post → viene DE FUERA, del cliente
    # db   → viene DE DENTRO, FastAPI lo obtiene con Depends()
    
    author_obj= None # de momento no tenemos ningún author_obj
    if post.author: # post -> PostCreate de Pydantic q ha llegado a la API. Comprueba si usuario ha enviado autor
        author_obj = db.execute(
            select(AuthorORM).where(AuthorORM.email == post.author.email)
            # Busca en la BD: ¿Ya existe un autor cuyo email sea el que acaba de llegar?
        ).scalar_one_or_none() # Da el AuthorORM o un None
        if not author_obj: # si no está el autor de la búsqueda author_obj
            author_obj = AuthorORM(name=post.author.name, 
                                   email=post.author.email)# la crea
            db.add(author_obj) # la añade en la BD
            db.flush() # Envía los cambios pendientes a la BD sin confirmar todavía la transacción. Falta el commit
    # cuando llega un nuevo post con un autor, comprobar si ese autor ya existe y, si no existe, crearlo.        
        
    new_post= PostORM(title=post.title, content=post.content, author= author_obj)
    # con el objeto post de Postcreate creamos un objeto ORM
    
    for tag in post.tags: # si existe tag en el post
        tag_obj = db.execute(
            select(TagORM).where(TagORM.name.ilike(tag.name))
        ).scalar_one_or_none()
        # Busca en tagORM un TagORM con el mismo nombre que tag.name y lo selecciona
        # trae algo o nada
        if not tag_obj: # Si nom existe tag_obj
            tag_obj =TagORM(name=tag.name) #lo crea con el nombre de tag
            db.add(tag_obj) # lo añade a la base de datos
            db.flush() # Envía los cambios pendientes a la BD sin confirmar todavía la transacción. 
            # Obtengo el tag_id pero todavía no hemos hecho commit()
        # Una vez creada la etiqueta hay que añadirla a la tabla intermedia:
        new_post.tags.append(tag_obj) 
        # Le dice a SQLAlchemy -> Este tag_obj pertenece a la colección .tags de 
        # este new_post
        # Recordar: Habíamos definido relationship entre tags y post_tags
    try:
        db.add(new_post) # lo añadimos a la sesión
        db.commit() # guardamos el cambio en la BD -> Se guardan todos los valores a los que le hicimos flush()
        db.refresh(new_post) 
        # Vuelve a consultar en la base de datos esta fila y actualiza new_post con los valores q tiene allí
        # Trae tb los datos no introducidos por el cliente: el id y el created_at -> deinidos en PostORM
        return new_post
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail= "El título ya existe, prueba con otro")
    except SQLAlchemyError: # si hay un error de SQLAlchemy
        db.rollback() # deshaz toda la operación
        raise HTTPException(status_code=500, detail="Error al crear el post") # notificamos el error
   
        
# Ahora queremos actualizar un post existente con PUT
    
@app.put("/posts/{post_id}", response_model=PostPublic, response_description= "Post actualizado", response_model_exclude_none=True, )
# response_model_exclude_none=True -> excluye los valores que sean None
def update_post(post_id: int, data: PostUpdate, db: Session = Depends(get_db)):

    post = db.get(PostORM, post_id) # -> Para buscar por clave primaria
    
   
    if not post:
        raise HTTPException(status_code=404, detail= "Post no encontrado")
    
    updates = data.model_dump(exclude_unset=True)  
    # Porque data es un objeto PostUpdate (pydantic) que no está en diccionario -> se pasa a diccionario 
   
    for campo, valor in updates.items():
        setattr(post, campo, valor)
        #setattr() es una función normal de Python, no de SQLAlchemy.
        # Sirve para modificar un atributo de un objeto cuando el nombre del atributo lo tienes en una variable.
    # Si modifico post.title y post.content,  SQLAlchemy detecta que ese objeto ha cambiado. 
    # Al hacer después:
    db.add(post)
    db.commit()
    db.refresh(post) 
    # Vuelve a leer el registro de la BD y sincroniza `post`
    # con los valores finalmente almacenados.
    
    return post
    # SQLAlchemy genera el UPDATE correspondiente.

    # raise HTTPException(status_code=404, detail="Post no encontrado")
    # Entonces para qué lo convierte Pydantic en PostUpdate si inmediatamente 
    # lo volvemos a convertir en diccionario?"
    # Porque entre medias ha hecho algo muy importante: validarlo.


# Ahora creamos un endpoint de delete
@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id:int, db: Session = Depends(get_db)):
     post = db.get(PostORM, post_id) # -> Para buscar por clave primaria
     if not post:
         raise HTTPException(status_code=404, detail= "Post no encontrado")
     db.delete(post)
     db.commit()
     return # vacío porque el status es no content
    
    
    
    