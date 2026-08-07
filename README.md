# 🎓 TutorIA — Proyecto de Tutoría con Inteligencia Artificial

¡Bienvenido a **TutorIA**! Este es un proyecto full-stack diseñado para ofrecer tutorías interactivas utilizando Inteligencia Artificial. La aplicación cuenta con un backend robusto en Python y un frontend móvil multiplataforma desarrollado en React Native con Expo.

Esta guía contiene todas las instrucciones necesarias para clonar, configurar y correr el proyecto en tu máquina local.

---

## 📌 Estado de las Fases del Proyecto

- **Fase 5 (Benchmark RAG y Análisis Cuantitativo):** **CERRADA**
- **Fase 6A (Auditoría Integral y Seguridad):** **COMPLETADA**
- **Fase 6B (Migración Pydantic V2 y Seguridad por Entorno):** **COMPLETADA** (162 pruebas aprobadas al cierre de Fase 6B)
- **Fase 6C (Cierre Documental Definitivo):** **CIERRE DOCUMENTAL COMPLETADO** (164 pruebas aprobadas al cierre de Fase 6C)
- **Cierre Técnico del Proyecto:** **COMPLETADO**
- **Suite de Pruebas Automatizadas:** **164 pruebas unitarias aprobadas, 0 fallidas** (144 iniciales, 162 al cerrar Fase 6B, y 164 al cerrar Fase 6C).
- **Fase 6D:** Corresponde únicamente a integración Git, pull request y entrega operativa.
- **Reconstrucción del RAG (Fases 0 a 4):** **COMPLETADA** — 445 pruebas aprobadas. Ver detalle abajo y operación en [`documentacion/07_rag_operacion.md`](documentacion/07_rag_operacion.md).

---

## 🔍 Reconstrucción del sistema RAG

El corpus documental y el motor de recuperación se rehicieron por completo tras una auditoría que midió su precisión real.

### El punto de partida

La evaluación publicada reportaba precisión global 0.33, pero ese número incluía los casos fuera de alcance, que puntúan 1.0 de forma trivial porque no hay nada que recuperar. **Sobre las consultas dentro de alcance, la precisión real era 2 de 12.**

La causa de fondo no estaba en la búsqueda sino en los datos: el corpus era una **paráfrasis temática** de los documentos oficiales y había perdido el articulado. El golden set pedía citas como `"Art. 15 - Reglamento de Tutoría"`, pero **no existía un solo número de artículo en los nueve archivos**, así que esa métrica era imposible de satisfacer por construcción. Algunos artículos citados (18, 22, 23, 25, 30) ni siquiera existen: el reglamento llega hasta el 16.

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
| Pruebas automatizadas | 277 | **445** |

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
transcripción vivía fuera del repositorio. Ahora está en `corpus_fuentes/` y
`validate_malla` la comprueba contra los totales que declara la propia imagen.

### Decisiones que vale la pena conocer

- **Nada se inventó.** Los artículos y resoluciones que no se pudieron verificar quedaron nulos y el validador los reporta como error, en vez de completarlos a ojo.
- **Los parámetros se calibraron, no se eligieron.** El umbral de distancia estaba en 0.45 y dejaba pasar **las tres** consultas fuera de alcance; medido contra el golden set, el valor correcto es 0.34. Lo mismo con el peso de autoridad: 0.2 en lugar del 0.5 puesto a mano.
- **La ingesta es estricta.** Ante un fallo de Gemini se detiene en vez de guardar el pseudo-embedding del *fallback*, que es indistinguible de un vector real y degrada la búsqueda en silencio.
- **La abstención vive en código**, antes de invocar al LLM, para no depender de que el *prompt* lo convenza de callarse.
- **El golden set v1 quedó congelado.** Sus hashes están fijados en las pruebas de integridad; el trabajo nuevo usa `golden_set_v2.json`, en un archivo aparte.

### 🔒 Entornos y Seguridad de Configuración (Fase 6B-2)
- `APP_ENV` admite los entornos: `development`, `test` y `production`.
- En entorno `production`, se bloquean automáticamente configuraciones inseguras de `SECRET_KEY` (claves de menos de 32 caracteres, la clave predeterminada de desarrollo o placeholders documentales).
- En entorno `production`, se bloquean contraseñas de base de datos por defecto o inseguras para `DB_PASSWORD`.
- En entornos `development` y `test`, se conservan las configuraciones por defecto para desarrollo local y ejecución de pruebas automatizadas.

---

## 🛠️ Tecnologías y Arquitectura

El proyecto está dividido en dos partes principales:

1. **Backend (`/backend`):**
   - **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12+)
   - **Base de Datos:** [PostgreSQL](https://www.postgresql.org/) con `pgvector`
   - **ORM & Migraciones:** [SQLAlchemy](https://www.sqlalchemy.org/) (Async) y [Alembic](https://alembic.sqlalchemy.org/)
   - **IA & Modelos Gemini:** Integración oficial con Google Gemini API (`google-genai`).
     - **Modelo Generativo Activo:** `gemini-3.5-flash-lite`
     - **Modelo de Embedding Activo:** `gemini-embedding-2` (768 dimensiones)
     - **Modelo Generativo Anterior:** `gemini-2.5-flash`

2. **Frontend (`/frontend`):**
   - **Framework:** [React Native](https://reactnative.dev/) con [Expo](https://expo.dev/) (SDK 54)
   - **Estilos:** [NativeWind](https://www.nativewind.dev/) (Tailwind CSS para React Native)
   - **Manejador de Estado:** [Zustand](https://github.com/pmndrs/zustand)
   - **Peticiones HTTP:** [Axios](https://axios-http.com/)

---

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado lo siguiente en tu sistema:

- **Git**
- **Docker y Docker Compose** *(Recomendado para correr la base de datos y el backend sin complicaciones)*
- **Node.js** (Versión 18 o superior) y **npm**
- **Python 3.12+** *(Solo si deseas correr el backend de forma local sin Docker)*
- **Expo Go** instalado en tu dispositivo móvil (iOS/Android) para probar la app física, o bien simuladores configurados (Android Studio / Xcode).

---

## 🚀 Guía de Inicio Rápido

Sigue estos pasos para levantar el entorno completo de desarrollo:

### 1. Clonar el repositorio y configurar variables de entorno

Clona este repositorio en tu máquina local y accede a él:

```bash
git clone https://github.com/Tomioka1809/Tutoria-IA.git
cd Tutoria-IA
```

Copia el archivo de variables de entorno de ejemplo a tu archivo `.env` local:

```bash
cp .env.example .env
```

> [!IMPORTANT]
> Abre el archivo `.env` recién creado y reemplaza `GEMINI_API_KEY` con tu clave de API de **Google AI Studio**. Puedes obtener una de manera gratuita en [Google AI Studio](https://aistudio.google.com).

---

### 2. Levantar el Backend y la Base de Datos

Tenemos dos opciones para ejecutar el backend. Elige la que mejor se adapte a tu flujo de trabajo:

#### Opción A: Usando Docker Compose (Recomendada 🐳)

Esta opción levantará tanto la base de datos PostgreSQL como la API de FastAPI dentro de contenedores de Docker de forma automática.

1. Inicia los servicios en segundo plano:
   ```bash
   docker compose up -d
   ```

2. Ejecuta las migraciones de la base de datos (para crear las tablas necesarias):
   ```bash
   docker compose exec backend alembic upgrade head
   ```

El backend ahora estará disponible en [http://localhost:8000](http://localhost:8000). Puedes verificar que está corriendo accediendo a la documentación interactiva en [http://localhost:8000/docs](http://localhost:8000/docs).

---

#### Opción B: Ejecución Local Manual (Sin Docker)

Si prefieres correr el backend directamente en tu máquina:

1. Asegúrate de tener una base de datos PostgreSQL corriendo localmente en el puerto `5433` (o cambia el valor de `DB_PORT` y `DB_HOST=localhost` en tu `.env`).
2. Entra al directorio del backend y crea un entorno virtual de Python:
   ```bash
   cd backend
   python -m venv venv
   ```
3. Activa el entorno virtual:
   * **Linux/macOS:**
     ```bash
     source venv/bin/activate
     ```
   * **Windows (PowerShell):**
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   * **Windows (CMD):**
     ```cmd
     .\venv\Scripts\activate.bat
     ```
4. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
5. Ejecuta las migraciones de Alembic para crear las tablas:
   ```bash
   alembic upgrade head
   ```
6. Inicia el servidor de desarrollo:
   ```bash
   uvicorn app.main:app --reload
   ```

---

### 3. Levantar el Frontend (React Native / Expo)

1. Abre una nueva terminal en la raíz del proyecto y entra al directorio `frontend`:
   ```bash
   cd frontend
   ```

2. Instala las dependencias de Node:
   ```bash
   npm install
   ```

3. Inicia el servidor de desarrollo de Expo:
   ```bash
   npm run start
   ```
   *(O bien `npx expo start`)*

#### ¿Cómo probar la app?

- **Dispositivo móvil real (Recomendado):** Abre la aplicación **Expo Go** en tu celular y escanea el código QR que se muestra en la terminal.
- **Simulador de Android:** Presiona `a` en la terminal (requiere tener Android Studio con un emulador configurado y corriendo).
- **Simulador de iOS:** Presiona `i` en la terminal (requiere macOS con Xcode configurado).
- **Navegador Web:** Presiona `w` para abrir la versión web (limitado a soporte web de las librerías).

> [!TIP]
> **Conexión Automática:** El frontend está configurado en [client.ts](file:///home/tsuki/Downloads/React-Native/frontend/src/api/client.ts) para detectar automáticamente la dirección IP de tu máquina host en la red local. Esto permite que tu celular (conectado al mismo Wi-Fi) se comunique con el backend corriendo en tu computadora sin configurar URLs manuales.

---

## 📁 Estructura del Proyecto

A grandes rasgos, el proyecto se organiza de la siguiente manera:

```text
React-Native/
├── backend/
│   ├── alembic/             # Migraciones de base de datos
│   ├── app/
│   │   ├── api/             # Endpoints de la API (v1)
│   │   ├── core/            # Configuración general y seguridad (JWT)
│   │   ├── db/              # Sesión y modelos base de SQLAlchemy
│   │   ├── models/          # Modelos de base de datos (Conversaciones, Mensajes, etc.)
│   │   ├── schemas/         # Esquemas de validación de Pydantic
│   │   └── services/        # Lógica de negocio (como integración con Gemini)
│   ├── Dockerfile
│   └── requirements.txt     # Dependencias de Python
├── frontend/
│   ├── app/                 # Vistas y enrutamiento (Expo Router)
│   ├── src/
│   │   ├── api/             # Cliente Axios configurado para conectarse al backend
│   │   ├── store/           # Estado global con Zustand (Auth, etc.)
│   │   └── components/      # Componentes compartidos de la interfaz
│   ├── package.json         # Dependencias de Node
│   └── tailwind.config.js   # Configuración de Tailwind CSS
├── docker-compose.yml       # Orquestación de DB y API
├── .env.example             # Plantilla de variables de entorno
└── README.md                # Esta guía
```

---

## 💡 Flujo de Desarrollo Común

- **Agregar dependencias backend:** Agrégalas a [requirements.txt](file:///home/tsuki/Downloads/React-Native/backend/requirements.txt) y reconstruye tu contenedor con `docker compose build`.
- **Modificar base de datos:** Si añades o cambias un modelo en `backend/app/models/`, genera una nueva migración con:
  ```bash
  docker compose exec backend alembic revision --autogenerate -m "descripción del cambio"
  ```
  Y aplícala con:
  ```bash
  docker compose exec backend alembic upgrade head
  ```
- **Resetear base de datos:** Si deseas limpiar la base de datos por completo y volver a correr las migraciones:
  ```bash
  docker compose down -v
  docker compose up -d
  docker compose exec backend alembic upgrade head
  ```

---

¡Listo! Con esto tú y tu equipo ya pueden trabajar en el proyecto. Si tienes alguna duda o inconveniente levantando el entorno, no dudes en preguntar. 🚀
