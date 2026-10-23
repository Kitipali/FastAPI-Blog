# la parte de tu aplicación que se encarga de consultar, crear y modificar usuarios 
# en la base de datos.


from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User

class UserRepository:
    def __init__(self, db: Session):
        self.db = db
    def get(self, user_id:int) -> User | None:
        return self.db.get(User, user_id)
        # obtenemos el User a través de user_id
        # Usamos get porque es uiser_id es clave primaria
        # db.get(ModeloORM, clave_primaria)
    
    def get_by_email(self, email:str) -> User | None:
        query = select(User).where(User.email == email)
        # aquí ya no es clave primaria
        return self.db.execute(query).scalar_one_or_none()
    
    def create(self, email:str, hashed_password:str, full_name: str | None) -> User:
        user = User(email=email, hashed_password= hashed_password, full_name= full_name)
        # Creamos una instancia del modelo SQLAlchemy User
        self.db.add(user)
        # Incorporamos este objeto a la sesión
        self.db.flush()
        # flush() envía a la base de datos las operaciones pendientes de la sesión, 
        # como los INSERT y UPDATE, sin confirmar todavía la transacción.
        # obetenemos el user.id 
        # refresh() vuelve a consultar el estado del objeto en la base de datos y actualiza sus atributos.
        # Lo hacemos en el endpoint
        return user
    
    def set_role(self, user:User, role: str) -> User: # Para modificar el rol
        user.role = role
        # modificamos el atributo
        self.db.add(user)
        self.db.flush() 
        self.db.refresh(user)
        # el profesor no puso flush pero mejor ponerlo porque con solo refresh recupera el valor 
        # de antes del cambio
        return user 