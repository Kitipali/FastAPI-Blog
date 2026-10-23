

from contextlib import contextmanager
from typing import Optional
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.category import CategoryORM
from app.models.tag import TagORM
from app.models.user import User
from app.seeds.data.categories import CATEGORIES
from app.seeds.data.tags import TAGS
from app.seeds.data.users import USERS

# Este service.py empieza a definir la lógica necesaria para cargar los seeds en la base de datos.

def hash_password(plain: str) -> str:
    return PasswordHash.recommended().hash(plain)
# Para cifrar contraseñas mediante hashing


@contextmanager
def atomic(db: Session):
    try:
        yield
        db.commit()
    except Exception:
        db.rollback()
        raise
# @ contextmanager -> decorador de Python que permite contruir un gestor de contexto
# Los gestores de contexto sob los que se utilizan con with -> ejemplo:
    # with open("datos.txt") as archivo:
    # contenido = archivo.read()   
# Python abre el archivo, ejecuta el bloque y después lo cierra automáticamente.
# Con @contextmanager, puedes crear un comportamiento parecido, pero para 
# las transacciones SQLAlchemy.
# yield significa => «Detén temporalmente esta función y ejecuta el código que hay dentro del bloque with».
# Ejemplo:
    # with atomic(db):
        # db.add(usuario)
        # db.add(categoria)
        # db.add(etiqueta)
# atomic -> Porque pretende que varias operaciones se comporten como una única unidad de trabajo: 
    # o se confirman todas, o se revierten todas.

def _user_by_email(db: Session, email: str) -> Optional[User]:
    return db.execute(select(User).where(User.email == email)).scalars().first()

def _category_by_slug(db: Session, slug:str)-> Optional[CategoryORM]:
    return db.execute(select(CategoryORM).where(CategoryORM.slug == slug)).scalars().first()
 
def _tag_by_name(db: Session, name:str)-> Optional[TagORM]:
    return db.execute(select(TagORM).where(TagORM.name == name)).scalars().first()

def seed_users(db: Session) -> None:
    with atomic(db):
        for data in USERS:
            obj = _user_by_email(db, data["email"])
            # busca el usuario en la BD
            # si existe -> Lo actualiza
            if obj:
                changed=False
                if obj.full_name != data.get("full_name"):
                    obj.full_name = data.get("full_name")
                    changed=True
                if data.get("password"):
                    obj.hashed_password = hash_password(data["password"])
                    changed=True
                if data.get("role"):
                    obj.role = data.get("role")
                    changed=True
                if changed:
                    db.add(obj)
            else:
                db.add(User(
                    email = data["email"],
                    full_name= data.get("full_name"),
                    role=data.get("role"),
                    hashed_password= hash_password(data["password"])
                ))
                
def seed_categories(db: Session)-> None:
    with atomic(db):
        for data in CATEGORIES:
                obj = _category_by_slug(db, data["slug"])
                if obj:
                    if obj.name != data["name"]:
                        obj.name= data["name"]
                        db.add(obj)
                else:
                    db.add(CategoryORM(name=data["name"], slug=data["slug"]))
                    
def seed_tags(db: Session) -> None:
    with atomic(db):
        for data in TAGS:
            obj = _tag_by_name(db, data["name"])
            if obj:
                if obj.name != data["name"]:
                    obj.name = data["name"]
                    db.add(obj)
            else:
                db.add(TagORM(name= data["name"]))
                           
def run_all() -> None:
    print("Entrando en run_all")
    with SessionLocal() as db:
        print("Ejecutando usuarios")
        seed_users(db)
        print("Ejecutando categorías")
        seed_categories(db)
        print("Ejecutando etiquetas")
        seed_tags(db)
                        

def run_users() -> None:
    with SessionLocal() as db:
        seed_users(db)
        
def run_categories() -> None:
    with SessionLocal() as db:
        seed_categories(db)
                
    
def run_tags() -> None:
    with SessionLocal() as db:
        seed_tags(db)
    
        

