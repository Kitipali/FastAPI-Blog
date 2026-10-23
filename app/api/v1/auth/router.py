
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.api.v1.auth.repository import UserRepository # Consultar y guardar usuarios
from app.core.db import get_db
from app.models.user import User
from .schemas import RoleUpdate, TokenResponse, UserCreate, UserLogin, UserPublic
from fastapi.security import OAuth2PasswordRequestForm
from app.core.security import create_access_token, get_current_user, hash_password, verify_password, require_admin, auth2_token

# Creación del router:
router = APIRouter(prefix="/auth", tags=["auth"])

# POST /auth/register -> Registrar un usuario

@router.post("/register", response_model = UserPublic, status_code= status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    repository = UserRepository(db) # le pasamos la sesión
    if repository.get_by_email(payload.email): # comprueba si existe el email
        raise HTTPException (status_code=400, detail ="Email ya registrado")
    user = repository.create( 
        email=payload.email,
        hashed_password= hash_password(payload.password), # no guardamos el password sino el hash
        full_name=payload.full_name
    )
    db.commit()
    db.refresh(user)
    return UserPublic.model_validate(user) # transforma el objeto SQLAlchemy en un esquema Pydantic.
# register() -> registrar un usuario
# 1º crea el repositorio 2º le pasa la sesión



# POST /auth/login -> Comprueba credenciales y entregar un JWT

@router.post("/login", response_model= TokenResponse)
async def login(payload: UserLogin, db: Session = Depends(get_db)):
    repository = UserRepository(db)
    user= repository.get_by_email(payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail= "Credenciales inválidas")
    token = create_access_token(sub= str(user.id)) # crea el jwt
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))

    # create_access_token() añade la expiración y genera el JWT.



# GET /auth/me -> Obtiene los datos del usuario autenticado

@router.get("/me", response_model=UserPublic) 
# dime  quién soy según el token que te estoy enviando
async def read_me(current: User = Depends(get_current_user)):
    return UserPublic.model_validate(current)
# Antes de ejecutar read_me, ejecuta get_current_user() y guarda lo que 
# devuelva en current
# get_current_user() depende a su vez de oauth2_scheme q obtiene el token
# current=Depends(get_current_user) -> Dame el usuario autenticado


# PUT /auth/role/{user_id} ->Modificar el rol de un usuario por parte del admnistrador
@router.put("/role/{user_id}", response_model= UserPublic)
def set_role(
    payload: RoleUpdate,
    user_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin)
    
):
    repository = UserRepository(db)
    user = repository.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail ="Usuario no encontrado")
    updated = repository.set_role(user, payload.role)
    
    db.commit()
    db.refresh(user)
    
    return UserPublic.model_validate(updated)

@router.post("/token")
async def token_endpoint(response=Depends(auth2_token)):
    return response