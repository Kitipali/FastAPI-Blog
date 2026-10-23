

import typer
# Biblioteca que construte la interfaz de línea de comandos
from app.seeds.service import run_all, run_categories, run_tags, run_users


app = typer.Typer(help= "Seeds: users, categories, tags")
# creamos uan aplicación de línea de comandos
# argumento help ->  establece una descripción que Typer puede mostrar al solicitar ayuda.

@app.command("all") # Cuando el usuario escriba el comando all, ejecuta la función all_().
def all_(): # añadimos "_" porque all es una palabra reservada
     print("Entrando en el comando ALL")
     run_all()
     typer.echo("Todos los seeds creados")
     # muestra un mensaje en la terminal. Parecido a print


@app.command("users")
def users(): # esta función será un comando de consola
    run_users()
    typer.echo("Usuarios cargados")

@app.command("categories")
def categories(): 
    run_categories()
    typer.echo("Categorias cargadas")    
    
@app.command("tags")
def tags(): 
    run_tags()
    typer.echo("Etiquetas cargadas")  