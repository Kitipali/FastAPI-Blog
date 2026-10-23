# FastAPI Blog API

API REST para la gestión de un blog, desarrollada como proyecto de aprendizaje de **FastAPI**. El objetivo es construir un backend organizado en capas, con persistencia relacional, validación de datos, autenticación y operaciones sobre publicaciones, usuarios, categorías y etiquetas.

> **Contexto:** proyecto realizado durante un curso de FastAPI. Este README documenta los componentes trabajados. Antes de publicarlo, conviene contrastar las rutas y los requisitos con la versión definitiva del código.

## Tecnologías

- **Python**: lenguaje principal.
- **FastAPI**: framework para crear la API REST y generar documentación OpenAPI.
- **Pydantic**: validación de entradas y serialización de respuestas.
- **SQLAlchemy**: modelos ORM, consultas y sesiones de base de datos.
- **SQLite**: base de datos utilizada durante el desarrollo.
- **Uvicorn / FastAPI CLI**: servidor de desarrollo.
- **Autenticación con tokens JWT**: protección de operaciones y gestión de permisos.

## Funcionalidades implementadas durante el curso

- Operaciones de creación, consulta y actualización de publicaciones.
- Consulta de publicaciones mediante identificador y mediante **slug** legible.
- Paginación, búsqueda, ordenación y filtros.
- Gestión de categorías y etiquetas, con relaciones entre entidades.
- Modelos de entrada, actualización y respuesta separados mediante Pydantic.
- Acceso a datos mediante clases de repositorio y sesiones de SQLAlchemy.
- Autenticación y dependencias para controlar el acceso de usuarios según permisos.
- Middlewares para medir tiempos de respuesta, registrar peticiones y generar identificadores de solicitud.
- Configuración de CORS para permitir solicitudes desde un frontend autorizado.
- Scripts de carga de datos de prueba (*seed*).

## Organización del código

La aplicación se encuentra bajo `app/` y separa las responsabilidades principales:

```text
app/
├── api/
│   └── v1/
│       ├── posts/
│       ├── categories/
│       ├── tags/
│       └── ...
├── core/
├── models/
├── utils/
└── ...
```

*Árbol orientativo:* los nombres exactos de todos los archivos y carpetas deben contrastarse con el repositorio.

### Capas y responsabilidades

| Componente | Responsabilidad |
| --- | --- |
| **Router** | Define los endpoints HTTP, parámetros, dependencias y códigos de respuesta. |
| **Schemas (Pydantic)** | Valida los datos recibidos y define qué información se devuelve al cliente. |
| **Repository** | Encapsula las consultas y operaciones de persistencia con SQLAlchemy. |
| **ORM models** | Representa tablas, columnas y relaciones de la base de datos. |
| **Core** | Centraliza configuración, conexión a base de datos y seguridad. |
| **Middleware** | Ejecuta lógica transversal antes y después de procesar las peticiones. |

Esta separación evita mezclar las reglas HTTP con los detalles de acceso a datos y facilita las pruebas y el mantenimiento.

## API y operaciones

### Publicaciones (*posts*)

Durante el desarrollo se trabajó con operaciones como las siguientes:

| Método | Ruta orientativa | Descripción |
| --- | --- | --- |
| `GET` | `/posts` | Listar publicaciones con búsqueda, paginación y ordenación. |
| `GET` | `/posts/{id}` | Consultar una publicación por identificador. |
| `POST` | `/posts` | Crear una publicación. |
| `PUT` | `/posts/{id}` | Actualizar una publicación. |
| `GET` | `/posts/by-tags` | Filtrar publicaciones por etiquetas. |
| `GET` | `/posts/{slug}` | Consultar una publicación por slug, según la ruta final definida. |

**Nota:** la tabla resume los ejercicios del curso, no constituye un inventario verificado de las rutas definitivas. La ubicación de cada endpoint bajo `/api/v1` y las posibles rutas alternativas deben consultarse en `/docs`.

### Parámetros de consulta

Se incorporaron conceptos habituales en APIs REST:

- **Paginación:** `page`, `per_page`, `limit` y/o `offset`, según el endpoint.
- **Búsqueda:** filtrado mediante un texto de consulta.
- **Ordenación:** campos como `order_by` y sentido `direction` (`asc` / `desc`).
- **Respuesta resumida o completa:** posibilidad de incluir o excluir el contenido de la publicación.
- **Filtrado por etiquetas:** consultas asociadas a relaciones entre publicaciones y etiquetas.

Los parámetros se validan mediante anotaciones de tipos y utilidades de FastAPI como `Query` y `Path`.

## Modelos y validación

La aplicación diferencia entre los **modelos ORM** y los **schemas Pydantic**:

- Los modelos ORM describen cómo se almacenan los datos.
- Los schemas de creación validan los datos necesarios para insertar registros.
- Los schemas de actualización permiten modificar únicamente los campos enviados.
- Los schemas públicos controlan los campos visibles en las respuestas.

Entre los patrones utilizados están `Field`, validadores de Pydantic, `ConfigDict(from_attributes=True)` y `model_dump(exclude_unset=True)` para actualizaciones parciales.

### Relaciones entre entidades

El proyecto trabaja con entidades como publicaciones, usuarios, categorías y etiquetas. Las relaciones se consultan mediante SQLAlchemy, incluyendo operaciones con `join`, `group_by`, `func.count`, ordenación y agregaciones. Se estudió, por ejemplo, cómo obtener la etiqueta más utilizada.

## Slugs únicos

Para ofrecer URLs más legibles, se añadió la generación de *slugs* a partir del título de las publicaciones.

Ejemplo conceptual:

```text
"Introducción a FastAPI"  ->  introduccion-a-fastapi
"Introducción a FastAPI"  ->  introduccion-a-fastapi-2
```

El proceso normaliza el texto y comprueba si el slug ya existe para evitar duplicados. El modelo ORM incluye una restricción de unicidad para reforzar esta regla en la base de datos.

## Autenticación y autorización

Se trabajó con autenticación basada en tokens **JWT** y dependencias reutilizables para identificar al usuario autenticado y aplicar controles de acceso.

La distinción principal es:

- **Autenticación:** comprobar quién realiza la petición.
- **Autorización:** comprobar qué operaciones tiene permitido realizar.

El código del curso incluye dependencias asociadas a distintos niveles de acceso, como usuario, editor y administrador. Las credenciales y claves de firma deben configurarse fuera del repositorio.

## Middlewares

Se añadieron componentes que intervienen en el ciclo de vida de cada petición:

| Middleware | Objetivo |
| --- | --- |
| Tiempo de proceso | Calcular la duración de una solicitud y devolverla en `X-Process-Time`. |
| Registro de solicitudes | Mostrar información de entrada y salida de las peticiones. |
| Identificador de solicitud | Generar un valor `X-Request-ID` por petición. |
| Bloqueo por IP | Ejemplo didáctico de rechazo de solicitudes procedentes de direcciones definidas. |
| CORS | Autorizar orígenes concretos para las solicitudes realizadas desde navegadores. |

**Consideración técnica:** un identificador de solicitud resulta especialmente útil cuando también se incorpora a los registros de la aplicación. CORS no sustituye la autenticación ni los permisos.

## Base de datos

Durante el desarrollo se utilizó **SQLite** con SQLAlchemy. La conexión se gestiona mediante un motor y sesiones proporcionadas a los endpoints a través de dependencias de FastAPI.

Conviene recordar que `Base.metadata.create_all()` crea las tablas que no existen, pero **no modifica automáticamente** las tablas ya creadas cuando se añaden o cambian columnas. Para proyectos que evolucionan, una herramienta de migraciones como Alembic es una mejora natural.

## Puesta en marcha

### 1. Obtener el código

```bash
git clone https://github.com/Kitipali/FastAPI-Blog.git
cd FastAPI-Blog
```

### 2. Preparar Python

Se recomienda crear un entorno virtual independiente:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Instalar las dependencias

Si el repositorio contiene `requirements.txt`:

```bash
python -m pip install -r requirements.txt
```

> Si todavía no se ha generado `requirements.txt`, habrá que incorporarlo antes de que otras personas puedan reproducir la instalación fácilmente.

### 4. Configurar el entorno

Revisar las variables utilizadas por `app/core/` y proporcionar sus valores localmente. No subir al repositorio secretos, contraseñas, tokens ni archivos `.env` reales.

### 5. Ejecutar el servidor

Desde la raíz del proyecto, utilizar el punto de entrada definido en el código. Por ejemplo, **si** la aplicación se expone como `app` en `app/main.py`:

```bash
uvicorn app.main:app --reload
```

Si se utiliza una factoría de aplicación, el comando de arranque puede ser distinto; debe adaptarse a la implementación final.

### 6. Consultar la documentación

Con el servidor en marcha:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Especificación OpenAPI: `http://127.0.0.1:8000/openapi.json`

## Aspectos aprendidos

Este proyecto ha permitido practicar:

1. Diseño de endpoints REST con FastAPI.
2. Validación y serialización con Pydantic.
3. Consultas y relaciones con SQLAlchemy.
4. Inyección de dependencias mediante `Depends`.
5. Separación de routers, modelos y repositorios.
6. Autenticación, permisos y protección de rutas.
7. Middlewares y política CORS.
8. Paginación, filtros, ordenación y agregaciones SQL.
9. Uso de Git y GitHub para controlar la evolución del código.

## Mejoras futuras

- Añadir pruebas automatizadas de endpoints, permisos y acceso a datos.
- Incorporar migraciones de base de datos con Alembic.
- Documentar y fijar versiones de dependencias.
- Mejorar los registros de la aplicación, asociándolos al identificador de petición.
- Añadir un ejemplo de configuración sin secretos (`.env.example`).
- Preparar el despliegue y la configuración para producción.

## Estado del proyecto

Proyecto educativo desarrollado durante un curso de FastAPI. Su propósito principal es consolidar los fundamentos de construcción de APIs y servir como referencia de aprendizaje.

---

**Autor:** [Kitipali](https://github.com/Kitipali)
