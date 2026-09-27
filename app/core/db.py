import os # # Para acceder, entre otras cosas, a las variables de entorno
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./blog.db")
# print("Conectado a: ", DATABASE_URL)
# borramos esto porque es innecesario y peligroso
# Reconocemos un archivo .env
# si no hay variable de entono toma el valor por defecto en sqlite:///./blog.db
# sqlite:///(protocolo)   +  ./blog.db (ruta del archivo) donde . es directorio actual


engine_kwargs = {} # sólo en sqlight
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"]={"check_same_thread": False} # configuración específica  de sql lite
#Comprueba si la base de datos es SQLite

engine = create_engine(DATABASE_URL, echo=True, future=True, **engine_kwargs)
# Creamos una conexión
# el motor de SQLAlchemy: el objeto que sabe dónde está mi base de datos y cómo debo comunicarme con ella
# echo=True -> para ver en terminal qué comandos sql se están ejecutando
# future=True -> queremos ocupar la sintaxis moderna de sql alchemy 2
# **engine_kwargs sólo par sqlite con postegresql no
# autocommit=False -> Tenemos un control explícito en el commit


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
# Creamos una "fábrica se sesiones", no una sesión
# class_=Session -> le dice a sessionmaker qué clase debe utilizar para fabricar las sesiones.
# después haremos:
    # db = Sessionlocal() ->se crea una sesión y la pregunta será: de que clase es db? -> class_=Session
# autoflush=False -> No envía cambios hasta hacer el commit


# DeclarativeBase -> Hace que SQLAlchemy pueda reconocer las clases que heredan de Base como 
# modelos ORM y recopilar información sobre las tablas que representan.



class Base(DeclarativeBase):
    pass



def get_db():
# función para crear la sesión cada vez que entre en cada uno de los endpoints y 
# que la cirre al salir cuando no la ocupe
    db = SessionLocal() # inicializamos una sesión
    try:
        yield db 
        # fastapi espera una dependencia generadora. Es como una "pausa"
        #yield db entrega db al endpoint ->get_db se queda "pausada"
        # si fuera return -> finalizaría la función
        # cuando el endpoint utiliza db -> termina el endpoint -> gt_db continúa después del yield
    finally:
        db.close() # se cierra la sesión
