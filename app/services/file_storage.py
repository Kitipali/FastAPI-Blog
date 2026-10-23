# Este servicio se va a encargar de guardar el archivo en el disco local
import os
import shutil # para permisos para guardar y mover archivos
import uuid # genera cadena de texto alaeatoria para no repetir nombres
from fastapi import APIRouter, File, UploadFile, HTTPException, status


MEDIA_DIR = "app/media"
ALLOW_MIME = ["image/png", "image/jpeg"]
MAX_MB = int(os.getenv("MAX_UPLOAD_MB", "2"))
CHUNKS = 1024 * 1024


def ensure_media_dir() -> None:
    os.makedirs(MEDIA_DIR, exist_ok=True)
    
    

def save_uploaded_image(file: UploadFile ) -> dict: # Por qué quitamos UploadedFile = File(...)?
    if file.content_type not in ALLOW_MIME:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sólo se permiten imágenes PNG o JPEG"
        )
    ensure_media_dir() # Para asegurarnos que la carpeta está creada
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
    
    # class _ChunkCounter: # lee los chunks que se estén generando
    #     def __init__(self, f):
    #         self._f = f
    #         self.calls = 0
    #         self.sizes = []
    #     def read(self, n=-1):
    #         data = self._f.read(n)
    #         if data:
    #             self.calls += 1
    #             self.sizes.append(len(data))
    #         return data
    #     def __getattr__(self, name):  # delega cualquier otro atributo
    #         return getattr(self._f, name)

    # reader = _ChunkCounter(file.file)
    
    
    
    
    with open(file_path, "wb") as buffer: # abrimos el archivo en modo escritura
        # Crea o abre el archivo de destino en modo escritura binaria.
        # "with" se encarga de cerrarlo automáticamente.
        shutil.copyfileobj(file.file, buffer, length=CHUNKS) # si  usáramos el contador en lugar de file.file -> reader
        # Copia el contenido del archivo recibido (UploadFile)
        # al archivo de destino, sin cargarlo entero en RAM.
        # shutil.copyfileobj(origen, destino)
        # length=1024 * 1024 -> se irán copiando en pedazos de 1 MB en 1 MB
        # Sin esto ya se hace por bloques pero así establecemos el tamaño de cada uno
    #  1 )creo un archivo vacío con la extensión del archivo original y 
    #  un nombre aleatorio y 
    #  2) relleno el contenido del nuevo archivo con el del archivo original
    
    size = os.path.getsize(file_path)
    if size > MAX_MB * CHUNKS:
        os.remove(file_path) # eliminamos el archivo que acabamos de guardar
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE, 
            detail= f"Archivo demasiado grande (>{MAX_MB} MB)"
        )
        
    return {
        "filename": filename,
        "content_type": file.content_type,
        "url": f"/media/{filename}",
        # "size": size,
        # "chunk_size_used": CHUNKS,
        # "chunk_calls": reader.calls,
        # "chunk_sizes_sample": reader.sizes[:5]
        
    }