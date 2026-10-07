import os
import shutil # para permisos para guardar y mover archivos
import uuid # genera cadena de texto alaeatoria para no repetir nombres
from fastapi import APIRouter, File, UploadFile, HTTPException, status

router = APIRouter(prefix="/upload", tags=["uploads"])
# prefix → afecta a la URL
# tags   → organiza la documentación

MEDIA_DIR = "app/media"

@router.post("/bytes")
async def upload_bytes(file: bytes = File(...) ):
    # bytes es una clase que está dentro de Python
    return {
        "filename": "archivo_subido",
        "size_bytes": len(file)
      
    }

@router.post("/file")
async def upload_file(file: UploadFile = File(...)):
    # UploadFile hay que importarlo porque no pertence a Pyhton -> FastAPI/Starlette
    return {"filename": file.filename,
            "content_type": file.content_type
    }
    
@router.post("/save")
async def save_file(file: UploadFile = File(...)):
    if file.content_type not in ["image/png", "image/jpeg"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sólo se permiten imágenes PNG o JPEG"
        )
    ext = os.path.splitext(file.filename)[1] # png, .jpeg
    # .splitext separa el nombre del archivo en nombre y ext. Para la extensión -> [1]
    # Devuelve la extensión incluyendo el punto
    filename = f"{uuid.uuid4().hex}{ext}"
    # uuid.uuid4() -> genera un identificador UUID aleatorio
    # algo parecido a:
    # 550e8400-e29b-41d4-a716-446655440000
    # on .hex obtienes sus caracteres hexadecimales sin guiones:
    # 550e8400e29b41d4a716446655440000
    # la f-string concatena eso con ext
    # El UUID se usa deliberadamente para crear un nombre único y controlado 
    # por el servidor.
    
    file_path= os.path.join(MEDIA_DIR, filename)
    # os.path.join() une la carpeta y el nombre del archivo para construir su ruta
    
    with open(file_path, "wb") as buffer: # abrimos el archivo en modo escritura
        # Crea o abre el archivo de destino en modo escritura binaria.
        # "with" se encarga de cerrarlo automáticamente.
        shutil.copyfileobj(file.file, buffer)
        # Copia el contenido del archivo recibido (UploadFile)
        # al archivo de destino, sin cargarlo entero en RAM.
        # shutil.copyfileobj(origen, destino)
    #  1 )creo un archivo vacío con la extensión del archivo original y 
    #  un nombre aleatorio y 
    #  2) relleno el contenido del nuevo archivo con el del archivo original
    return {
        "filename": filename,
        "content_type": file.content_type,
        "url": f"/media/{filename}",
    }