# 🎓 TutorIA — Proyecto de Tutoría con Inteligencia Artificial

¡Bienvenido a **TutorIA**! Este es un proyecto full-stack diseñado para ofrecer tutorías interactivas utilizando Inteligencia Artificial. La aplicación cuenta con un backend robusto en Python y un frontend móvil multiplataforma desarrollado en React Native con Expo.

Esta guía contiene todas las instrucciones necesarias para clonar, configurar y correr el proyecto en tu máquina local.

---

## 🛠️ Tecnologías y Arquitectura

El proyecto está dividido en dos partes principales:

1. **Backend (`/backend`):**
   - **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12+)
   - **Base de Datos:** [PostgreSQL](https://www.postgresql.org/)
   - **ORM & Migraciones:** [SQLAlchemy](https://www.sqlalchemy.org/) (Async) y [Alembic](https://alembic.sqlalchemy.org/)
   - **IA:** Integración con la API de Google Gemini (Google AI Studio)

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
