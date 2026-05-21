# Forum Backend

API REST asíncrona del foro interno, construida con **FastAPI** y **SQLAlchemy async**. Se conecta a una base de datos PostgreSQL (esquema compatible con Discourse) y utiliza **Celery + Redis** para tareas en segundo plano.

---

## Tabla de contenidos

- [Tecnologías](#tecnologías)
- [Requisitos previos](#requisitos-previos)
- [Instalación](#instalación)
- [Variables de entorno](#variables-de-entorno)
- [Ejecución en local](#ejecución-en-local)
- [Endpoints de la API](#endpoints-de-la-api)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Workers Celery](#workers-celery)
- [Pruebas unitarias](#pruebas-unitarias)
- [Docker](#docker)
- [Seguridad](#seguridad)

---

## Tecnologías

| Paquete | Versión | Rol |
|---|---|---|
| **FastAPI** | 0.115.5 | Framework HTTP asíncrono |
| **SQLAlchemy (async)** | 2.0.36 | ORM y connection pooling |
| **asyncpg** | 0.30.0 | Driver async para PostgreSQL (FastAPI) |
| **psycopg v3** | ≥ 3.2.0 | Driver sync para PostgreSQL (Celery) |
| **Pydantic v2** | 2.10.3 | Validación de esquemas y settings |
| **PyJWT** | 2.10.1 | Validación de tokens JWT (Azure AD / dev) |
| **httpx** | 0.28.1 | Cliente HTTP async (descarga de JWKS) |
| **mistune** | 3.0.2 | Renderizador Markdown → HTML |
| **beautifulsoup4** | 4.12.3 | Extracción de texto plano de HTML |
| **Pillow** | 11.0.0 | Redimensionado de imágenes y avatares |
| **Celery + Redis** | 5.4.0 | Cola de tareas en segundo plano |
| **python-multipart** | 0.0.20 | Soporte para file uploads |
| **uv** | — | Gestor de paquetes y entornos virtuales |

---

## Requisitos previos

- **Python ≥ 3.12**
- **[uv](https://docs.astral.sh/uv/)** instalado globalmente (`pip install uv` o `curl -Ls https://astral.sh/uv/install.sh | sh`)
- **PostgreSQL** con un esquema de Discourse existente (base de datos `discourse`)
- **Redis** (opcional en local — ver `CELERY_ENABLED=false`)

---

## Instalación

```bash
# Clonar el repositorio y entrar al directorio del backend
cd backend

# Crear entorno virtual e instalar todas las dependencias (incluyendo dev)
uv sync --group dev
```

Esto crea automáticamente `.venv/` e instala las dependencias listadas en `pyproject.toml`.

---

## Variables de entorno

Copia el archivo de ejemplo y completa los valores:

```bash
cp .env.example .env
```

| Variable | Descripción | Ejemplo |
|---|---|---|
| `DATABASE_URL` | Conexión async para FastAPI | `postgresql+asyncpg://user:pass@localhost:5432/discourse` |
| `DATABASE_URL_SYNC` | Conexión sync para Celery | `postgresql+psycopg://user:pass@localhost:5432/discourse` |
| `AZURE_AD_TENANT_ID` | Tenant ID de Azure AD / Entra ID | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| `AZURE_AD_CLIENT_ID` | Client ID de la app registrada en Azure | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| `AZURE_AD_AUDIENCE` | Audience del token de acceso | `api://xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| `CORS_ORIGINS` | Lista JSON de orígenes permitidos | `["http://localhost:4200"]` |
| `DEBUG` | Habilita logs SQL y docs de la API | `true` / `false` |
| `DEV_MODE` | Acepta tokens JWT locales (sin Azure AD) | `true` / `false` |
| `DEV_JWT_SECRET` | Secreto HS256 para tokens de dev | Mínimo 32 caracteres aleatorios |
| `CELERY_ENABLED` | Activa o desactiva la cola de tareas | `true` / `false` |
| `CELERY_BROKER_URL` | URL del broker Redis | `redis://localhost:6379/0` |
| `UPLOADS_PATH` | Directorio local de imágenes subidas | `./uploads` |
| `SITE_BASE_URL` | URL pública del servidor | `http://localhost:8000` |

> **En producción:** `DEV_MODE` debe ser `false` y `DEV_JWT_SECRET` debe ser un secreto fuerte. El servidor lanza un error en arranque si detecta el secreto por defecto con `DEV_MODE=false`.

Generar un secreto seguro:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Ejecución en local

### Con uv (recomendado)

```bash
# Servidor de desarrollo con reload automático
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

O usando el script incluido:

```bash
uv run python run.py
```

### Con Make

```bash
make run      # Inicia el servidor
make install  # Instala dependencias
make test     # Ejecuta los tests
make lint     # Verifica el estilo
make format   # Formatea el código
```

Una vez iniciado, la API estará disponible en:

- **API base:** `http://localhost:8000/api`
- **Docs interactivos (Swagger):** `http://localhost:8000/api/docs` *(solo con `DEBUG=true`)*
- **ReDoc:** `http://localhost:8000/api/redoc` *(solo con `DEBUG=true`)*
- **Health check:** `http://localhost:8000/api/health`

---

## Estructura del proyecto

```
backend/
├── app/
│   ├── core/
│   │   ├── config.py          # Settings con Pydantic (lee .env)
│   │   ├── database.py        # Engine async y sesión SQLAlchemy
│   │   ├── guardian.py        # Sistema de permisos por rol
│   │   └── security.py        # Validación JWT (Azure AD + dev tokens)
│   ├── models/                # Modelos SQLAlchemy (tablas de Discourse)
│   │   ├── category.py
│   │   ├── post.py
│   │   ├── post_action.py     # Likes y bookmarks
│   │   ├── topic.py
│   │   ├── upload.py
│   │   └── user.py
│   ├── routers/               # Endpoints FastAPI
│   │   ├── auth.py
│   │   ├── bookmarks.py
│   │   ├── categories.py
│   │   ├── posts.py
│   │   ├── search.py
│   │   ├── topics.py
│   │   ├── uploads.py
│   │   └── users.py
│   ├── schemas/               # Esquemas Pydantic (request / response)
│   │   ├── category.py
│   │   ├── post.py
│   │   ├── topic.py
│   │   ├── upload.py
│   │   └── user.py
│   ├── services/
│   │   ├── markdown_renderer.py   # Markdown → HTML (mistune, sanitizado)
│   │   ├── post_creator.py        # Lógica de creación de posts
│   │   └── topic_creator.py       # Lógica de creación de temas
│   ├── tasks/
│   │   ├── celery_app.py          # Configuración de Celery
│   │   ├── process_post.py        # Re-renderiza cooked + indexa búsqueda
│   │   └── pull_hotlinked_images.py  # Descarga imágenes externas a local
│   └── main.py                # Aplicación FastAPI + middlewares
├── tests/
│   ├── conftest.py            # Fixtures compartidos (mocks de DB y usuario)
│   ├── test_guardian.py       # Tests de permisos
│   ├── test_markdown.py       # Tests del renderer
│   ├── test_routes_auth.py    # Tests de endpoints de autenticación
│   ├── test_routes_bookmarks.py
│   ├── test_routes_categories.py
│   ├── test_routes_posts.py
│   ├── test_routes_users.py
│   ├── test_schemas.py
│   └── test_security.py       # Tests de validación JWT
├── .env.example               # Plantilla de variables de entorno
├── Dockerfile
├── Makefile
├── pyproject.toml             # Dependencias y configuración de pytest
└── run.py                     # Script de arranque para desarrollo
```

## Workers Celery

Los workers procesan dos tareas en background:

| Tarea | Cuándo se lanza | Qué hace |
|---|---|---|
| `process_post` | Al crear/editar un post | Re-renderiza Markdown → HTML, actualiza el índice full-text (`post_search_data`) |
| `pull_hotlinked_images` | Tras `process_post` si hay imágenes externas | Descarga imágenes externas y las sirve desde el servidor local |

### Iniciar un worker

```bash
# Requiere Redis corriendo en localhost:6379
uv run celery -A app.tasks.celery_app worker --loglevel=info
```

Para desarrollo sin Redis, desactiva Celery:

```env
CELERY_ENABLED=false
```

En este modo los posts se renderizan sincrónicamente en el momento de la creación.

---

## Pruebas unitarias

Los tests **no requieren base de datos real**. Usan un `AsyncMock` de la sesión SQLAlchemy y fixtures de usuarios/posts/topics falsos definidos en `conftest.py`.

```bash
# Ejecutar todos los tests con cobertura
uv run pytest

# Sin reporte de cobertura (más rápido)
uv run pytest --no-cov

# Un módulo específico
uv run pytest tests/test_guardian.py -v

# Un test específico
uv run pytest tests/test_routes_auth.py::test_dev_login_creates_user -v
```

El reporte de cobertura HTML se genera en `htmlcov/index.html`. La cobertura mínima configurada es **75%**.

### Módulos de test

| Archivo | Qué cubre |
|---|---|
| `test_guardian.py` | Reglas de permisos: ver, crear, editar y borrar temas/posts por rol |
| `test_markdown.py` | Renderizado Markdown, menciones `@usuario`, citas `[quote]` |
| `test_security.py` | Creación y validación de tokens JWT dev |
| `test_schemas.py` | Validación de entrada con Pydantic |
| `test_routes_auth.py` | Endpoints `/api/auth/*` |
| `test_routes_categories.py` | Endpoints `/api/categories` |
| `test_routes_posts.py` | Creación, edición, likes y bookmarks |
| `test_routes_users.py` | Perfil, avatar y temas de usuario |
| `test_routes_bookmarks.py` | Listado de bookmarks |

---

## Docker

### Construir y ejecutar

```bash
# Desde la carpeta backend/
docker build -t forum-backend .

docker run -p 8000:8000 \
  --env-file .env \
  forum-backend
```

### Variables de entorno en Docker

Pasar el archivo `.env` con `--env-file` o definir cada variable con `-e`:

```bash
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/discourse" \
  -e AZURE_AD_TENANT_ID="..." \
  -e AZURE_AD_CLIENT_ID="..." \
  -e DEV_JWT_SECRET="$(python -c 'import secrets; print(secrets.token_hex(32))')" \
  forum-backend
```

El Dockerfile usa `uv sync --frozen --no-dev` para instalar solo dependencias de producción.

---