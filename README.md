# 🎓 TutorIA — Tutoría universitaria asistida por IA

TutorIA es una aplicación full-stack para la **Escuela Profesional de Ingeniería
Informática y de Sistemas de la UNSAAC**. Los estudiantes consultan a un chatbot
que responde **citando la normativa oficial de la universidad** (reglamentos,
estatuto, planes de estudio) y gestionan sus tutorías; los docentes-tutores
administran sus sesiones y estudiantes asignados.

- **Backend:** FastAPI + PostgreSQL con `pgvector`, en arquitectura hexagonal.
- **Frontend:** React Native con Expo (SDK 54).
- **IA:** Google Gemini, con un sistema RAG que **se abstiene de responder**
  cuando no encuentra respaldo documental, en vez de inventar.

Esta guía alcanza para levantar el proyecto desde cero sin conocerlo.

---

## 📋 Índice

1. [Qué necesitas instalado](#-qué-necesitas-instalado)
2. [Puesta en marcha con Docker](#-puesta-en-marcha-con-docker-recomendado)
3. [Puesta en marcha sin Docker](#-puesta-en-marcha-sin-docker)
4. [Levantar la app móvil](#-levantar-la-app-móvil)
5. [Ejecutar las pruebas](#-ejecutar-las-pruebas)
6. [El corpus y el índice del RAG](#-el-corpus-y-el-índice-del-rag)
7. [Estructura del proyecto](#-estructura-del-proyecto)
8. [Tareas frecuentes](#-tareas-frecuentes)
9. [Problemas frecuentes](#-problemas-frecuentes)
10. [Estado del proyecto](#-estado-del-proyecto)
11. [Reconstrucción del sistema RAG](#-reconstrucción-del-sistema-rag)
12. [Documentación técnica](#-documentación-técnica)

---

## 🧰 Qué necesitas instalado

| Herramienta | Para qué | Obligatorio |
|---|---|---|
| **Git** | Clonar el repositorio | Sí |
| **Docker + Docker Compose** | Levantar base de datos y API sin instalar nada más | Recomendado |
| **Node.js 18+ y npm** | Compilar y servir la app móvil | Sí |
| **Python 3.12+** | Correr el backend o las pruebas fuera de Docker | Solo sin Docker |
| **Expo Go** (celular) o Android Studio / Xcode | Abrir la app | Sí, alguno |

También necesitas una **clave de API de Google AI Studio**, gratuita, en
[aistudio.google.com](https://aistudio.google.com). Sin ella el proyecto arranca
igual, pero el chatbot no responde y el índice del RAG queda vacío.

---

## 🐳 Puesta en marcha con Docker (recomendado)

### 1. Clonar el repositorio

```bash
git clone https://github.com/Tomioka1809/Tutoria-IA.git
cd Tutoria-IA
```

### 2. Crear el archivo `.env`

```bash
cp .env.example .env
```

Abre el `.env` y completa al menos `GEMINI_API_KEY`. Estas son todas las
variables:

| Variable | Para qué sirve | Valor sugerido para desarrollo |
|---|---|---|
| `APP_ENV` | Entorno: `development`, `test` o `production` | `development` |
| `DB_USER` / `DB_PASSWORD` / `DB_NAME` | Credenciales de PostgreSQL | `postgres` / `postgres` / `tutoria_db` |
| `DB_HOST` | `db` con Docker Compose, `localhost` sin Docker | `db` |
| `DB_PORT` | Puerto de PostgreSQL en el host | `5433` |
| `SECRET_KEY` | Firma de los tokens JWT | cualquier cadena larga |
| `ALGORITHM` | Algoritmo del JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Duración de la sesión | `60` |
| `CORS_ALLOWED_ORIGINS` | Orígenes permitidos, separados por coma | vacío |
| `GEMINI_API_KEY` | **Tu clave de Google AI Studio** | *(obligatoria)* |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` / `ADMIN_NAME` | Admin que se crea solo en el primer arranque | los que quieras |
| `AUTO_BOOTSTRAP` | `0` desactiva toda la siembra automática | `1` |
| `AUTO_SEED_CORPUS` | `0` evita generar embeddings al arrancar | `1` |

> [!IMPORTANT]
> `CORS_ALLOWED_ORIGINS` puede quedar vacío en `development` y `test`: se
> permite cualquier origen, porque Expo usa IP de LAN que cambian. En
> `production` es **obligatorio** y no se acepta `*`; el backend no arranca sin
> al menos un origen explícito.

> [!TIP]
> Si tu cuota de Gemini es ajustada, pon `AUTO_SEED_CORPUS=0`. El backend
> levanta igual y luego generas el índice cuando quieras
> ([ver más abajo](#-el-corpus-y-el-índice-del-rag)).

### 3. Levantar los servicios

```bash
docker compose up -d
```

Esto arranca dos contenedores:

| Contenedor | Qué es | Puerto en tu máquina |
|---|---|---|
| `tutoria_db` | PostgreSQL 16 con la extensión `pgvector` | `5433` |
| `tutoria_backend` | La API FastAPI | `8000` |

### 4. Qué pasa solo en el primer arranque

No hace falta correr migraciones a mano. El
[entrypoint](backend/docker-entrypoint.sh) hace, en este orden:

1. **Aplica las migraciones** (`alembic upgrade head`) en cada arranque.
2. **Crea el usuario admin**, solo si todavía no existe ninguno con rol `admin`
   y definiste `ADMIN_EMAIL` y `ADMIN_PASSWORD`.
3. **Carga el roster** de tutores y estudiantes, solo si la base no tiene
   ninguno.
4. **Actualiza el índice del RAG** desde `backend/corpus/estructurado/`. La
   ingesta es **incremental**: compara hashes y solo genera los embeddings que
   faltan, así que reiniciar es barato. Si la cuota de Gemini se agota a mitad
   de camino, el arranque continúa y la próxima corrida sigue donde quedó.

Cada paso se salta si ya está hecho: ningún reinicio destruye datos existentes.

Puedes seguir el proceso con:

```bash
docker compose logs -f backend
```

La primera ingesta completa tarda varios minutos: son ~1370 fragmentos y cada
uno necesita una llamada de embedding.

### 5. Comprobar que funciona

```bash
curl http://localhost:8000/docs
```

O abre [http://localhost:8000/docs](http://localhost:8000/docs) en el navegador:
es la documentación interactiva de la API.

Si no definiste `ADMIN_EMAIL` / `ADMIN_PASSWORD` en el `.env`, crea el admin a
mano:

```bash
docker compose exec backend python -m app.create_superuser
```

---

## 🐍 Puesta en marcha sin Docker

Solo si prefieres correr el backend nativo. Necesitas un PostgreSQL con
`pgvector` disponible por tu cuenta.

```bash
# 1. Base de datos: lo más simple es usar solo el contenedor de PostgreSQL
docker compose up -d db

# 2. Ajusta el .env para salir del contenedor
#    DB_HOST=localhost
#    DB_PORT=5433

# 3. Entorno virtual e instalación
cd backend
python -m venv venv
source venv/bin/activate          # Windows PowerShell: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 4. Migraciones
alembic upgrade head

# 5. Datos iniciales (admin, roster e índice del RAG)
python -m app.bootstrap_data

# 6. Servidor de desarrollo
uvicorn app.main:app --reload
```

> [!NOTE]
> `requirements.txt` trae solo lo necesario para servir la API. Para correr las
> pruebas o generar los gráficos de evaluación instala además
> `pip install -r requirements-dev.txt` (pytest y matplotlib).

---

## 📱 Levantar la app móvil

En otra terminal, desde la raíz del proyecto:

```bash
cd frontend
npm install
npm run start
```

Después:

| Cómo probar | Qué hacer | Requiere |
|---|---|---|
| **Celular real** (recomendado) | Escanea el QR con la app **Expo Go** | Mismo Wi-Fi que tu PC |
| **Emulador Android** | Presiona `a` en la terminal | Android Studio con un AVD corriendo |
| **Simulador iOS** | Presiona `i` | macOS con Xcode |
| **Navegador** | Presiona `w` | Nada, pero el soporte web es parcial |

> [!TIP]
> **No hace falta configurar ninguna URL.** El cliente HTTP
> ([`frontend/src/api/client.ts`](frontend/src/api/client.ts)) detecta sola la
> IP de tu máquina en la red local, para que el celular encuentre al backend.

---

## 🧪 Ejecutar las pruebas

### Backend — 505 pruebas unitarias

Desde la **raíz del repositorio** (no desde `backend/`): el
[`conftest.py`](conftest.py) de la raíz es el que pone `backend/` en el
`sys.path`, y [`pytest.ini`](pytest.ini) apunta a `backend/tests`.

```bash
# con el venv del backend activado, o:
backend/venv/bin/python -m pytest
```

Son unitarias: **no necesitan base de datos ni clave de Gemini**, y tardan unos
5 segundos. Viven en `backend/tests/unit/`.

Otros comandos útiles:

```bash
python -m pytest -q                                    # salida compacta
python -m pytest backend/tests/unit/test_chat_use_cases.py   # un archivo
python -m pytest -k "corpus"                           # por nombre
```

### Backend — verificador por fases

Audita el repositorio completo (estructura, configuración, secretos, pipeline
RAG, frontend, integración) sin modificar nada:

```bash
python backend/tests/verificar_tutoria.py --fase todas
```

Lee la raíz desde el directorio actual, así que **córrelo desde la raíz** o pasa
`--root /ruta/al/proyecto`. Con `--integracion` agrega las comprobaciones que
requieren los servicios levantados. El reporte queda en
`backend/tests/reporte_verificacion.json`.

### Frontend

```bash
cd frontend
npx tsc --noEmit     # tipos
npm run lint         # ESLint vía Expo
npm run verify:api        # capa de API
npm run verify:errors     # capa de errores
npm run verify:calendar   # capa de calendario
npm run verify:data       # datos reales y paridad ES/EN
npm run verify:quality    # calidad estática
```

---

## 📚 El corpus y el índice del RAG

El chatbot no responde de memoria: recupera fragmentos de la normativa de la
UNSAAC desde la tabla `corpus_chunks` de PostgreSQL y responde citando la
fuente. Ese índice se construye desde archivos JSON versionados en el
repositorio, **no desde los PDF directamente**.

### Las tres carpetas de `backend/corpus/`

Son **dos entradas y una salida** de un mismo pipeline:

```
corpus/heredado/   ──> scripts.convert_corpus  ─┐
   9 JSON                                       ├──> corpus/estructurado/ ──> scripts.ingest_corpus ──> pgvector
corpus/fuentes/    ──> scripts.extract_*       ─┘        20 JSON
   4 JSON
```

| Carpeta | Qué contiene | Quién la lee |
|---|---|---|
| `corpus/heredado/` | Los 9 JSON originales, en el formato viejo, previos a la reconstrucción | Solo `scripts.convert_corpus` |
| `corpus/fuentes/` | 4 JSON transcritos a mano de fuentes que **no** son PDF: la imagen de la malla 2017, el catálogo del Centro de Cómputo, el portal de la escuela y el índice de becas | Los `scripts.extract_*` |
| `corpus/estructurado/` | Los 20 JSON finales, ya con articulado y procedencia citable | `scripts.ingest_corpus` — **es lo único que se indexa** |

Los PDF oficiales no están versionados (pesan demasiado); sí lo están las
transcripciones y el resultado, para que el índice se pueda reconstruir sin
volver a las fuentes originales.

### Comandos

Todos se corren desde `backend/`, con el entorno virtual activo:

```bash
# Validar el corpus estructurado (no toca la base de datos)
python -m scripts.validate_corpus

# Auditar cobertura documental: ¿el texto necesario existe?
python -m scripts.audit_corpus_coverage --corpus corpus/estructurado

# Regenerar el corpus estructurado a partir del heredado (previsualización)
python -m scripts.convert_corpus --dry-run

# Indexar: genera los embeddings que falten y los guarda en pgvector
python -m scripts.ingest_corpus
```

El detalle del pipeline, cómo agregar un documento nuevo y cómo se calibraron
los parámetros está en
[`documentacion/07_rag_operacion.md`](documentacion/07_rag_operacion.md).

---

## 📁 Estructura del proyecto

```text
Tutoria-IA/
├── .env.example                 # Plantilla de variables de entorno
├── docker-compose.yml           # PostgreSQL (pgvector) + API FastAPI
├── conftest.py                  # Pone backend/ en sys.path para las pruebas
├── pytest.ini                   # testpaths = backend/tests
├── README.md                    # Esta guía
│
├── backend/
│   ├── Dockerfile
│   ├── docker-entrypoint.sh     # Migraciones + siembra idempotente al arrancar
│   ├── requirements.txt         # Dependencias para servir la API
│   ├── requirements-dev.txt     # pytest y matplotlib
│   ├── alembic/                 # Migraciones de base de datos
│   │
│   ├── app/                     # Arquitectura hexagonal
│   │   ├── main.py              # Punto de entrada ASGI
│   │   ├── bootstrap_data.py    # Siembra idempotente (admin, roster, índice RAG)
│   │   ├── create_superuser.py  # Crear un admin a mano
│   │   ├── domain/              # Entidades y excepciones, sin dependencias externas
│   │   ├── application/         # Casos de uso, DTOs y puertos (interfaces)
│   │   └── infrastructure/      # Adaptadores concretos
│   │       ├── adapters/        #   Google Gemini
│   │       ├── api/v1/endpoints/#   Routers FastAPI
│   │       ├── config/          #   pydantic-settings
│   │       ├── database/        #   SQLAlchemy async, repositorios, pgvector
│   │       └── security/        #   Hash de contraseñas y JWT
│   │
│   ├── corpus/                  # Material documental del RAG
│   │   ├── heredado/            #   9 JSON en el formato original (entrada)
│   │   ├── fuentes/             #   4 JSON transcritos a mano (entrada)
│   │   └── estructurado/        #   20 JSON: lo único que se indexa (salida)
│   │
│   ├── scripts/                 # Extracción, conversión, ingesta y calibración
│   │
│   └── tests/
│       ├── unit/                # 505 pruebas unitarias
│       ├── dataset/             # Golden sets de evaluación (v1 congelado, v2 activo)
│       ├── resultados/          # Informes JSON/CSV y gráficos de la evaluación
│       ├── run_eval_v2.py       # Runner de evaluación contra el golden set
│       └── verificar_tutoria.py # Auditoría por fases del repositorio
│
├── frontend/
│   ├── app/                     # Rutas de Expo Router
│   │   ├── auth/                #   Login, registro, recuperación
│   │   ├── (estudiante)/        #   Pantallas del rol estudiante
│   │   ├── (tutor)/             #   Pantallas del rol docente-tutor
│   │   └── (admin)/             #   Pantallas del rol administrador
│   ├── src/
│   │   ├── api/                 # Cliente Axios con autodetección de IP
│   │   ├── components/          # Componentes de interfaz
│   │   ├── store/               # Estado global con Zustand
│   │   ├── i18n/                # Español e inglés
│   │   └── theme/               # Colores y modo oscuro
│   ├── scripts/                 # Verificaciones estáticas (verify:*)
│   └── package.json
│
└── documentacion/               # Documentación técnica por fases
```

---

## 🔧 Tareas frecuentes

**Agregar una dependencia de Python**

```bash
# añádela a backend/requirements.txt y luego
docker compose build backend && docker compose up -d
```

**Cambiar un modelo de base de datos**

```bash
docker compose exec backend alembic revision --autogenerate -m "descripción"
docker compose exec backend alembic upgrade head
```

**Resetear la base de datos por completo**

```bash
docker compose down -v      # -v borra el volumen: se pierden todos los datos
docker compose up -d        # el entrypoint migra y vuelve a sembrar
```

> [!WARNING]
> `down -v` borra también el índice del RAG, y reconstruirlo vuelve a consumir
> cuota de Gemini (~1370 embeddings).

**Ver los logs**

```bash
docker compose logs -f backend
docker compose logs -f db
```

---

## 🚑 Problemas frecuentes

| Síntoma | Causa probable | Solución |
|---|---|---|
| El celular no conecta con el backend | El celular y la PC están en redes distintas | Ponlos en el mismo Wi-Fi; revisa que el firewall no bloquee el puerto 8000 |
| `port 5433 already in use` | Ya tienes un PostgreSQL ocupando ese puerto | Cambia el mapeo en `docker-compose.yml` y `DB_PORT` en el `.env` |
| El chat responde "no tengo información suficiente" a todo | El índice del RAG está vacío | Revisa `GEMINI_API_KEY`; corre `python -m scripts.ingest_corpus` |
| `[bootstrap] Falta GEMINI_API_KEY` en los logs | El `.env` no tiene la clave | Complétala y reinicia con `docker compose up -d` |
| La ingesta se corta a mitad | Se agotó la cuota diaria de Gemini | No pasa nada: es reanudable, vuelve a correrla más tarde |
| `ModuleNotFoundError: app` al correr pytest | Estás ejecutando desde `backend/` | Córrelo desde la raíz del repositorio |
| El backend no arranca en `production` | `SECRET_KEY` débil, `DB_PASSWORD` por defecto o falta `CORS_ALLOWED_ORIGINS` | Es a propósito; corrígelos en el `.env` |

---

## 📌 Estado del proyecto

- **Fase 5 (Benchmark RAG y análisis cuantitativo):** cerrada
- **Fase 6A (Auditoría integral y seguridad):** completada
- **Fase 6B (Migración a Pydantic V2 y seguridad por entorno):** completada
- **Fase 6C (Cierre documental):** completada
- **Reconstrucción del RAG (Fases 0 a 4):** completada
- **Suite de pruebas:** **505 aprobadas, 0 fallidas**

### 🔒 Entornos y seguridad de configuración

- `APP_ENV` admite `development`, `test` y `production`.
- En `production` se bloquean automáticamente las `SECRET_KEY` inseguras: menos
  de 32 caracteres, la clave de desarrollo por defecto o placeholders
  documentales.
- En `production` se bloquean también las contraseñas de base de datos por
  defecto o inseguras.
- En `development` y `test` se conservan los valores por defecto, para no
  estorbar el desarrollo local ni las pruebas.

---

## 🔍 Reconstrucción del sistema RAG

El corpus documental y el motor de recuperación se rehicieron por completo tras
una auditoría que midió su precisión real.

### El punto de partida

La evaluación publicada reportaba precisión global 0.33, pero ese número incluía
los casos fuera de alcance, que puntúan 1.0 de forma trivial porque no hay nada
que recuperar. **Sobre las consultas dentro de alcance, la precisión real era 2
de 12.**

La causa de fondo no estaba en la búsqueda sino en los datos: el corpus era una
**paráfrasis temática** de los documentos oficiales y había perdido el
articulado. El golden set pedía citas como `"Art. 15 - Reglamento de Tutoría"`,
pero **no existía un solo número de artículo en los nueve archivos**, así que esa
métrica era imposible de satisfacer por construcción. Algunos artículos citados
(18, 22, 23, 25, 30) ni siquiera existen: el reglamento llega hasta el 16.

### Qué se hizo

| Fase | Trabajo |
|---|---|
| **0** | Auditoría de cobertura documental. Mide si el texto necesario **existe**, sin llamar a Gemini. Definió el techo alcanzable: **8.3%** |
| **1** | Esquema único de corpus. El fragmento pasa a ser la unidad de recuperación, con procedencia citable y jerarquía como encabezado |
| **2** | Extracción del articulado real desde los PDF oficiales, más tablas (planes de estudio) y OCR en español (calendario escaneado) |
| **3** | Ingesta incremental, embeddings asimétricos, búsqueda híbrida con RRF y umbral calibrado |
| **4** | Reordenamiento por autoridad de la fuente, calibrado con barrido |

### Resultado

| Métrica | Antes | Después |
|---|---|---|
| Cobertura documental (techo) | 8.3% | **96.9%** (31/32 casos en alcance) |
| Acierto de artículo | imposible de medir | **16/19 (84%)** |
| Acierto de documento | — | **32/32 (100%)** |
| Abstención fuera de alcance | rota (0/3) | **3/3** |
| Fragmentos citables | 0 | **1369** |
| Artículos indexados | 0 | **732** |
| Pruebas automatizadas | 277 | **505** |

Las métricas de recuperación (MRR 0.815, nDCG@6 0.775, Recall@6 0.875) y los
ocho gráficos de la evaluación se explican en
[`documentacion/08_metricas_evaluacion.md`](documentacion/08_metricas_evaluacion.md).

### Cierre del corpus (2026-08-06)

Se incorporaron los reglamentos que faltaban y que el propio proyecto tenía
anotados como brecha documental:

| Documento | Norma | Qué cierra |
|---|---|---|
| Reglamento del Programa de Movilidad Académica | CU-349-2026 | Reemplaza al `reglamento_intercambio_estudiantil`, que era una paráfrasis sin resolución ni articulado |
| Reglamento de Subvenciones Económicas | CU-667-2025 | El apoyo económico a intercambios y congresos pasa a ser citable |
| Reglamento para Uso de Vivienda Estudiantil | CU-372-2020 | Única de las cinco unidades de bienestar con reglamento propio publicado |
| ROF 2024 | AU-008-2024 | Reemplaza al ROF 2019. Las cinco unidades de bienestar quedan citables (Art. 104-115) |

Los dos primeros son escaneos sin capa de texto: se procesan con OCR en español
y el extractor lee el Markdown resultante.

### Consultas sobre la carrera y los apoyos (2026-08-06)

Siete preguntas frecuentes no tenían respuesta o la tenían mal. Todas se
verificaron contra la fuente oficial antes de incorporarlas.

| Pregunta | Qué pasaba | Qué se incorporó |
|---|---|---|
| Malla 2017 | Quince casilleros decían solo `ASIGNATURA DE ESPECIALIDAD`, sin nombre ni código | `plan_estudios_2017`, desde el catálogo del Centro de Cómputo: 37 asignaturas de especialidad, las extracurriculares (IF060-IF066) y la práctica preprofesional (IF020) |
| Qué becas existen | Una FAQ sin fuente decía que Bienestar "promueve y tramita becas", sin nombrar ninguna | `becas_y_comedor` (índice con la norma citada en cada entrada) y `reglamento_idiomas` (CU-281-2020), única norma publicada que articula becas de estudio |
| Misión y visión de la carrera | El corpus solo tenía la misión de la universidad | `escuela_informatica`, texto literal del portal de la escuela |
| Autoridades de Informática | No estaban | Decano, Director del Departamento Académico y Directora de la Escuela, con correo |
| Círculos de estudio y eventos | No estaban | ACM-UNSAAC Student Chapter (Res. D-2161-2025-FIEEIM) y los eventos habituales: CUSCONTEST, NEUROKUP, seminarios y charlas |
| Aniversario de la carrera | No estaba | Se celebra en diciembre; creación 13.12.1971 (CG-110-71) y reapertura 22.01.1993 (CU-009-93) |
| Cómo obtener el comedor | La respuesta se quedaba en "hay una evaluación socioeconómica" | El procedimiento de reserva de cupo, desde el manual oficial de Bienestar |

Tres hallazgos que valen más que el contenido agregado:

- **La imagen de la malla 2017 y el catálogo de matrícula discrepan en cinco
  códigos** (`ME351/IF351`, `FI370/IF370`, `EL371/LI371`, `ME356/ME359`,
  `DE901/DR901`). Responder con el de la imagen le daba al estudiante una clave
  con la que no puede matricularse. Ahora el fragmento entrega los dos y dice
  cuál vale.
- **La paráfrasis sin fuente le ganaba al articulado.** Medido: ante *"¿qué
  servicios de apoyo ofrece la universidad?"*, cuatro de los seis fragmentos
  entregados salían de `servicios_bienestar`, que no tiene fuente verificable, y
  el artículo del Estatuto que responde quedaba fuera. Se retiraron los ocho
  fragmentos de ese archivo que ya son citables desde el ROF o el Estatuto; se
  conservó lo que no está en la norma.
- **El chat reescribe la consulta de malla** anteponiéndole `malla curricular
  Plan <año>`. Solo las FAQ del plan 2025 estaban redactadas con esa forma, así
  que *"qué cursos llevo en el sexto ciclo de la malla 2017"* devolvía seis
  fragmentos del 2025 y ninguno del 2017, y el sistema se abstenía. Los
  fragmentos del 2017 abren ahora con esa misma forma.

Se corrigió también que `malla_2017.json` no se podía regenerar: su
transcripción vivía fuera del repositorio. Ahora está en `corpus/fuentes/` y
`validate_malla` la comprueba contra los totales que declara la propia imagen.

### Decisiones que vale la pena conocer

- **Nada se inventó.** Los artículos y resoluciones que no se pudieron verificar
  quedaron nulos y el validador los reporta como error, en vez de completarlos a
  ojo.
- **Los parámetros se calibraron, no se eligieron.** El umbral de distancia
  estaba en 0.45 y dejaba pasar **las tres** consultas fuera de alcance; medido
  contra el golden set, el valor correcto es 0.34. Lo mismo con el peso de
  autoridad: 0.2 en lugar del 0.5 puesto a mano.
- **La ingesta es estricta.** Ante un fallo de Gemini se detiene en vez de
  guardar el pseudo-embedding del *fallback*, que es indistinguible de un vector
  real y degrada la búsqueda en silencio.
- **La abstención vive en código**, antes de invocar al LLM, para no depender de
  que el *prompt* lo convenza de callarse.
- **El golden set v1 quedó congelado.** Sus hashes están fijados en las pruebas
  de integridad; el trabajo nuevo usa `golden_set_v2.json`, en un archivo
  aparte.

---

## 📖 Documentación técnica

| Documento | Contenido |
|---|---|
| [`00_inventario.md`](documentacion/00_inventario.md) | Radiografía del repositorio y stack detectado |
| [`00_linea_base_verificada.md`](documentacion/00_linea_base_verificada.md) | Línea base verificada del proyecto |
| [`01_contrato_funcional_verificado.md`](documentacion/01_contrato_funcional_verificado.md) | Cada acción del frontend contra su endpoint |
| [`01_descripcion_proyecto.md`](documentacion/01_descripcion_proyecto.md) | Descripción funcional |
| [`02_backend_arquitectura.md`](documentacion/02_backend_arquitectura.md) | Arquitectura hexagonal del backend |
| [`03_pipeline_rag.md`](documentacion/03_pipeline_rag.md) | Diseño del pipeline RAG |
| [`03_despliegue_rag_fase3.md`](documentacion/03_despliegue_rag_fase3.md) | Despliegue del RAG |
| [`04_frontend.md`](documentacion/04_frontend.md) | Estructura de la app móvil |
| [`05_banco_pruebas.md`](documentacion/05_banco_pruebas.md) | Banco de pruebas y cobertura |
| [`06_reporte_final.md`](documentacion/06_reporte_final.md) | Reporte final del cierre técnico |
| [`07_rag_operacion.md`](documentacion/07_rag_operacion.md) | **Operar el RAG:** agregar documentos, reindexar, calibrar |
| [`08_metricas_evaluacion.md`](documentacion/08_metricas_evaluacion.md) | Métricas de evaluación y gráficos |

---

¿Se te trabó algo levantando el entorno? Revisa
[Problemas frecuentes](#-problemas-frecuentes) y, si sigue, abre un issue en el
repositorio. 🚀
