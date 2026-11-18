# Task Manager — Aplicación Full Stack Preparada para CI/CD y AWS

Aplicación web **Task Manager** desarrollada con arquitectura desacoplada (**React + TypeScript + Vite** en el frontend, **FastAPI + SQLAlchemy + Pydantic** en el backend y **PostgreSQL** como base de datos relacional). El proyecto está diseñado bajo estándares de calidad de código, pruebas automatizadas en múltiples niveles (unitarias, integración y aceptación con Selenium), contenedorización con Docker y preparación para pipelines de **CI/CD (GitHub Actions + SonarCloud)** y despliegue en **AWS ECS Fargate + Amazon ECR + Terraform**.

---

## 1. Tecnologías Utilizadas

| Capa / Propósito | Tecnologías |
| :--- | :--- |
| **Frontend** | React 18, TypeScript, Vite, CSS3 Responsive, Nginx (producción) |
| **Pruebas Frontend** | Vitest, React Testing Library, User Event, JSDOM, Coverage V8 (LCOV) |
| **Backend** | Python 3.12, FastAPI, Uvicorn, SQLAlchemy 2.0 (ORM), Pydantic v2 |
| **Base de Datos** | PostgreSQL 16 (`psycopg` v3 binary) |
| **Pruebas Backend e Integración** | Pytest, Pytest-Cov (umbral mínimo obligatorio del **80%**), HTTPX |
| **Pruebas de Aceptación (E2E)** | Selenium WebDriver (Chrome / Edge Headless) |
| **Calidad y Estilo de Código** | Flake8, Pylint, Black, SonarCloud (`sonar-project.properties`) |
| **Infraestructura Local** | Docker, Docker Compose (con `healthcheck` y espera activa de base de datos) |

---

## 2. Arquitectura y Estructura del Proyecto

El frontend y el backend están completamente separados. El frontend se comunica únicamente con el backend a través de solicitudes HTTP REST; el backend valida los datos, aplica la lógica de negocio y gestiona la persistencia en PostgreSQL.

```text
final-CICD/
├── .env.example                  # Plantilla de variables de entorno
├── .flake8                       # Configuración global de Flake8
├── .gitignore                    # Archivos excluidos de control de versiones
├── .pylintrc                     # Configuración global de Pylint
├── docker-compose.yml            # Orquestación local (Frontend + Backend + PostgreSQL)
├── pyproject.toml                # Configuración de Black y Coverage
├── pytest.ini                    # Configuración de Pytest y umbral de cobertura >= 80%
├── README.md                     # Documentación de instalación, ejecución y pruebas
├── requirements.txt              # Referencia de dependencias Python desde la raíz
├── sonar-project.properties      # Configuración de análisis para SonarCloud
├── database/
│   └── init-test-db.sql          # Inicialización automática de la BD de pruebas (taskmanager_test)
├── backend/
│   ├── .dockerignore
│   ├── .flake8
│   ├── .pylintrc
│   ├── Dockerfile                # Imagen Docker del backend (FastAPI + Uvicorn)
│   ├── pyproject.toml
│   ├── pytest.ini
│   ├── requirements.txt          # Dependencias de ejecución, pruebas y calidad del backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py             # Gestión de variables de entorno
│   │   ├── crud.py               # Operaciones CRUD transaccionales sobre SQLAlchemy
│   │   ├── database.py           # Motor SQLAlchemy, sesiones y espera activa de PostgreSQL
│   │   ├── main.py               # Punto de entrada FastAPI, CORS, lifespan y manejo de errores
│   │   ├── models.py             # Modelo ORM Task y enumeración TaskStatus
│   │   ├── schemas.py            # Esquemas y validaciones Pydantic
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── health.py         # Endpoint GET /health
│   │       └── tasks.py          # Endpoints CRUD /api/tasks
│   └── tests/
│       ├── conftest.py           # Fixtures y configuración de BD de pruebas aislada
│       ├── unit/                 # Pruebas unitarias de API, CRUD, validaciones y health
│       ├── integration/          # Pruebas de integración Backend <-> Base de Datos
│       └── acceptance/           # Pruebas E2E automatizadas con Selenium
└── frontend/
    ├── .dockerignore
    ├── Dockerfile                # Construcción multi-stage (Node Build -> Nginx)
    ├── index.html
    ├── nginx.conf                # Servidor Nginx para SPA y endpoint /health
    ├── package.json              # Dependencias y scripts del frontend
    ├── package-lock.json         # Lockfile para reproducibilidad exacta
    ├── tsconfig.json
    ├── vite.config.ts            # Configuración de Vite y Vitest
    └── src/
        ├── App.tsx               # Dashboard principal y gestión de estado
        ├── App.css               # Estilos modernos y diseño responsive
        ├── index.css             # Variables CSS y reset base
        ├── main.tsx              # Punto de montaje React
        ├── types/
        │   └── task.ts           # Tipos e interfaces TypeScript
        ├── services/
        │   └── taskService.ts    # Cliente HTTP para consumir la API REST del backend
        ├── components/
        │   ├── AlertBanner.tsx   # Notificaciones de éxito y error
        │   ├── ConfirmModal.tsx  # Modal de confirmación antes de eliminar tareas
        │   ├── Header.tsx        # Encabezado de la aplicación
        │   ├── TaskCard.tsx      # Tarjeta individual de tarea con indicadores visuales
        │   ├── TaskFilter.tsx    # Filtros por estado (Todas, Pendientes, Completadas)
        │   ├── TaskForm.tsx      # Formulario validado para crear y editar tareas
        │   ├── TaskList.tsx      # Listado de tareas y estados vacío/carga
        │   └── TaskStats.tsx     # Contadores y barra de progreso del dashboard
        └── test/
            ├── setup.ts          # Inicialización de Vitest y Testing Library
            ├── App.test.tsx      # Pruebas de componentes, flujos de usuario y errores
            └── taskService.test.ts # Pruebas unitarias del cliente HTTP
```

---

## 3. Modelo de Datos (PostgreSQL)

Tabla `tasks`:

| Columna | Tipo | Restricciones | Descripción |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY`, `AUTOINCREMENT` | Identificador único de la tarea |
| `title` | `VARCHAR(150)` | `NOT NULL` | Título obligatorio (no vacío) |
| `description` | `TEXT` | `NOT NULL`, `DEFAULT ''` | Descripción detallada de la tarea |
| `status` | `VARCHAR(20)` | `NOT NULL`, `DEFAULT 'Pending'` | Estado: `Pending` o `Completed` |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL` | Fecha y hora de creación (UTC) |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL` | Fecha y hora de última actualización (UTC) |

---

## 4. Documentación de la API REST

Con el backend en ejecución, la documentación interactiva OpenAPI (Swagger UI) está disponible en:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

### Endpoints Implementados

| Método | Ruta | Código Éxito | Descripción |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | `200 OK` | Verifica el estado del backend y la conexión a PostgreSQL (`503` si falla la BD). |
| `GET` | `/api/tasks` | `200 OK` | Obtiene todas las tareas (acepta filtro opcional `?status=Pending` o `?status=Completed`). |
| `GET` | `/api/tasks/{id}` | `200 OK` | Obtiene una tarea específica por su ID (`404` si no existe). |
| `POST` | `/api/tasks` | `201 Created` | Crea una nueva tarea validando que el título no esté vacío (`422` si es inválido). |
| `PUT` | `/api/tasks/{id}` | `200 OK` | Actualiza título, descripción y opcionalmente estado de una tarea (`404` si no existe). |
| `PATCH` | `/api/tasks/{id}/status` | `200 OK` | Cambia el estado de una tarea entre `Pending` y `Completed` (`404` si no existe). |
| `DELETE` | `/api/tasks/{id}` | `200 OK` | Elimina permanentemente una tarea existente (`404` si no existe). |

#### Ejemplo de cuerpo para `POST /api/tasks` y `PUT /api/tasks/{id}`:
```json
{
  "title": "Configurar pipeline CI/CD",
  "description": "Integrar pruebas, SonarCloud y construcción de imágenes Docker"
}
```

#### Ejemplo de cuerpo para `PATCH /api/tasks/{id}/status`:
```json
{
  "status": "Completed"
}
```

---

## 5. Instrucciones de Instalación y Ejecución Local

### Requisitos Previos
- **Docker** y **Docker Compose** (recomendado para levantar todo el entorno con un solo comando).
- **Python 3.11+** y **Node.js 20+** (para ejecutar pruebas y herramientas de calidad localmente).

### Opción A: Ejecución Completa con Docker Compose (Recomendada)

1. **Clonar el repositorio e ingresar al directorio:**
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd final-CICD
   ```

2. **Crear el archivo `.env` a partir de `.env.example`:**
   ```bash
   cp .env.example .env
   ```

3. **Construir y levantar los servicios (PostgreSQL, Backend y Frontend):**
   ```bash
   docker compose up --build -d
   ```

4. **Verificar que los contenedores estén saludables (`healthy`):**
   ```bash
   docker compose ps
   ```

5. **Acceder a la aplicación:**
   - **Frontend (Interfaz Web):** `http://localhost:3000`
   - **Backend (API REST):** `http://localhost:8000/api/tasks`
   - **Health Check:** `http://localhost:8000/health`
   - **Swagger Docs:** `http://localhost:8000/docs`

6. **Detener los servicios:**
   ```bash
   docker compose down
   ```

---

### Opción B: Instalación de Dependencias en Entorno Local

1. **Backend (Python):**
   ```bash
   python -m venv .venv
   # En Windows (PowerShell):
   .\.venv\Scripts\Activate.ps1
   # En Linux / macOS:
   # source .venv/bin/activate

   pip install -r requirements.txt
   ```

2. **Frontend (Node.js):**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---

## 6. Ejecución de Pruebas Automatizadas y Calidad de Código

### 6.1. Análisis Estático y Formato del Backend (Black, Flake8, Pylint)

Desde la carpeta `backend/` (o desde la raíz del proyecto):

```bash
cd backend

# 1. Verificar formato de código con Black
black --check app tests

# 2. Analizar estilo y calidad con Flake8
flake8 app tests

# 3. Ejecutar análisis estático con Pylint
pylint app tests
```

### 6.2. Pruebas Unitarias y de Integración del Backend (con Pytest-Cov >= 80%)

Las pruebas utilizan automáticamente una base de datos de pruebas independiente (`taskmanager_test` cuando PostgreSQL está activo o una base de datos aislada en memoria si se ejecuta sin Docker), garantizando que los datos de desarrollo nunca sean modificados ni eliminados.

```bash
cd backend

# Ejecutar pruebas unitarias y de integración verificando cobertura mínima del 80%
pytest

# Ejecutar únicamente pruebas unitarias
pytest tests/unit

# Ejecutar únicamente pruebas de integración con la base de datos
pytest tests/integration
```

> Si la cobertura del paquete `app` es inferior al **80%**, el comando `pytest` fallará automáticamente gracias a `--cov-fail-under=80` configurado en `pytest.ini`.

### 6.3. Pruebas Automatizadas del Frontend (Vitest + React Testing Library)

```bash
cd frontend

# Ejecutar pruebas de componentes y servicios
npm test

# Ejecutar pruebas generando reporte de cobertura (LCOV para SonarCloud)
npm run test:coverage

# Verificar tipado estático de TypeScript y compilación de producción
npm run typecheck
npm run build
```

### 6.4. Pruebas de Aceptación End-to-End con Selenium

Con la aplicación levantada mediante `docker compose up -d` (Frontend en `http://localhost:3000` y Backend en `http://localhost:8000`):

```bash
cd backend
pytest tests/acceptance
```

Esta suite abre un navegador headless con Selenium y valida de principio a fin:
1. Carga correcta de la aplicación y contadores del dashboard.
2. Creación de una tarea desde el formulario.
3. Visualización de la tarjeta y verificación en PostgreSQL vía API.
4. Edición del título y descripción de la tarea.
5. Cambio de estado entre `Pending` y `Completed`.
6. Filtrado de tareas por `Pendientes`, `Completadas` y `Todas`.
7. Eliminación de la tarea confirmando en el modal y comprobando código `404` en el backend.

---

## 7. Preparación para SonarCloud y CI/CD

El archivo `sonar-project.properties` en la raíz del proyecto está configurado para integrar **SonarCloud** en el pipeline de GitHub Actions, consumiendo:
- Código fuente de `backend/app` y `frontend/src`.
- Reporte XML de cobertura del backend (`backend/coverage.xml`).
- Reporte LCOV de cobertura del frontend (`frontend/coverage/lcov.info`).
- Reportes de análisis estático de Flake8 y Pylint (`flake8-report.txt`, `pylint-report.txt`).
