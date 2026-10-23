

import os
from fastapi import FastAPI
from app.core.db import Base, engine
from app.api.v1.posts.router import router as post_router 
# Porque en el futuro podemos tener routers para otras cosas que no sean posts
from app.api.v1.auth.router import router as auth_router
from app.api.v1.uploads.router import router as upload_router
from app.api.v1.tags.router import router as tag_router
from app.api.v1.categories.router import router as category_router
from fastapi.staticfiles import StaticFiles # servimos los archivos estáticos
from dotenv import load_dotenv

from app.core.middleware import register_middleware

load_dotenv()

MEDIA_DIR = "app/media"

# dev -> sólo para entorno de desarrollo. 



def create_app() -> FastAPI:
    app = FastAPI(title="Mini Blog", swagger_ui_parameters={"persistAuthorization": True}) # crea la aplicación
    # swagger_ui_parameters={"persistAuthorization": True} -> Para que cuando recarga swagger no se vaya la autenticación
    Base.metadata.create_all(bind=engine) # dev. crea las tablas que falten.
    register_middleware(app) # registramos el middleware
    
    # montamos los routers:
    app.include_router(auth_router, prefix="/api/v1")
    # Porque en security.py definimos -> oauth2_scheme = OAuth2PasswordBearer(tokenUrl= "/api/v1/auth/login")
    # y en router.py hacemos sólo prefix de /auth y de /login
    app.include_router(post_router) 
    # FastAPI, incorpora a mi aplicación todos los endpoints que están definidos 
    # en post_router
    app.include_router(tag_router)
    app.include_router(upload_router)
    app.include_router(category_router)
    os.makedirs(MEDIA_DIR , exist_ok= True) # Creraá al carpeta app/media si no existe
    app.mount("/media", StaticFiles(directory= MEDIA_DIR), name="media")
    # Asocia la URL /media con la carpeta física app/media
    # para poder servir los archivos guardados como archivos estáticos.
    # Todo lo que llegue bajo /media lo gestionará StaticFiles, sirviendo archivos 
    # de esa carpeta.
    
    
    return app

app = create_app()

    




    

