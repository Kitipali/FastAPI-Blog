# Archivo de entrada / inicio
from .author import AuthorORM
from .tag import TagORM
from .post import PostORM, post_tags

__all__= ["AuthorORM","TagORM", "PostORM", "post_tags"]
# si ponemos que importe todo de este archivo esto es lo que se importará
# si quiero que algo no se importe, lo quito de esta lista
