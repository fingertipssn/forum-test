# Forum Frontend

SPA del foro interno construida con **Angular 20** (standalone components). Se autentica contra **Azure Active Directory / Entra ID** usando MSAL, o contra un backend local con tokens JWT en modo desarrollo.

---

## Tabla de contenidos

- [Tecnologías](#tecnologías)
- [Requisitos previos](#requisitos-previos)
- [Instalación](#instalación)
- [Variables de entorno](#variables-de-entorno)
- [Ejecución en local](#ejecución-en-local)
- [Build de producción](#build-de-producción)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Rutas de la aplicación](#rutas-de-la-aplicación)
- [Autenticación](#autenticación)
- [Pruebas unitarias](#pruebas-unitarias)
- [Seguridad](#seguridad)

---

## Tecnologías

| Paquete | Versión | Rol |
|---|---|---|
| **Angular** | 20.x | Framework de UI (standalone components, signals) |
| **@azure/msal-angular** | 3.x | Integración MSAL para Angular |
| **@azure/msal-browser** | 3.x | Flujo OAuth2/OIDC en el navegador |
| **marked** | 18.x | Parser de Markdown en el cliente |
| **DOMPurify** | 3.x | Sanitización HTML (anti-XSS) |
| **RxJS** | 7.8 | Programación reactiva |
| **TypeScript** | 5.8 | Tipado estático |
| **Karma + Jasmine** | — | Framework de pruebas unitarias |

---

## Requisitos previos

- **Node.js ≥ 20** (se recomienda la versión LTS más reciente)
- **npm ≥ 10**
- **Angular CLI** (opcional, ya incluido en `devDependencies`):
  ```bash
  npm install -g @angular/cli
  ```

---

## Instalación

```bash
# Desde la raíz del repositorio
cd frontend

npm install
```

---

## Variables de entorno

La configuración se gestiona a través de los archivos en `src/environments/`:

| Archivo | Cuándo se usa |
|---|---|
| `environment.ts` | Desarrollo local (`ng serve`) |
| `environment.prod.ts` | Build de producción (`ng build`) |

### Parámetros configurables

| Campo | Descripción |
|---|---|
| `production` | `true` en el build de producción |
| `devMode` | `true` activa el login local con JWT (sin Azure AD) |
| `apiUrl` | URL base del backend (`http://localhost:8000/api` en local, `/api` en producción) |
| `msalConfig.auth.clientId` | Client ID de la app registrada en Azure AD |
| `msalConfig.auth.authority` | `https://login.microsoftonline.com/{tenantId}` |
| `msalConfig.auth.redirectUri` | URI de callback registrada en Azure AD |
| `msalConfig.auth.postLogoutRedirectUri` | URI de redirección tras logout |
| `apiScopes` | Scopes solicitados al token de acceso |

> **Antes del primer deploy a producción:** actualiza `redirectUri` y `postLogoutRedirectUri` en `environment.prod.ts` con el dominio real y regístralos en Azure AD Portal → App registrations → Authentication → Redirect URIs.

---

## Ejecución en local

```bash
# Servidor de desarrollo con hot-reload
npm start
# o
npx ng serve
```

La aplicación queda disponible en **`http://localhost:4200`**.

### Modo desarrollo sin Azure AD (`devMode: true`)

Cuando `devMode: true` en `environment.ts`, la pantalla de login muestra un formulario simple (usuario, email, nombre). El backend crea o recupera el usuario y devuelve un token JWT local. No se requiere ninguna cuenta de Azure AD.

Para activarlo, edita `src/environments/environment.ts`:

```typescript
export const environment = {
  production: false,
  devMode: true,   // <-- activar
  apiUrl: 'http://localhost:8000/api',
  // ...
};
```

---

## Build de producción

```bash
npm run build
```

Los artefactos se generan en `dist/discourse-forum-frontend/browser/`. Sirve esa carpeta con cualquier servidor estático (nginx, Azure Static Web Apps, etc.).

```bash
# Vista previa del build de producción
npm run build && npx http-server dist/discourse-forum-frontend/browser -p 4200
```

---

## Estructura del proyecto

```
frontend/src/
├── app/
│   ├── app.component.ts          # Componente raíz
│   ├── app.config.ts             # Configuración de la app (providers globales)
│   ├── app.routes.ts             # Definición de rutas (lazy loading)
│   │
│   ├── core/
│   │   ├── auth/
│   │   │   ├── auth.guard.ts             # Guard de rutas protegidas
│   │   │   ├── auth.service.ts           # Estado de autenticación (signals)
│   │   │   ├── azure-auth.interceptor.ts # Adjunta token Azure AD a peticiones HTTP
│   │   │   ├── dev-auth.interceptor.ts   # Adjunta token dev desde localStorage
│   │   │   └── msal.config.ts            # Factory de MSAL (instancia, guard, providers)
│   │   ├── models/
│   │   │   └── index.ts                  # Interfaces TypeScript (User, Topic, Post, etc.)
│   │   └── services/
│   │       ├── api.service.ts            # Cliente HTTP base
│   │       ├── category.service.ts       # Categorías
│   │       ├── post.service.ts           # Posts (crear, editar, like, bookmark)
│   │       ├── search.service.ts         # Búsqueda full-text
│   │       ├── topic.service.ts          # Temas
│   │       └── upload.service.ts         # Subida de imágenes
│   │
│   ├── features/                         # Vistas de la aplicación
│   │   ├── admin-categories/             # Gestión de categorías (staff)
│   │   ├── auth-callback/                # Procesamiento del redirect de Azure AD
│   │   ├── bookmarks/                    # Listado de bookmarks
│   │   ├── category-list/                # Página de inicio (lista de categorías)
│   │   ├── composer/                     # Editor de posts/temas (modal)
│   │   ├── login/                        # Pantalla de login
│   │   ├── navigation/                   # Barra de navegación superior
│   │   ├── search/                       # Resultados de búsqueda
│   │   ├── sidebar/                      # Barra lateral
│   │   ├── topic-detail/                 # Vista de un tema con sus posts
│   │   ├── topic-list/                   # Lista de temas (latest / por categoría)
│   │   └── user-profile/                 # Perfil de usuario
│   │
│   └── shared/
│       └── pipes/
│           ├── markdown.pipe.ts          # Markdown → HTML sanitizado (DOMPurify)
│           └── time-ago.pipe.ts          # Fechas relativas ("hace 5 min")
│
└── environments/
    ├── environment.ts                    # Config de desarrollo
    └── environment.prod.ts               # Config de producción
```

---

## Rutas de la aplicación

| Ruta | Componente | Guard | Descripción |
|---|---|---|---|
| `/` | `CategoryListComponent` | — | Página de inicio: lista de categorías |
| `/login` | `LoginComponent` | — | Pantalla de acceso |
| `/latest` | `TopicListComponent` | — | Todos los temas, orden cronológico |
| `/c/:slug` | `TopicListComponent` | — | Temas de una categoría |
| `/t/:id` | `TopicDetailComponent` | — | Detalle de un tema con posts |
| `/search` | `SearchResultsComponent` | — | Resultados de búsqueda |
| `/u/:username` | `UserProfileComponent` | — | Perfil público de un usuario |
| `/bookmarks` | `BookmarksComponent` | — | Bookmarks del usuario autenticado |
| `/admin/categories` | `AdminCategoriesComponent` | — | Administración de categorías |
| `/auth/finish` | `AuthCallbackComponent` | — | Callback de Azure AD (procesa auth code) |

Las rutas se cargan con **lazy loading**: cada feature module se divide en su propio chunk de JavaScript.

---

## Autenticación

El frontend soporta dos modos de autenticación configurables por entorno:

### Modo producción: Azure AD / Entra ID

```
Usuario → loginRedirect() → Azure AD → redirect a /auth/finish
         → MSAL procesa auth code → token de acceso
         → AzureAuthInterceptor adjunta Bearer token a cada petición HTTP
         → Backend valida RS256 con JWKS públicos de Azure
```

1. `msalInstanceFactory()` configura la instancia de MSAL con el `clientId` y `authority`.
2. `AzureAuthInterceptor` adquiere silenciosamente el token antes de cada petición al backend.
3. `AuthCallbackComponent` en `/auth/finish` procesa el resultado del redirect.
4. `AuthService` expone signals reactivos: `currentUser`, `isAuthenticated`, `isStaff`.

### Modo desarrollo: JWT local (`devMode: true`)

```
Usuario → formulario de login → POST /api/auth/dev-login
        → Backend devuelve token HS256
        → DevAuthInterceptor adjunta el token desde sessionStorage
```

El token se almacena bajo la clave `discourse_dev_token` en `sessionStorage`.

### Guards

`authGuard` redirige a `/login` si `isAuthenticated()` es `false`. Se puede aplicar a rutas que requieren sesión activa.

---

## Pruebas unitarias

```bash
# Ejecutar los tests una sola vez
npm test -- --watch=false

# Modo watch (re-ejecuta al guardar cambios)
npm test

# Con reporte de cobertura
npm test -- --watch=false --code-coverage
```

El reporte de cobertura se genera en `coverage/discourse-forum-frontend/`.

### Módulos con tests

| Archivo | Qué cubre |
|---|---|
| `auth.service.spec.ts` | Inicialización, login, logout y carga de usuario |
| `api.service.spec.ts` | Métodos HTTP del servicio base |
| `category.service.spec.ts` | Peticiones de categorías |
| `post.service.spec.ts` | Creación, edición, like y bookmark de posts |
| `topic.service.spec.ts` | Obtención de temas y detalles |
| `topic-detail.component.spec.ts` | Renderizado del componente de detalle |
| `bookmarks.component.spec.ts` | Renderizado del listado de bookmarks |
| `category-list.component.spec.ts` | Renderizado de la lista de categorías |
| `user-profile.component.spec.ts` | Renderizado del perfil |
| `dev-auth.interceptor.spec.ts` | Adjuntar token dev en requests |
| `time-ago.pipe.spec.ts` | Formato de fechas relativas |