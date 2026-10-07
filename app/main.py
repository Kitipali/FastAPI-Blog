

import os
from fastapi import FastAPI
from app.core.db import Base, engine
from app.api.v1.posts.router import router as post_router 
# Porque en el futuro podemos tener routers para otras cosas que no sean posts
from app.api.v1.auth.router import router as auth_router
from app.api.v1.uploads.router import router as upload_router
from fastapi.staticfiles import StaticFiles # servimos los archivos estáticos
from dotenv import load_dotenv

load_dotenv()

MEDIA_DIR = "app/media"

# dev -> sólo para entorno de desarrollo. 



def create_app() -> FastAPI:
    app = FastAPI(title="Mini Blog") # crea la aplicación
    Base.metadata.create_all(bind=engine) # dev. crea las tablas que falten.
    # montamos los routers:
    app.include_router(auth_router, prefix="/api/v1")
    # Porque en security.py definimos -> oauth2_scheme = OAuth2PasswordBearer(tokenUrl= "/api/v1/auth/login")
    # y en router.py hacemos sólo prefix de /auth y de /login
    app.include_router(post_router) 
    # FastAPI, incorpora a mi aplicación todos los endpoints que están definidos 
    # en post_router
    app.include_router(upload_router)
    os.makedirs(MEDIA_DIR , exist_ok= True) # Creraá al carpeta app/media si no existe
    app.mount("/media", StaticFiles(directory= MEDIA_DIR), name="media")
    # Montamos la URL por la que mis archivos estáticos tendrán acceso
    
    
    return app

app = create_app()

    




    

