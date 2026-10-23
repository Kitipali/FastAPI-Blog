from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Role = Literal["user","editor", "admin"]
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True) 
    # Permite construir el schema leyendo atributos de un objeto,
    # por ejemplo una instancia ORM, además de recibir un diccionario.
    

class UserPublic(UserBase): # cómo quieres representar un usuario hacia fuera
    # datos del USUARIO que puedo devolver al cliente
    id:int
    role: Role
    is_active: bool

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)
    full_name: Optional[str] = None
 
class UserLogin(BaseModel):
    email: EmailStr
    password: str   

class TokenResponse(BaseModel): # Lo que se le entrega al cliente al hacer login
    # añado atributos a esta clase:
    access_token: str
    token_type: str = "bearer"
    user: UserPublic

class RoleUpdate(BaseModel):
    role: Role
    
class TokenData(BaseModel): # los datos que esperamos encontrar dentro del JWT
    sub: str
    username: str
    
