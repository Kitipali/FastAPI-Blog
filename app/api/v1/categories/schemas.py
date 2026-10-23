

from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    name: str = Field(min_length=2, max_length = 60)
    slug: str = Field(min_length=2, max_length = 60)
    
class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel): # la categoría que devuelve
    name: str | None  = Field(default= None, min_length=2, max_length = 60)
    slug: str | None  = Field(default= None, min_length=2, max_length = 60)
# al modificar la categoría tal vez sólo querimas modificar un cambio
class CategoryPublic(CategoryBase):
    id: int
    model_config={"from_attributes": True}
    # tb se podría así  model_config = ConfigDict(from_attributes=True)
    
    
