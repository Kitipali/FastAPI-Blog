from pydantic import BaseModel, ConfigDict

# Definimos tres esquemas Pydantic distintos para tres momentos diferentes 
# de la autenticación:


class Token(BaseModel): # Lo que se le entrega al cliente al hacer login
    # añado atributos a esta clase:
    access_token: str
    token_type: str = "bearer"
    
class TokenData(BaseModel): # los datos que esperamos encontrar dentro del JWT
    sub: str
    username: str
    
class UserPublic(BaseModel): # cómo quieres representar un usuario hacia fuera
    # datos del USUARIO que puedo devolver al cliente
    email:str
    username: str
    model_config = ConfigDict(from_attributes=True) 
    # Permite construir el schema leyendo atributos de un objeto,
    # por ejemplo una instancia ORM, además de recibir un diccionario.