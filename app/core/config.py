import os



class settings(): # en lugar constantes ahora tenemos atributos de clase
    JWT_SECRET: str = os.getenv("SECRET_KEY","change-me-in-prod")
    JWT_ALG: str = "HS256" # Va a ocupar un HMAC -> Rápido y eficiente
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES","30"))
    # Para establecer el tiempo de caducidad del token
    # 30 minutos para que el token expire