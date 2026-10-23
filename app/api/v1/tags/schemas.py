


from pydantic import BaseModel, ConfigDict, Field


class TagPublic(BaseModel): # devolver una etiqueta al cliente
    id: int
    name: str = Field(..., min_length=2, max_length=30, 
                      description= "Nombre de la etiqueta")

    model_config = ConfigDict(from_attributes=True) 
    # Esta validación va a aceptar ORM. Si no lo ponemos, únicamente va a aceptar diccionarios

class TagCreate(BaseModel): # recibir los datos para crear una etiqueta
    name: str = Field(..., min_length=2, max_length=30, 
                      description= "Nombre de la etiqueta")
    
class TagUpdate(BaseModel): # recibir los datos para actualizar una etiqueta
    name: str = Field(..., min_length=2, max_length=30, 
                      description= "Nombre de la etiqueta")
    
class TagWithCount(TagPublic): # Devolver una etiqueta y cuántos posts la utilizan
    uses: int
    
    
    
    