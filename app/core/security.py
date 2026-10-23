import os
from datetime import datetime, timedelta, timezone
# datetime -> Obtener ña fecha y hor actual
# timedelta -> Sumar un intervalo de tiempo
# timezone-> Trabajar con UTC
from typing import Literal, Optional
from fastapi import Depends, HTTPException, status
# Depends -> Inyectar dependencias de fastapi
# status -> Utilizar constantes como HTTP_401_UNAUTHORIZED
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# OAuth2PasswordBearer -> Extraer tokens Bearer de las peticiones
import jwt
# jwt-> Crear y verificar JWT
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError, PyJWTError
from app.api.v1.auth.repository import UserRepository
from app.core.config import settings
# Leer la configuración de mi aplicación
from app.core.db import get_db
# Obtener una sesión de base de datos
from app.models.user import User
# modelo SQLAlchemy de usuarios
from sqlalchemy.orm import Session
# Tipo de la sesión SQLAlchemy
from pwdlib import PasswordHash
# PasswordHash es una clase de la biblioteca pwdlib que permite generar y verificar hashes de contraseñas.

password_hash = PasswordHash.recommended()
# Se crea un objeto que se usará para generar y verificar los hashes
# recommended() -> selecciona una configuración recomendada de hashing (basada en argon2)


# Creo una variable donde está la La URL donde el cliente puede autenticarse para conseguir el token:
oauth2_scheme = OAuth2PasswordBearer(tokenUrl= "/api/v1/auth/token")
# Le indica a FastAPI que la aplicación utiliza autenticación mediante tokens Bearer y dónde se pueden solicitar esos tokens.
# oauth2_scheme extrae la parte correspondiente al token de las peticiones a los endpoints protegidos
# Cuando escribo oken: 'str = Depends(oauth2_scheme)' -> FastAPI ejecuta esa dependencia y 
# proporciona el token como cadena.
# OAuth2PasswordBearer permite que Swagger muestre el botón 'Authorize'

# Usaremos este objeto como dependencia -> Una excepción reutilizable -> raise credentials_exc
credentials_exc = HTTPException(
        status_code= status.HTTP_401_UNAUTHORIZED,
        detail= "No autenticado",
        headers= {"WWW-Authenticate": "Bearer"} 
)
        # WWW-Authenticate es un header HTTP estándar. Significa:
        # «No estás autenticado. Para acceder a este recurso debes autenticarte 
        # mediante el esquema Bearer.» -> definido en oauth2_scheme
        #"Bearer" -> texto del protocolo HTTP

def raise_expired_token(): # función que, al ejecutarse, devuelve un objeto HTTPException -> Por eso después escribimos raise raise_expired_token()
    return HTTPException(
        status_code= status.HTTP_401_UNAUTHORIZED,
        detail= "Token expirado",
        headers= {"WWW-Authenticate": "Bearer"} # Para autenticarte aquí, debes usr el esquema Bearer
    # En el 401 indicamos al cliente que debe autenticarse
    # mediante un Bearer token.
    )

def raise_forbidden():
    return HTTPException(
        status_code= status.HTTP_403_FORBIDDEN,
        detail= "No tienes permisos suficientes",
    )


def invalid_credentials():
    return HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail= "No tienes permisos suficientes",
        )
    
    
def decode_token(token: str)-> dict: # comprueba técnicamente el JWT
    payload = jwt.decode(jwt= token, key = settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    return payload
# No se limita a «decodificar» en el sentido de leer el contenido. 
# jwt.decode() con PyJWT verifica el token: 
    # comprueba su firma usando SECRET_KEY, 
    # que el algoritmo permitido sea HS256 y también 
    # valida exp si existe.
# El payload podría contener 
    # {
    #     "sub": "15", -> Identifica al usuario
    #     "exp": 1791900000 -> Indica cuándo expira ek token
    # }




# def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
#     to_encode = data.copy() 
#     # Crea una copia del diccionario recibido -> Para añadir info al payload y 
#     # no modificar el diccionario original data
    
#     expire = datetime.now(tz=timezone.utc) + (expires_delta or  timedelta(minutes= settings.ACCESS_TOKEN_EXPIRE_MINUTES))
#     # expires delta -> viene del usuario: primera opción
#     # timedelta -> Los minutos que establecemos en la variable ACCESS_TOKEN_EXPIRE_MINUTES
#     to_encode.update({"exp":expire})
#     # actualizamos el diccionario añadiendo el tiempo de expiración
#     token = jwt.encode(payload=to_encode, key= settings.SECRET_KEY,algorithm = settings.ALGORITHM )
#     # Codificamos en un toke el payload, la key y el algoritmo
#     return token

def create_access_token(sub: str, minutes: int | None = None)-> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes= minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": sub,"exp": expire}, key=settings.JWT_SECRET, algorithm=settings.JWT_ALG)

# sub -> subjet -> Identificador del usuario. Habitual usar el ID del usuario . + estable que su email
# minutes: int | None = None -> Este parámetro es opcional.
    # Puedes llamar a la función así:
        # create_access_token(sub="15")
    # O con una duración personalizada:
        # create_access_token(sub="15", minutes=30)
# jwt.encode() genera un JWT firmado.
# Ojo la firma sirve para detectar modificaciones no para ocultar información
    

async def get_current_user(db: Session = Depends(get_db),token: str = Depends(oauth2_scheme))-> User: # interpreta ese payload como un usuario
    
    
    try:
        payload= decode_token(token)
        sub: Optional[str] = payload.get("sub")
        if not sub:
            raise credentials_exc
        # El JWT puede ser técnicamente válido, pero para nuestra aplicación no sirve
        # como credencial si no contiene sub y username
        
        
        user_id = int(sub)
        # Convertimos el user_id en un entero
    
    except ExpiredSignatureError: # cuando el token ya no es válido
        raise raise_expired_token() # como función 
    except InvalidTokenError:
        raise credentials_exc # como variable
    except PyJWTError:
        raise invalid_credentials()
    
    user = db.get(User, user_id) 
    # Buscamos el usuario en la base de datos
    # dentro de User vamos a buscar el user_id
    
    if not User or not User.is_active:
        raise invalid_credentials()
    
    return user
    
def hash_password(plain: str) -> str: # le pasamos la contraseña en texto plano para convertirla en hash
    return password_hash.hash(plain)
    # password_hash.hash(plain): genera un hash seguro de esa contraseña.
def verify_password(plain: str, hashed: str)-> bool: # Comprobar una contraseña, devuelve True o False
    return password_hash.verify(plain, hashed)

def require_role(min_role: Literal["user", "editor", "admin"]):
    order = {"user": 0, "editor": 1, "admin": 2}
    def evaluation(user: User = Depends(get_current_user)) -> User:
        if order[user.role] < order[min_role]:
            raise raise_forbidden()
        return user
    return evaluation # devuelve la función no el resultado pq queremos que gastapi lo ejecute después, cuando llegue una petición HTTP
# min_role -> el rol mínimo necesario
# order = {"user": 0, "editor": 1, "admin": 2} -> establece la jerarquía. No guarda usuarios 
# ni modifica la base de datos. Simplemente asigna un número a cada rol para poder compararlos.



# Esta función añade una pieza importante al sistema de autenticación: 
# permitir q Swagger obtenga 1 token JWT utilizando su formulario de autoriz. OAuth2.

async def auth2_token(form:OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Cuando dejas Depends() vacío, FastAPI utiliza automáticamente OAuth2PasswordRequestForm 
    # como dependencia.
    # Equivale a form: OAuth2PasswordRequestForm = Depends(OAuth2PasswordRequestForm)
    # antes usabamos un JSON ahora un formulario
    repository = UserRepository(db)
    user = repository.get_by_email(form.username)
    # form.username -> campo de username en swagger
    if not user or not verify_password(form.password,user.hashed_password):
        raise invalid_credentials()
    token = create_access_token(sub=str(user.id))
    return {"access_token": token, "token_type": "bearer"}


    
    


require_user = require_role("user")
require_editor = require_role("editor")
require_admin = require_role("admin")

# Aquí estás creando tres dependencias reutilizables.
# No son tres funciones evaluation escritas manualmente. Son tres funciones generadas a partir de la misma estructura, cada una con un valor distinto de min_role.
#Por ejemplo, para proteger un endpoint:
    # @router.delete("/{tag_id}")
    # def delete_tag(
    #     tag_id: int,
    #     user: User = Depends(require_admin)
    # ):
    #     ...