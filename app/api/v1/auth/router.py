
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from .schemas import Token, UserPublic
from fastapi.security import OAuth2PasswordRequestForm
from app.core.security import create_access_token, get_current_user

FAKE_USERS = {
    "ricardo@example.com": {"email": "ricardo@example.com", "username": "ricardo", "password": "secret123"},
    "alumno@example.com":  {"email": "alumno@example.com",  "username": "alumno",  "password": "123456"},
}

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model= Token)
async def login(form_data:OAuth2PasswordRequestForm= Depends()): # equivale a form_data: OAuth2PasswordRequestForm = Depends(OAuth2PasswordRequestForm)
    user = FAKE_USERS.get(form_data.username)
    if not user or user["password"] != form_data.password:
        # si no encuentra ese usuario en FAKE_USERS -> not user
        # si la contraseña es distinta a la guardad -> user["password"] != form_data.password
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail = "Credenciales inválidas" )
    token= create_access_token(
        data = {"sub": user["email"], "username": user["username"]},
        expires_delta= timedelta(minutes=30)
    )
    return {"access_token": token, "token_type":"bearer"}
    # create_access_token() añade la expiración y genera el JWT.




@router.get("/me", response_model=UserPublic) 
# dime  quién soy según el token que te estoy enviando
async def read_me(current=Depends(get_current_user)):
    return {"email": current["email"], "username": current["username"]}
# Antes de ejecutar read_me, ejecuta get_current_user() y guarda lo que 
# devuelva en current
# get_current_user() depende a su vez de oauth2_scheme q obtiene el token
# current=Depends(get_current_user) -> Dame el usuario autenticado