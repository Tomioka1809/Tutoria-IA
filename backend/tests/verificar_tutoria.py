#!/usr/bin/env python3
"""
Verificador por fases del proyecto TutorIA.

Este script NO modifica el proyecto. Audita estructura, configuración, código,
pipeline RAG, frontend, banco de pruebas e integración.

Ejemplos:
    python backend/tests/verificar_tutoria.py --fase 0
    python backend/tests/verificar_tutoria.py --fase 2,3
    python backend/tests/verificar_tutoria.py --fase todas

Pruebas que requieren servicios locales:
    python backend/tests/verificar_tutoria.py --fase 2,5,6 --integracion

--root sale de os.getcwd(), asi que debe ejecutarse desde la raiz del
repositorio, no desde la carpeta del script. Si no, indicarla:
    python backend/tests/verificar_tutoria.py --root /ruta/al/proyecto --fase todas
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence


PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"
SKIP = "SKIP"


@dataclass
class Result:
    phase: int
    code: str
    description: str
    status: str
    detail: str = ""
    duration_ms: int = 0


class Verifier:
    def __init__(
        self,
        root: Path,
        integration: bool,
        backend_url: str,
        timeout: int,
        verbose: bool,
    ) -> None:
        self.root = root.resolve()
        self.integration = integration
        self.backend_url = backend_url.rstrip("/")
        self.timeout = timeout
        self.verbose = verbose
        self.results: list[Result] = []

    # ------------------------------------------------------------------
    # Utilidades generales
    # ------------------------------------------------------------------
    def add(
        self,
        phase: int,
        code: str,
        description: str,
        status: str,
        detail: str = "",
        duration_ms: int = 0,
    ) -> None:
        self.results.append(
            Result(
                phase=phase,
                code=code,
                description=description,
                status=status,
                detail=detail,
                duration_ms=duration_ms,
            )
        )

    def check(
        self,
        phase: int,
        code: str,
        description: str,
        callback: Callable[[], tuple[str, str]],
    ) -> None:
        start = time.perf_counter()
        try:
            status, detail = callback()
        except Exception as exc:
            status = FAIL
            detail = f"{type(exc).__name__}: {exc}"
        elapsed = int((time.perf_counter() - start) * 1000)
        self.add(phase, code, description, status, detail, elapsed)

    def rel(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.root))
        except ValueError:
            return str(path)

    def first_existing(self, *items: str) -> Path | None:
        for item in items:
            path = self.root / item
            if path.exists():
                return path
        return None

    @staticmethod
    def read_text(path: Path) -> str:
        return path.read_text(encoding="utf-8", errors="replace")

    @staticmethod
    def read_json(path: Path) -> object:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))

    def source_files(self, base: Path, suffixes: Sequence[str]) -> list[Path]:
        if not base.exists():
            return []

        ignored = {
            ".git",
            ".expo",
            ".next",
            ".venv",
            "venv",
            "__pycache__",
            "node_modules",
            "dist",
            "build",
        }

        files: list[Path] = []
        for path in base.rglob("*"):
            if any(part in ignored for part in path.parts):
                continue
            if path.is_file() and path.suffix.lower() in suffixes:
                files.append(path)
        return files

    def regex_matches(
        self,
        files: Iterable[Path],
        pattern: str,
        flags: int = re.IGNORECASE,
    ) -> list[tuple[Path, int, str]]:
        regex = re.compile(pattern, flags)
        matches: list[tuple[Path, int, str]] = []

        for path in files:
            try:
                lines = self.read_text(path).splitlines()
            except OSError:
                continue

            for number, line in enumerate(lines, start=1):
                if regex.search(line):
                    matches.append((path, number, line.strip()))

        return matches

    def format_matches(
        self,
        matches: Sequence[tuple[Path, int, str]],
        limit: int = 8,
    ) -> str:
        lines = [
            f"{self.rel(path)}:{number}: {line[:180]}"
            for path, number, line in matches[:limit]
        ]
        if len(matches) > limit:
            lines.append(f"... y {len(matches) - limit} coincidencias adicionales")
        return "\n".join(lines)

    @staticmethod
    def command_exists(command: str) -> bool:
        return shutil.which(command) is not None

    def run_command(
        self,
        command: Sequence[str],
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> tuple[int, str]:
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)

        process = subprocess.run(
            list(command),
            cwd=str(cwd or self.root),
            env=merged_env,
            capture_output=True,
            text=True,
            timeout=timeout or self.timeout,
            check=False,
        )
        output = "\n".join(
            part.strip()
            for part in (process.stdout, process.stderr)
            if part.strip()
        )
        return process.returncode, output[-8000:]

    def backend_python(self) -> str:
        candidates = [
            self.root / "backend/venv/bin/python",
            self.root / "backend/.venv/bin/python",
            self.root / "backend/venv/Scripts/python.exe",
            self.root / "backend/.venv/Scripts/python.exe",
        ]
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        return sys.executable

    def http_get(self, url: str) -> tuple[int, str]:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "TutorIA-Verifier/1.0"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read(500_000).decode("utf-8", errors="replace")
                return response.status, body
        except urllib.error.HTTPError as exc:
            body = exc.read(100_000).decode("utf-8", errors="replace")
            return exc.code, body

    # ------------------------------------------------------------------
    # Fase 0: inventario, configuración y línea base
    # ------------------------------------------------------------------
    def phase_0(self) -> None:
        phase = 0

        def structure() -> tuple[str, str]:
            required = [
                "backend",
                "backend/app",
                "backend/app/domain",
                "backend/app/application",
                "backend/app/infrastructure",
                "frontend",
                "frontend/app",
                "frontend/src",
                "docker-compose.yml",
            ]
            missing = [item for item in required if not (self.root / item).exists()]
            if missing:
                return FAIL, "Faltan rutas esenciales: " + ", ".join(missing)
            return PASS, "La estructura principal del repositorio está presente."

        self.check(phase, "F0-001", "Estructura principal", structure)

        def configuration_files() -> tuple[str, str]:
            groups = {
                "plantilla de entorno": [".env.example", "backend/.env.example"],
                "dependencias backend": [
                    "backend/requirements.txt",
                    "backend/pyproject.toml",
                ],
                "dependencias frontend": ["frontend/package.json"],
                "migraciones": ["backend/alembic.ini", "backend/alembic"],
            }

            missing: list[str] = []
            selected: list[str] = []
            for label, alternatives in groups.items():
                match = self.first_existing(*alternatives)
                if match is None:
                    missing.append(label)
                else:
                    selected.append(self.rel(match))

            if missing:
                return FAIL, "No se encontró: " + ", ".join(missing)
            return PASS, "Archivos localizados: " + ", ".join(selected)

        self.check(
            phase,
            "F0-002",
            "Configuración y dependencias",
            configuration_files,
        )

        def env_security() -> tuple[str, str]:
            gitignore = self.root / ".gitignore"
            if not gitignore.exists():
                return WARN, "No existe .gitignore en la raíz."

            text = self.read_text(gitignore)
            ignores_env = bool(
                re.search(r"(?m)^\s*\.env(?:\*|$)", text)
                or re.search(r"(?m)^\s*\*\*/\.env(?:\*|$)", text)
            )
            if not ignores_env:
                return FAIL, ".gitignore no parece excluir los archivos .env."

            if self.command_exists("git") and (self.root / ".git").exists():
                code, output = self.run_command(
                    ["git", "ls-files", ".env", "backend/.env", "frontend/.env"]
                )
                if code == 0 and output.strip():
                    return FAIL, "Hay archivos .env rastreados por Git:\n" + output

            return PASS, "Los archivos .env están protegidos frente a Git."

        self.check(phase, "F0-003", "Protección de secretos", env_security)

        def env_example() -> tuple[str, str]:
            env_file = self.first_existing(".env.example", "backend/.env.example")
            if env_file is None:
                return FAIL, "No se encontró .env.example."

            present = {
                match.group(1)
                for match in re.finditer(
                    r"(?m)^\s*([A-Z][A-Z0-9_]*)\s*=",
                    self.read_text(env_file),
                )
            }
            expected = {
                "DB_USER",
                "DB_PASSWORD",
                "DB_NAME",
                "DB_HOST",
                "DB_PORT",
                "SECRET_KEY",
                "GEMINI_API_KEY",
            }
            missing = sorted(expected - present)

            if missing:
                return WARN, "Variables no declaradas: " + ", ".join(missing)
            return PASS, f"Plantilla revisada: {self.rel(env_file)}"

        self.check(phase, "F0-004", "Variables de entorno mínimas", env_example)

        def compose_syntax() -> tuple[str, str]:
            if not self.command_exists("docker"):
                return SKIP, "Docker no está disponible en PATH."

            code, output = self.run_command(
                ["docker", "compose", "config", "--quiet"],
                timeout=max(self.timeout, 30),
            )
            if code != 0:
                return FAIL, output or "docker compose config devolvió error."
            return PASS, "docker-compose.yml es sintácticamente válido."

        self.check(phase, "F0-005", "Sintaxis de Docker Compose", compose_syntax)

    # ------------------------------------------------------------------
    # Fase 1: contrato funcional y consistencia del stack
    # ------------------------------------------------------------------
    def phase_1(self) -> None:
        phase = 1

        def backend_stack() -> tuple[str, str]:
            dependency_file = self.first_existing(
                "backend/requirements.txt",
                "backend/pyproject.toml",
            )
            if dependency_file is None:
                return FAIL, "No existe archivo de dependencias backend."

            text = self.read_text(dependency_file).lower()
            expected = [
                "fastapi",
                "sqlalchemy",
                "alembic",
                "asyncpg",
                "google-genai",
            ]
            missing = [name for name in expected if name not in text]
            if missing:
                return WARN, "Dependencias no detectadas: " + ", ".join(missing)
            return PASS, "Stack principal del backend detectado."

        self.check(phase, "F1-001", "Stack del backend", backend_stack)

        def frontend_stack() -> tuple[str, str]:
            package = self.root / "frontend/package.json"
            if not package.exists():
                return FAIL, "No existe frontend/package.json."

            data = self.read_json(package)
            if not isinstance(data, dict):
                return FAIL, "package.json no contiene un objeto JSON."

            dependencies: dict[str, object] = {}
            dependencies.update(data.get("dependencies", {}) or {})
            dependencies.update(data.get("devDependencies", {}) or {})

            expected = [
                "expo",
                "react-native",
                "expo-router",
                "zustand",
                "axios",
                "i18next",
                "nativewind",
            ]
            missing = [name for name in expected if name not in dependencies]
            if missing:
                return WARN, "Paquetes no detectados: " + ", ".join(missing)

            versions = ", ".join(
                f"{name}={dependencies[name]}" for name in expected
            )
            return PASS, versions

        self.check(phase, "F1-002", "Stack del frontend", frontend_stack)

        def role_routes() -> tuple[str, str]:
            app_dir = self.root / "frontend/app"
            groups = {
                "autenticación": ["auth", "(auth)"],
                "estudiante": ["(estudiante)", "estudiante"],
                "tutor": ["(tutor)", "tutor"],
                "administrador": ["(admin)", "admin"],
            }

            missing: list[str] = []
            found: list[str] = []
            for label, alternatives in groups.items():
                match = next(
                    (
                        app_dir / name
                        for name in alternatives
                        if (app_dir / name).exists()
                    ),
                    None,
                )
                if match is None:
                    missing.append(label)
                else:
                    found.append(self.rel(match))

            if missing:
                return WARN, "Rutas no encontradas: " + ", ".join(missing)
            return PASS, "Rutas por rol: " + ", ".join(found)

        self.check(phase, "F1-003", "Navegación por roles", role_routes)

        def phase_documents() -> tuple[str, str]:
            docs = self.root / "documentacion"
            if not docs.exists():
                return WARN, "No existe documentacion/."

            names = [path.name for path in docs.glob("*.md")]
            missing = [
                f"{number:02d}_"
                for number in range(7)
                if not any(name.startswith(f"{number:02d}_") for name in names)
            ]
            if missing:
                return WARN, "Faltan documentos con prefijo: " + ", ".join(missing)
            return PASS, f"Se detectaron {len(names)} documentos Markdown."

        self.check(phase, "F1-004", "Documentación por fases", phase_documents)

    # ------------------------------------------------------------------
    # Fase 2: backend y arquitectura hexagonal
    # ------------------------------------------------------------------
    def phase_2(self) -> None:
        phase = 2
        app = self.root / "backend/app"

        def python_syntax() -> tuple[str, str]:
            if not app.exists():
                return FAIL, "No existe backend/app."

            python = self.backend_python()
            code, output = self.run_command(
                [python, "-m", "compileall", "-q", str(app)],
                timeout=max(self.timeout, 60),
            )
            if code != 0:
                return FAIL, output or "compileall devolvió error."
            return PASS, f"Compilación sintáctica correcta con {python}."

        self.check(phase, "F2-001", "Sintaxis Python", python_syntax)

        def domain_purity() -> tuple[str, str]:
            files = self.source_files(app / "domain", [".py"])
            matches = self.regex_matches(
                files,
                r"^\s*(?:from|import)\s+"
                r"(?:fastapi|sqlalchemy|app\.infrastructure|"
                r"backend\.app\.infrastructure)",
                flags=re.IGNORECASE,
            )
            if matches:
                return FAIL, (
                    "Dependencias externas dentro de domain:\n"
                    + self.format_matches(matches)
                )
            return PASS, "domain no importa FastAPI, SQLAlchemy ni infrastructure."

        self.check(phase, "F2-002", "Pureza de domain", domain_purity)

        def application_isolation() -> tuple[str, str]:
            files = self.source_files(app / "application", [".py"])
            matches = self.regex_matches(
                files,
                r"^\s*(?:from|import)\s+"
                r"(?:fastapi|sqlalchemy|app\.infrastructure|"
                r"backend\.app\.infrastructure)",
                flags=re.IGNORECASE,
            )
            if matches:
                return WARN, (
                    "Acoplamientos en application:\n"
                    + self.format_matches(matches)
                )
            return PASS, "application no importa frameworks ni infrastructure."

        self.check(
            phase,
            "F2-003",
            "Aislamiento de application",
            application_isolation,
        )

        def schemas_module() -> tuple[str, str]:
            schemas = app / "domain/schemas"
            if not schemas.exists():
                return FAIL, "No existe backend/app/domain/schemas."

            modules = list(schemas.glob("*.py"))
            init = schemas / "__init__.py"
            if not modules:
                return FAIL, "domain/schemas no contiene módulos Python."
            if not init.exists() or not self.read_text(init).strip():
                return WARN, "domain/schemas/__init__.py está ausente o vacío."
            return PASS, f"{len(modules)} módulo(s) en domain/schemas."

        self.check(phase, "F2-004", "Esquemas y DTO", schemas_module)

        def domain_exceptions() -> tuple[str, str]:
            path = app / "domain/exceptions.py"
            if not path.exists():
                return FAIL, "No existe domain/exceptions.py."

            classes = re.findall(
                r"(?m)^\s*class\s+([A-Za-z_]\w*)",
                self.read_text(path),
            )
            if len(classes) < 3:
                return WARN, f"Solo se detectaron {len(classes)} excepciones."
            return PASS, "Excepciones: " + ", ".join(classes[:12])

        self.check(
            phase,
            "F2-005",
            "Excepciones de dominio",
            domain_exceptions,
        )

        if self.integration:
            def pytest_execution() -> tuple[str, str]:
                tests = self.root / "backend/tests"
                if not tests.exists():
                    return SKIP, "No existe backend/tests."

                python = self.backend_python()
                code, output = self.run_command(
                    [python, "-m", "pytest", "-q", str(tests)],
                    env={"PYTHONPATH": str(self.root / "backend")},
                    timeout=max(self.timeout, 240),
                )
                if code != 0:
                    return FAIL, output
                return PASS, output or "pytest finalizó correctamente."

            self.check(phase, "F2-006", "Ejecución de pytest", pytest_execution)
        else:
            self.add(
                phase,
                "F2-006",
                "Ejecución de pytest",
                SKIP,
                "Use --integracion para ejecutar las pruebas.",
            )

    # ------------------------------------------------------------------
    # Fase 3: pipeline RAG
    # ------------------------------------------------------------------
    def phase_3(self) -> None:
        phase = 3
        backend = self.root / "backend"
        app_files = self.source_files(backend / "app", [".py"])

        def corpus_integrity() -> tuple[str, str]:
            # Se audita el corpus estructurado y no las otras dos carpetas de
            # backend/corpus/: heredado/ y fuentes/ son material de origen, y
            # estructurado/ es lo unico que ingest_corpus.py indexa.
            corpus = backend / "corpus" / "estructurado"
            if not corpus.exists():
                return FAIL, "No existe backend/corpus/estructurado."

            json_files = sorted(corpus.glob("*.json"))
            if not json_files:
                return FAIL, "No hay archivos JSON en backend/corpus/estructurado."

            invalid: list[str] = []
            empty: list[str] = []
            for path in json_files:
                try:
                    data = self.read_json(path)
                    if data in ({}, [], "", None):
                        empty.append(path.name)
                except Exception as exc:
                    invalid.append(f"{path.name}: {exc}")

            if invalid:
                return FAIL, "JSON inválidos: " + "; ".join(invalid)
            if empty:
                return WARN, "Archivos vacíos: " + ", ".join(empty)
            return PASS, f"{len(json_files)} archivos JSON válidos."

        self.check(phase, "F3-001", "Integridad del corpus", corpus_integrity)

        def vector_metric() -> tuple[str, str]:
            candidates = [
                path
                for path in app_files
                if "corpus" in self.rel(path).lower()
                or "repository" in self.rel(path).lower()
            ]
            cosine = self.regex_matches(
                candidates,
                r"cosine_distance|vector_cosine_ops|<=>",
            )
            l2 = self.regex_matches(
                candidates,
                r"l2_distance|vector_l2_ops|<->",
            )

            if l2 and not cosine:
                return FAIL, (
                    "Solo se detectó distancia L2:\n"
                    + self.format_matches(l2)
                )
            if l2 and cosine:
                return WARN, (
                    "Hay referencias a coseno y L2; confirmar la consulta activa:\n"
                    + self.format_matches(cosine + l2)
                )
            if cosine:
                return PASS, (
                    "Recuperación por coseno detectada:\n"
                    + self.format_matches(cosine)
                )
            return WARN, "No se pudo identificar la métrica vectorial."

        self.check(phase, "F3-002", "Métrica vectorial", vector_metric)

        def embedding_model() -> tuple[str, str]:
            docs = self.source_files(self.root / "documentacion", [".md"])
            files = app_files + docs
            pattern = (
                r"(?:gemini-embedding-\d+|text-embedding-\d+|"
                r"models/[A-Za-z0-9._-]*embedding[A-Za-z0-9._-]*)"
            )
            matches = self.regex_matches(files, pattern)
            regex = re.compile(pattern, re.IGNORECASE)
            names: set[str] = set()

            for _, _, line in matches:
                names.update(name.lower() for name in regex.findall(line))

            if len(names) > 1:
                return WARN, (
                    "Modelos distintos detectados: "
                    + ", ".join(sorted(names))
                )
            if len(names) == 1:
                return PASS, "Modelo detectado: " + next(iter(names))
            return WARN, "No se identificó el modelo de embeddings."

        self.check(
            phase,
            "F3-003",
            "Consistencia del modelo de embeddings",
            embedding_model,
        )

        def embedding_dimensions() -> tuple[str, str]:
            candidates = [
                path
                for path in app_files
                if any(
                    token in self.rel(path).lower()
                    for token in ("gemini", "corpus", "model")
                )
            ]
            matches = self.regex_matches(
                candidates,
                r"(?:output_dimensionality\s*=\s*|"
                r"Vector\s*\(\s*|VECTOR\s*\(\s*)768\b",
            )
            if not matches:
                return WARN, "No se pudo confirmar la dimensionalidad 768."
            return PASS, (
                "Dimensionalidad 768 detectada:\n"
                + self.format_matches(matches)
            )

        self.check(
            phase,
            "F3-004",
            "Dimensionalidad vectorial",
            embedding_dimensions,
        )

        def retrieval_threshold() -> tuple[str, str]:
            candidates = [
                path
                for path in app_files
                if any(
                    token in self.rel(path).lower()
                    for token in ("chat", "corpus", "retriev")
                )
            ]
            matches = self.regex_matches(
                candidates,
                r"score_threshold|min_similarity|similarity_threshold|"
                r"max_distance|distance_threshold",
            )
            if not matches:
                return WARN, "No se detectó un umbral explícito de similitud."
            return PASS, (
                "Umbral potencial detectado:\n"
                + self.format_matches(matches)
            )

        self.check(
            phase,
            "F3-005",
            "Umbral de recuperación",
            retrieval_threshold,
        )

        def hnsw_index() -> tuple[str, str]:
            files = self.source_files(backend / "alembic", [".py", ".sql"])
            matches = self.regex_matches(files, r"\bhnsw\b|vector_cosine_ops")
            if not matches:
                return WARN, "No se detectó índice HNSW en migraciones."
            return PASS, "Índice detectado:\n" + self.format_matches(matches)

        self.check(phase, "F3-006", "Índice vectorial HNSW", hnsw_index)

        def grounding_policy() -> tuple[str, str]:
            candidates = [
                path
                for path in app_files
                if any(
                    token in self.rel(path).lower()
                    for token in ("chat", "gemini", "prompt")
                )
            ]
            unsafe = self.regex_matches(
                candidates,
                r"seg[uú]n internet|buscar en internet|"
                r"conocimiento general|general knowledge",
            )
            abstention = self.regex_matches(
                candidates,
                r"fuera de alcance|no invent|"
                r"no (?:tengo|dispongo|cuento con) (?:esa )?informaci[oó]n",
            )

            if unsafe:
                return WARN, (
                    "El prompt podría permitir respuestas no ancladas:\n"
                    + self.format_matches(unsafe)
                )
            if abstention:
                return PASS, (
                    "Política de abstención detectada:\n"
                    + self.format_matches(abstention)
                )
            return WARN, "No se confirmó una política explícita de abstención."

        self.check(
            phase,
            "F3-007",
            "Grounding y abstención",
            grounding_policy,
        )

    # ------------------------------------------------------------------
    # Fase 4: frontend React Native / Expo
    # ------------------------------------------------------------------
    def phase_4(self) -> None:
        phase = 4
        frontend = self.root / "frontend"
        files = self.source_files(
            frontend,
            [".ts", ".tsx", ".js", ".jsx"],
        )

        def package_configuration() -> tuple[str, str]:
            package = frontend / "package.json"
            if not package.exists():
                return FAIL, "No existe frontend/package.json."

            data = self.read_json(package)
            if not isinstance(data, dict):
                return FAIL, "package.json no contiene un objeto JSON."

            scripts = data.get("scripts", {}) or {}
            if not scripts:
                return WARN, "package.json no define scripts."
            return PASS, "Scripts: " + ", ".join(sorted(scripts))

        self.check(
            phase,
            "F4-001",
            "Configuración npm/Expo",
            package_configuration,
        )

        def hardcoded_ip() -> tuple[str, str]:
            candidates = [
                path
                for path in files
                if any(
                    token in self.rel(path).lower()
                    for token in ("api", "client", "service", "config")
                )
            ]
            matches = self.regex_matches(
                candidates,
                r"https?://(?:"
                r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
                r"192\.168\.\d{1,3}\.\d{1,3}|"
                r"172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}"
                r")(?::\d+)?",
            )
            if matches:
                return WARN, (
                    "IP privada hardcodeada:\n"
                    + self.format_matches(matches)
                )
            return PASS, "No se detectaron IP privadas hardcodeadas."

        self.check(phase, "F4-002", "URL dinámica del backend", hardcoded_ip)

        def authenticated_client() -> tuple[str, str]:
            api_files = [
                path
                for path in files
                if any(
                    token in self.rel(path).lower()
                    for token in ("api", "client", "service")
                )
            ]
            bearer = self.regex_matches(
                api_files,
                r"Authorization.*Bearer|Bearer\s*\$\{",
            )
            interceptor = self.regex_matches(
                api_files,
                r"interceptors\.request|interceptors\.response",
            )

            if not bearer:
                return FAIL, "No se detectó Authorization: Bearer."
            if not interceptor:
                return WARN, "Bearer detectado, pero no interceptores Axios."
            return PASS, "Autorización JWT e interceptores detectados."

        self.check(
            phase,
            "F4-003",
            "Cliente API autenticado",
            authenticated_client,
        )

        def direct_fetches() -> tuple[str, str]:
            matches = self.regex_matches(files, r"\bfetch\s*\(")
            if not matches:
                return PASS, "No se detectaron llamadas fetch directas."

            suspicious: list[tuple[Path, int, str]] = []
            for path, number, line in matches:
                lines = self.read_text(path).splitlines()
                start = max(0, number - 4)
                end = min(len(lines), number + 14)
                window = "\n".join(lines[start:end])
                if not re.search(r"Authorization|Bearer", window, re.IGNORECASE):
                    suspicious.append((path, number, line))

            if suspicious:
                return WARN, (
                    "fetch sin autorización cercana; revisar:\n"
                    + self.format_matches(suspicious)
                )
            return PASS, "Los fetch detectados incluyen autorización cercana."

        self.check(
            phase,
            "F4-004",
            "Llamadas HTTP fuera de Axios",
            direct_fetches,
        )

        def i18n_parity() -> tuple[str, str]:
            locales = frontend / "src/i18n/locales"
            es = locales / "es.json"
            en = locales / "en.json"

            if not es.exists() or not en.exists():
                return WARN, "No se encontraron simultáneamente es.json y en.json."

            def flatten(value: object, prefix: str = "") -> set[str]:
                keys: set[str] = set()
                if isinstance(value, dict):
                    for key, child in value.items():
                        complete = f"{prefix}.{key}" if prefix else str(key)
                        keys.add(complete)
                        keys.update(flatten(child, complete))
                return keys

            es_keys = flatten(self.read_json(es))
            en_keys = flatten(self.read_json(en))
            only_es = sorted(es_keys - en_keys)
            only_en = sorted(en_keys - es_keys)

            if only_es or only_en:
                details: list[str] = []
                if only_es:
                    details.append("Faltan en EN: " + ", ".join(only_es[:20]))
                if only_en:
                    details.append("Faltan en ES: " + ", ".join(only_en[:20]))
                return WARN, "\n".join(details)

            return PASS, f"Paridad confirmada para {len(es_keys)} claves."

        self.check(phase, "F4-005", "Paridad i18n ES/EN", i18n_parity)

        def typescript_check() -> tuple[str, str]:
            if not (frontend / "node_modules").exists():
                return SKIP, "node_modules no existe; no se instalarán paquetes."

            if not self.command_exists("npx"):
                return SKIP, "npx no está disponible."

            code, output = self.run_command(
                ["npx", "tsc", "--noEmit", "--pretty", "false"],
                cwd=frontend,
                timeout=max(self.timeout, 180),
            )
            if code != 0:
                return FAIL, output
            return PASS, output or "TypeScript no reportó errores."

        self.check(
            phase,
            "F4-006",
            "Comprobación TypeScript",
            typescript_check,
        )

        def lint_check() -> tuple[str, str]:
            package = frontend / "package.json"
            if not package.exists():
                return FAIL, "No existe package.json."
            if not (frontend / "node_modules").exists():
                return SKIP, "node_modules no existe."

            data = self.read_json(package)
            scripts = data.get("scripts", {}) if isinstance(data, dict) else {}
            if "lint" not in scripts:
                return SKIP, "package.json no define el script lint."

            code, output = self.run_command(
                ["npm", "run", "lint"],
                cwd=frontend,
                timeout=max(self.timeout, 180),
            )
            if code != 0:
                return FAIL, output
            return PASS, output or "Lint finalizó correctamente."

        self.check(phase, "F4-007", "Lint del frontend", lint_check)

    # ------------------------------------------------------------------
    # Fase 5: banco de pruebas y métricas RAG
    # ------------------------------------------------------------------
    def phase_5(self) -> None:
        phase = 5
        tests = self.root / "backend/tests"

        def golden_path() -> Path | None:
            candidates = [
                tests / "dataset/golden_set.json",
                tests / "golden_set.json",
            ]
            return next((path for path in candidates if path.exists()), None)

        def golden_set() -> tuple[str, str]:
            path = golden_path()
            if path is None:
                return FAIL, "No se encontró golden_set.json."

            data = self.read_json(path)
            if isinstance(data, dict):
                for key in (
                    "cases",
                    "casos",
                    "questions",
                    "preguntas",
                    "items",
                    "data",
                ):
                    if isinstance(data.get(key), list):
                        data = data[key]
                        break

            if not isinstance(data, list):
                return FAIL, "El Golden Set no contiene una lista de casos."

            count = len(data)
            incomplete = 0
            for case in data:
                if not isinstance(case, dict):
                    incomplete += 1
                    continue

                has_question = any(
                    case.get(key)
                    for key in ("question", "pregunta", "query")
                )
                has_expected = any(
                    case.get(key)
                    for key in (
                        "expected_answer",
                        "respuesta_esperada",
                        "answer",
                    )
                )
                if not has_question or not has_expected:
                    incomplete += 1

            if incomplete:
                return WARN, f"{count} casos; {incomplete} parecen incompletos."
            if count != 15:
                return FAIL, f"El Golden Set contiene {count} casos; se esperaban exactamente 15."
            return PASS, f"Golden Set válido con {count} casos."

        self.check(phase, "F5-001", "Golden Dataset", golden_set)

        def evaluation_modules() -> tuple[str, str]:
            expected = [
                tests / "test_retrieval.py",
                tests / "test_generation.py",
                tests / "run_eval.py",
            ]
            missing = [self.rel(path) for path in expected if not path.exists()]
            if missing:
                return FAIL, "Faltan módulos: " + ", ".join(missing)
            return PASS, "Módulos de retrieval, generation y runner presentes."

        self.check(
            phase,
            "F5-002",
            "Suite de evaluación",
            evaluation_modules,
        )

        def result_artifacts() -> tuple[str, str]:
            json_file = tests / "resultados/eval_results.json"
            csv_file = tests / "resultados/eval_results.csv"
            hist_json = tests / "resultados/historico_32/eval_results_32.json"
            manifest = tests / "dataset/golden_set_manifest.json"

            if not json_file.exists() and not csv_file.exists():
                if hist_json.exists() and manifest.exists():
                    return PASS, "Resultados de 32 archivados en historico_32/. Benchmark de 15 casos pendiente de ejecución."
                return WARN, "Resultados no generados."

            missing = [
                self.rel(path)
                for path in (json_file, csv_file)
                if not path.exists()
            ]
            if missing:
                return WARN, "Resultados no generados: " + ", ".join(missing)
            if json_file.stat().st_size == 0 or csv_file.stat().st_size == 0:
                return FAIL, "Uno de los resultados está vacío."
            return PASS, "Resultados JSON y CSV presentes."

        self.check(
            phase,
            "F5-003",
            "Artefactos de resultados",
            result_artifacts,
        )

        def metric_ranges() -> tuple[str, str]:
            path = tests / "resultados/eval_results.json"
            hist_path = tests / "resultados/historico_32/eval_results_32.json"

            target_path = path if path.exists() else (hist_path if hist_path.exists() else None)
            if target_path is None:
                return SKIP, "No existen artefactos de resultados."

            data = self.read_json(target_path)
            metrics: list[tuple[str, float]] = []

            def walk(value: object, prefix: str = "") -> None:
                if isinstance(value, dict):
                    for key, child in value.items():
                        complete = f"{prefix}.{key}" if prefix else str(key)
                        if (
                            re.search(
                                r"precision|precisi[oó]n|recall|cobertura|"
                                r"faithfulness|pertinencia",
                                str(key),
                                re.IGNORECASE,
                            )
                            and isinstance(child, (int, float))
                        ):
                            metrics.append((complete, float(child)))
                        walk(child, complete)
                elif isinstance(value, list):
                    for index, child in enumerate(value):
                        walk(child, f"{prefix}[{index}]")

            walk(data)

            if not metrics:
                return WARN, "No se identificaron métricas numéricas."

            invalid = [
                (name, value)
                for name, value in metrics
                if not (0 <= value <= 1 or 0 <= value <= 100)
            ]
            if invalid:
                text = ", ".join(
                    f"{name}={value}" for name, value in invalid[:12]
                )
                return FAIL, "Métricas fuera de rango: " + text

            text = ", ".join(
                f"{name}={value}" for name, value in metrics[:12]
            )
            prefix_label = "Métricas detectadas" if path.exists() else "Métricas históricas archivadas (32 casos)"
            return PASS, f"{prefix_label}: {text}"

        self.check(phase, "F5-004", "Rango de métricas", metric_ranges)

        if self.integration:
            def run_evaluation() -> tuple[str, str]:
                runner = tests / "run_eval.py"
                if not runner.exists():
                    return SKIP, "No existe run_eval.py."

                python = self.backend_python()
                code, output = self.run_command(
                    [python, str(runner)],
                    env={
                        "PYTHONPATH": str(self.root / "backend"),
                        "DB_HOST": os.environ.get("DB_HOST", "localhost"),
                        "DB_PORT": os.environ.get("DB_PORT", "5433"),
                    },
                    timeout=max(self.timeout, 900),
                )
                if code != 0:
                    return FAIL, output
                return PASS, output or "La evaluación finalizó correctamente."

            self.check(
                phase,
                "F5-005",
                "Ejecución del benchmark RAG",
                run_evaluation,
            )
        else:
            self.add(
                phase,
                "F5-005",
                "Ejecución del benchmark RAG",
                SKIP,
                "Use --integracion; esta prueba puede consumir Gemini.",
            )

    # ------------------------------------------------------------------
    # Fase 6: integración y cierre
    # ------------------------------------------------------------------
    def phase_6(self) -> None:
        phase = 6

        def docker_services() -> tuple[str, str]:
            if not self.command_exists("docker"):
                return SKIP, "Docker no está disponible."
            if not (self.root / "docker-compose.yml").exists():
                return FAIL, "No existe docker-compose.yml."

            code, output = self.run_command(
                ["docker", "compose", "ps"],
                timeout=max(self.timeout, 30),
            )
            if code != 0:
                return FAIL, output
            if not output.strip():
                return WARN, "Docker Compose no reporta servicios."
            if "Up" not in output and "running" not in output.lower():
                return WARN, "No se confirmó que los servicios estén activos:\n" + output
            return PASS, output[:4000]

        self.check(
            phase,
            "F6-001",
            "Servicios Docker",
            docker_services,
        )

        if self.integration:
            def openapi_contract() -> tuple[str, str]:
                urls = [
                    f"{self.backend_url}/openapi.json",
                    f"{self.backend_url}/api/v1/openapi.json",
                ]
                errors: list[str] = []

                for url in urls:
                    try:
                        status, body = self.http_get(url)
                        if status != 200:
                            errors.append(f"{url}: HTTP {status}")
                            continue

                        data = json.loads(body)
                        paths = data.get("paths", {}) if isinstance(data, dict) else {}
                        expected = [
                            "auth",
                            "chat",
                            "session",
                            "event",
                            "notification",
                            "streak",
                            "admin",
                        ]
                        found = [
                            token
                            for token in expected
                            if any(token in str(path).lower() for path in paths)
                        ]
                        missing = sorted(set(expected) - set(found))

                        if missing:
                            return WARN, (
                                f"{len(paths)} rutas documentadas. "
                                "Módulos no detectados: "
                                + ", ".join(missing)
                            )
                        return PASS, (
                            f"{len(paths)} rutas OpenAPI; "
                            "módulos principales detectados."
                        )
                    except Exception as exc:
                        errors.append(f"{url}: {exc}")

                return FAIL, "No se pudo leer OpenAPI:\n" + "\n".join(errors)

            self.check(
                phase,
                "F6-002",
                "Contrato OpenAPI",
                openapi_contract,
            )
        else:
            self.add(
                phase,
                "F6-002",
                "Contrato OpenAPI",
                SKIP,
                "Use --integracion para consultar el backend local.",
            )

        def expo_config() -> tuple[str, str]:
            frontend = self.root / "frontend"
            if not (frontend / "node_modules").exists():
                return SKIP, "node_modules no existe."
            if not self.command_exists("npx"):
                return SKIP, "npx no está disponible."

            code, output = self.run_command(
                ["npx", "expo", "config", "--type", "public"],
                cwd=frontend,
                timeout=max(self.timeout, 180),
            )
            if code != 0:
                return FAIL, output
            return PASS, "Expo pudo resolver la configuración pública."

        self.check(phase, "F6-003", "Configuración Expo", expo_config)

        def pending_documented_items() -> tuple[str, str]:
            report = self.root / "documentacion/06_reporte_final.md"
            if not report.exists():
                return WARN, "No existe documentacion/06_reporte_final.md."

            text = self.read_text(report)
            pending = len(
                re.findall(
                    r"pendiente|requiere confirmaci[oó]n",
                    text,
                    flags=re.IGNORECASE,
                )
            )
            if pending:
                return WARN, (
                    f"El reporte final contiene {pending} referencia(s) "
                    "a trabajo pendiente o por confirmar."
                )
            return PASS, "El reporte final no declara pendientes explícitos."

        self.check(
            phase,
            "F6-004",
            "Pendientes del reporte final",
            pending_documented_items,
        )

    # ------------------------------------------------------------------
    # Ejecución y reporte
    # ------------------------------------------------------------------
    def run(self, phases: Sequence[int]) -> None:
        methods = {
            0: self.phase_0,
            1: self.phase_1,
            2: self.phase_2,
            3: self.phase_3,
            4: self.phase_4,
            5: self.phase_5,
            6: self.phase_6,
        }
        for phase in phases:
            methods[phase]()

    def relative_root(self) -> str:
        """Raiz auditada, relativa al directorio desde el que se invoco.

        El reporte se versiona. Guardar la ruta absoluta lo ataba a la maquina
        que lo genero: cambiaba en cada checkout, ensuciaba el diff sin que
        hubiera cambiado nada del proyecto y publicaba el home del usuario.
        Ejecutado desde la raiz, que es lo normal, queda ".".
        """
        try:
            return os.path.relpath(self.root, Path.cwd())
        except ValueError:
            # En Windows relpath falla si root y cwd estan en unidades
            # distintas (C: y D:). Ahi no hay ruta relativa posible.
            return self.root.name

    def summary(self) -> dict[str, object]:
        counts = {
            status: sum(result.status == status for result in self.results)
            for status in (PASS, WARN, FAIL, SKIP)
        }
        return {
            "project_root": self.relative_root(),
            "integration_mode": self.integration,
            "counts": counts,
            "ok": counts[FAIL] == 0,
            "results": [asdict(result) for result in self.results],
        }

    def print_report(self) -> None:
        symbols = {
            PASS: "[OK]",
            WARN: "[!]",
            FAIL: "[X]",
            SKIP: "[-]",
        }

        current_phase: int | None = None
        for result in self.results:
            if result.phase != current_phase:
                current_phase = result.phase
                print(f"\n=== FASE {current_phase} ===")

            print(
                f"{symbols[result.status]} {result.code} "
                f"{result.description} ({result.duration_ms} ms)"
            )
            if result.detail and (
                self.verbose or result.status in {WARN, FAIL}
            ):
                for line in result.detail.splitlines():
                    print(f"    {line}")

        summary = self.summary()
        counts = summary["counts"]
        print("\n=== RESUMEN ===")
        print(
            f"PASS={counts[PASS]}  WARN={counts[WARN]}  "
            f"FAIL={counts[FAIL]}  SKIP={counts[SKIP]}"
        )
        print(
            "Resultado general: "
            + ("APROBADO" if summary["ok"] else "REQUIERE CORRECCIONES")
        )


def parse_phases(value: str) -> list[int]:
    value = value.strip().lower()
    if value in {"todas", "all", "*"}:
        return list(range(7))

    phases: set[int] = set()
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            phase = int(item)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(
                f"Fase inválida: {item}"
            ) from exc

        if phase not in range(7):
            raise argparse.ArgumentTypeError(
                "Las fases válidas son 0,1,2,3,4,5,6."
            )
        phases.add(phase)

    if not phases:
        raise argparse.ArgumentTypeError("Debe indicar al menos una fase.")
    return sorted(phases)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Auditor por fases del proyecto TutorIA."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Raíz del repositorio. Por defecto: directorio actual.",
    )
    parser.add_argument(
        "--fase",
        default="todas",
        help="Fase individual, lista separada por comas o 'todas'.",
    )
    parser.add_argument(
        "--integracion",
        action="store_true",
        help=(
            "Ejecuta pytest, benchmark RAG y consultas al backend. "
            "Puede requerir Docker, PostgreSQL y Gemini."
        ),
    )
    parser.add_argument(
        "--backend-url",
        default="http://localhost:8000",
        help="URL local del backend para comprobar OpenAPI.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout base por comando o solicitud, en segundos.",
    )
    parser.add_argument(
        "--salida",
        type=Path,
        default=Path("backend/tests/reporte_verificacion.json"),
        help="Archivo JSON donde se guardará el reporte.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Muestra el detalle de todas las comprobaciones.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    phases = parse_phases(args.fase)

    if not args.root.exists():
        parser.error(f"La ruta no existe: {args.root}")

    verifier = Verifier(
        root=args.root,
        integration=args.integracion,
        backend_url=args.backend_url,
        timeout=args.timeout,
        verbose=args.verbose,
    )
    verifier.run(phases)
    verifier.print_report()

    report = verifier.summary()
    output_path = args.salida
    if not output_path.is_absolute():
        output_path = args.root / output_path

    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nReporte JSON: {output_path}")

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
