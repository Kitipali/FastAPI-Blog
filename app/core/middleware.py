

import time
import uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi. middleware.cors import CORSMiddleware

BLACKLIST = {}
def register_middleware(app: FastAPI): 
    # La función recibe como argumento una instancia de FastAPI, es decir, 
    # la aplicación que he creado en main.py.
    app.add_middleware(CORSMiddleware,
                       allow_origins=["http://127.0.0.1:555", "http://localhost:5173"], # qué orígenes pueden acceder a mi API desde JavaScript en un navegador
                       allow_credentials=True, # Permite que las respuestas CORS autoricen peticiones con credenciales, como cookies o determinadas formas de autenticación gestionadas por el navegador.
                       allow_methods =["*"], # Permite todos los métodos HTTP en las peticiones CORS:GET, POST, PUT, PATCH, DELETE, etc
                       allow_headers =["*"] # Permite todas las cabeceras solicitadas por el frontend en las comprobaciones CORS.
    )
    # la diferencia con los decoradores es que ORSMiddleware ya viene implementado por Starlette, 
    # la biblioteca sobre la que se construye FastAPI.
    @ app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        # call_next sirve para invocar la siguiente acción
        # request -> objeto que representa la petición HTTP recibida
        # request contiene: la URL, las cabeceras y otros datos de la petición
        # call_next -> unción que FastAPI proporciona al middleware para continuar procesando la petición
        start = time.perf_counter()
        # perf_counter -> ontador de alta resolución, expresado en segundos.
        response = await call_next(request) # esperamos la respuesta de call_next
        process_time = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{process_time:.4f} s"
        return response
    
    @app.middleware("http")
    async def log_request(request: Request, call_next):
        print(f"**ENTRADA: {request.method} {request.url} ** ")
        response= await call_next(request)
        print(f"**SALIDA: {response.status_code} ** ")
        return response
    
    @app.middleware("http")
    async def add_request_id_header(request: Request, call_next):
        request_id = str(uuid.uuid4())
        response= await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    # Su función es asignar un identificador único a cada petición HTTP
    # y devolverlo en una cabecera de la respuesta.
    
    @app.middleware("http")
    async def block_ip_middleware(request: Request, call_next):
        client_ip = request.client.host
        # obtenemos IP del cliente
            # .cliente -> info de la conexión del cliente
            # .host -> dirección IP del cliente
        if client_ip in BLACKLIST:
            raise HTTPException(
                status_code= 403, detail = "Acceso denegado a esta IP")
        return await call_next(request)
    # Este  es un middleware para bloquear peticiones según la dirección IP del cliente.