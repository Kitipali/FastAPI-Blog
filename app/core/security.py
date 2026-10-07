import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

SECRET_KEY = os.getenv("SECRET_KEY","change-me-in-prod")
ALGORITHM = "HS256" # Va a ocupar un HMAC -> Rápido y eficiente
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES","30"))
# Para establecer el tiempo de caducidad del token
# 30 minutos para que el token expire


# Creo una variable donde está la La URL donde el cliente puede autenticarse para conseguir el token:
oauth2_scheme = OAuth2PasswordBearer(tokenUrl= "/api/v1/auth/login")
# Usaremos este objeto como dependencia
credentials_exc = HTTPException(
        status_code= status.HTTP_401_UNAUTHORIZED,
        detail= "No autenticado",
        headers= {"WWW-Authenticate": "Bearer"} 
)
        # WWW-Authenticate es un header HTTP estándar. Significa:
        # «No estás autenticado. Para acceder a este recurso debes autenticarte 
        # mediante el esquema Bearer.» -> definidpo en oauth2_scheme
        #"Bearer" -> texto del protocolo HTTP

def raise_expired_token():
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

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy() 
    # Crea una copia del diccionario recibido -> Para añadir info al payload y 
    # no modificar el diccionario original data
    
    expire = datetime.now(tz=timezone.utc) + (expires_delta or  timedelta(minutes= ACCESS_TOKEN_EXPIRE_MINUTES))
    # expires delta -> viene del usuario: primera opción
    # timedelta -> Los minutos que establecemos en la variable ACCESS_TOKEN_EXPIRE_MINUTES
    to_encode.update({"exp":expire})
    # actualizamos el diccionario añadiendo el tiempo de expiración
    token = jwt.encode(payload=to_encode, key= SECRET_KEY,algorithm = ALGORITHM )
    # Codificamos en un toke el payload, la key y el algoritmo
    return token

def decode_token(token: str)-> dict: # comprueba técnicamente el JWT
    payload = jwt.decode(jwt= token, key = SECRET_KEY, algorithms=[ALGORITHM])
    return payload
# No se limita a «decodificar» en el sentido de leer el contenido. 
# jwt.decode() con PyJWT verifica el token: 
    # comprueba su firma usando SECRET_KEY, 
    # que el algoritmo permitido sea HS256 y también 
    # valida exp si existe.

async def get_current_user(token: str = Depends(oauth2_scheme)): # interpreta ese payload como un usuario
    
    
    try:
        payload= decode_token(token)
        sub: Optional[str] = payload.get("sub")
        username: Optional[str] = payload.get("username")
        if not sub or not username:
            raise credentials_exc
        # El JWT puede ser técnicamente válido, pero para nuestra aplicación no sirve
        # como credencial si no contiene sub y username
        return {"email":sub, "username": username}
    except ExpiredSignatureError: # cuando el token ya no es válido
        raise raise_expired_token() #como función 
    except InvalidTokenError:
        raise credentials_exc # como variable

        