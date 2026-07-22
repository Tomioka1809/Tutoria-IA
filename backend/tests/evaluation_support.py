import asyncio
import hashlib
import inspect
import json
import logging
import os
import re
import shutil
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Tuple

logger = logging.getLogger(__name__)

class InfrastructureError(Exception):
    """Excepción lanzada cuando ocurre un error de infraestructura no recuperable."""
    def __init__(self, message: str, attempts: int = 1, error_type: str = "InfrastructureError"):
        super().__init__(message)
        self.sanitized_message = sanitize_secret_message(message)
        self.attempts = attempts
        self.error_type = error_type

class NonRetryableError(Exception):
    """Excepción lanzada cuando ocurre un error no transitorio que no debe reintentarse."""
    def __init__(self, message: str, attempts: int = 1, error_type: str = "NonRetryableError"):
        super().__init__(message)
        self.sanitized_message = sanitize_secret_message(message)
        self.attempts = attempts
        self.error_type = error_type

def sanitize_secret_message(msg: str) -> str:
    """
    Sanitiza mensajes de error ocultando credenciales en DSNs (PostgreSQL, MySQL, DSNs genéricos),
    incluyendo contraseñas que contienen caracteres como '@', '!', ':', '%', etc.
    Oculta también parámetros sensibles (password, token, secret, api_key) y Bearer tokens,
    conservando esquema, host y puerto.
    """
    if not msg:
        return ""

    def _sanitize_url(match: re.Match) -> str:
        scheme = match.group(1)
        userinfo = match.group(2)
        if ":" in userinfo:
            return f"{scheme}[REDACTED]:[REDACTED]@"
        return f"{scheme}[REDACTED]@"

    # Sanitize userinfo in URLs (greedy match for userinfo up to the last @ before host)
    cleaned = re.sub(
        r'([a-zA-Z0-9\+\-\.]+://)([^/\s]+)@',
        _sanitize_url,
        msg
    )

    # Sanitize parameters (password, passwd, token, secret, api_key, key)
    cleaned = re.sub(
        r'(?:api_key|apikey|token|password|passwd|secret|key)\s*[:=]\s*["\']?[A-Za-z0-9_\-\.]{4,}["\']?',
        '[REDACTED]',
        cleaned,
        flags=re.IGNORECASE
    )

    # Sanitize Bearer tokens
    cleaned = re.sub(
        r'Bearer\s+[A-Za-z0-9_\-\.]+',
        'Bearer [REDACTED]',
        cleaned,
        flags=re.IGNORECASE
    )

    return cleaned

def generate_secure_run_id(manual_id: Optional[str] = None) -> str:
    """
    Genera o valida un run_id seguro.
    Diferencia None (generar automático) de cadenas vacías/espacios (rechazar).
    Rechaza caracteres especiales y separadores de ruta.
    """
    if manual_id is not None:
        cleaned = manual_id.strip()
        if not cleaned:
            raise ValueError("EVAL_RUN_ID no puede estar vacío")
        if len(cleaned) > 64 or not re.match(r'^[A-Za-z0-9_\-\.]+$', cleaned):
            raise ValueError("EVAL_RUN_ID contiene caracteres inválidos o separadores de ruta")
        return cleaned

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    random_hex = uuid.uuid4().hex[:8]
    return f"eval_run_{timestamp}_{random_hex}"

def parse_case_ids(env_str: Optional[str], valid_ids: Optional[set] = None) -> Optional[List[int]]:
    """
    Parsea una cadena de IDs separados por comas.
    Rechaza cadenas vacías intermedias, valores no numéricos, duplicados e IDs inexistentes.
    """
    if env_str is None:
        return None
    raw_str = env_str.strip()
    if not raw_str:
        return None

    tokens = raw_str.split(",")
    parsed_ids: List[int] = []
    seen = set()

    for token in tokens:
        clean = token.strip()
        if not clean:
            raise ValueError(f"Token de ID vacío detectado en EVAL_CASE_IDS: '{env_str}'")
        if not clean.isdigit():
            raise ValueError(f"Token de ID no numérico en EVAL_CASE_IDS: '{clean}'")
        val = int(clean)
        if val in seen:
            raise ValueError(f"ID duplicado en EVAL_CASE_IDS: {val}")
        if valid_ids is not None and val not in valid_ids:
            raise ValueError(f"ID inexistente {val} en EVAL_CASE_IDS")
        seen.add(val)
        parsed_ids.append(val)

    return parsed_ids

def filter_golden_set_cases(
    golden_set: List[Dict[str, Any]],
    case_limit: Optional[int] = None,
    case_ids: Optional[List[int]] = None
) -> List[Dict[str, Any]]:
    """Filtra el Golden Set según el límite de casos o la lista explícita de IDs."""
    valid_ids = {item["id"] for item in golden_set}
    selected = list(golden_set)

    if case_ids is not None:
        invalid_requested = set(case_ids) - valid_ids
        if invalid_requested:
            raise ValueError(f"IDs solicitados inexistentes en Golden Set: {sorted(list(invalid_requested))}")
        selected = [item for item in selected if item["id"] in case_ids]

    if case_limit is not None:
        if case_limit < 0:
            raise ValueError("EVAL_CASE_LIMIT debe ser no negativo")
        selected = selected[:case_limit]

    return selected

def validate_output_directory(
    output_dir_str: Optional[str],
    is_partial: bool,
    repo_root: Path,
    official_dir: Path
) -> Path:
    """
    Valida las políticas de directorio de salida utilizando pathlib.Path.resolve() e is_relative_to().
    Las ejecuciones oficiales escriben solo en official_dir.
    Las ejecuciones parciales exigen EVAL_OUTPUT_DIR fuera de official_dir y dentro de repo_root o /tmp.
    """
    official_dir = official_dir.resolve()
    repo_root = repo_root.resolve()
    tmp_root = Path("/tmp").resolve()

    if not is_partial:
        if output_dir_str:
            target = Path(output_dir_str).resolve()
            if target != official_dir:
                raise ValueError("Una ejecución oficial solo puede escribir en backend/tests/resultados")
        return official_dir

    if not output_dir_str:
        raise ValueError("EVAL_OUTPUT_DIR es obligatorio para ejecuciones parciales")

    target = Path(output_dir_str).resolve()

    if target == official_dir or target.is_relative_to(official_dir):
        raise ValueError("Una ejecución parcial no puede escribir en el directorio oficial ni en sus subdirectorios")

    in_repo = target.is_relative_to(repo_root)
    in_tmp = target.is_relative_to(tmp_root)

    if not (in_repo or in_tmp):
        raise ValueError(f"Ruta de salida '{target}' no permitida fuera del repositorio o /tmp")

    return target

def is_official_complete_run(
    total_cases: int,
    selected_cases: int,
    completed_cases: int,
    infra_errors: int,
    skipped: int,
    is_partial: bool = False
) -> bool:
    """
    Determina si una ejecución es oficial y completa.
    Retorna False si la ejecución fue configurada con filtros (is_partial=True).
    """
    if is_partial:
        return False
    return (
        total_cases == 32 and
        selected_cases == 32 and
        completed_cases == 32 and
        infra_errors == 0 and
        skipped == 0
    )

class EvaluationConfig:
    def __init__(
        self,
        max_retries: Optional[int] = None,
        initial_backoff: Optional[float] = None,
        max_backoff: Optional[float] = None,
        inter_case_delay: Optional[float] = None,
        case_limit: Optional[int] = None,
        case_ids: Optional[List[int]] = None,
        output_dir: Optional[str] = None,
        run_id: Optional[str] = None,
        valid_ids: Optional[set] = None
    ):
        env_retries = os.getenv("EVAL_MAX_RETRIES")
        self.max_retries = max_retries if max_retries is not None else (int(env_retries) if env_retries else 3)
        if self.max_retries < 0:
            raise ValueError("EVAL_MAX_RETRIES debe ser no negativo")

        env_init_backoff = os.getenv("EVAL_INITIAL_BACKOFF_SECONDS")
        self.initial_backoff = initial_backoff if initial_backoff is not None else (float(env_init_backoff) if env_init_backoff else 1.0)
        if self.initial_backoff < 0:
            raise ValueError("EVAL_INITIAL_BACKOFF_SECONDS debe ser no negativo")

        env_max_backoff = os.getenv("EVAL_MAX_BACKOFF_SECONDS")
        self.max_backoff = max_backoff if max_backoff is not None else (float(env_max_backoff) if env_max_backoff else 10.0)
        if self.max_backoff < 0:
            raise ValueError("EVAL_MAX_BACKOFF_SECONDS debe ser no negativo")

        env_delay = os.getenv("EVAL_INTER_CASE_DELAY_SECONDS")
        self.inter_case_delay = inter_case_delay if inter_case_delay is not None else (float(env_delay) if env_delay else 0.5)
        if self.inter_case_delay < 0:
            raise ValueError("EVAL_INTER_CASE_DELAY_SECONDS debe ser no negativo")

        env_limit = os.getenv("EVAL_CASE_LIMIT")
        self.case_limit = case_limit if case_limit is not None else (int(env_limit) if env_limit else None)
        if self.case_limit is not None and self.case_limit < 0:
            raise ValueError("EVAL_CASE_LIMIT debe ser no negativo")

        if case_ids is not None:
            self.case_ids = case_ids
        else:
            self.case_ids = parse_case_ids(os.getenv("EVAL_CASE_IDS"), valid_ids=valid_ids)

        self.output_dir = output_dir or os.getenv("EVAL_OUTPUT_DIR")

        # Explicitly distinguish None from empty string for run_id
        raw_run_id = (
            run_id
            if run_id is not None
            else os.getenv("EVAL_RUN_ID")
        )
        self.run_id = generate_secure_run_id(raw_run_id)

def is_transient_error(exc: Exception) -> bool:
    """
    Determina si un error es transitorio (red, timeout, 429, 500, 502, 503, 504).
    Devuelve False para errores 400, 401, 403 o errores de validación/código.
    """
    if isinstance(exc, (NonRetryableError, InfrastructureError)):
        return False
    if isinstance(exc, (ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError)):
        return False

    status_code = getattr(exc, "status_code", getattr(exc, "code", getattr(exc, "status", None)))
    if status_code in (400, 401, 403):
        return False
    if status_code in (429, 500, 502, 503, 504):
        return True

    if isinstance(exc, (TimeoutError, asyncio.TimeoutError, ConnectionError, OSError)):
        return True

    msg = str(exc).lower()
    non_retryable_terms = ["400", "401", "403", "unauthorized", "forbidden", "invalid_argument", "bad request"]
    if any(term in msg for term in non_retryable_terms):
        return False

    transient_terms = [
        "429", "500", "502", "503", "504", "resource_exhausted",
        "quota", "rate limit", "timeout", "connection", "unavailable",
        "temporarily unavailable", "service unavailable"
    ]
    return any(term in msg for term in transient_terms)

async def execute_with_retry(
    operation: Callable[[], Any],
    config: Optional[EvaluationConfig] = None,
    sleep_fn: Optional[Callable[[float], Any]] = None
) -> Tuple[Any, int]:
    """
    Ejecuta una operación con reintentos adicionales configurados en EVAL_MAX_RETRIES.
    Retorna (resultado, cantidad_real_de_intentos).
    """
    cfg = config or EvaluationConfig()
    sleep = sleep_fn or asyncio.sleep

    max_attempts = 1 + cfg.max_retries
    attempts = 0
    backoff = cfg.initial_backoff

    while attempts < max_attempts:
        attempts += 1
        try:
            if inspect.iscoroutinefunction(operation):
                res = await operation()
            else:
                res = operation()
                if asyncio.iscoroutine(res):
                    res = await res
            return res, attempts
        except Exception as exc:
            sanitized_msg = sanitize_secret_message(str(exc))
            err_type = type(exc).__name__

            if not is_transient_error(exc):
                logger.warning(f"Error no transitorio detectado en intento {attempts}: {err_type} - {sanitized_msg}")
                raise NonRetryableError(sanitized_msg, attempts=attempts, error_type=err_type) from exc

            if attempts >= max_attempts:
                logger.error(f"Reintentos agotados tras {attempts} intentos: {err_type} - {sanitized_msg}")
                raise InfrastructureError(sanitized_msg, attempts=attempts, error_type=err_type) from exc

            wait_time = min(backoff, cfg.max_backoff)
            logger.info(f"Reintento {attempts}/{max_attempts} por error transitorio ({err_type}). Esperando {wait_time:.2f}s...")

            res_sleep = sleep(wait_time)
            if asyncio.iscoroutine(res_sleep):
                await res_sleep
            backoff *= 2.0

def compute_golden_set_hash(golden_set_path: str | Path) -> str:
    """Calcula el hash SHA-256 del archivo Golden Set."""
    with open(golden_set_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def atomic_write_artifact_pair(
    json_path: str | Path,
    json_content: str,
    csv_path: str | Path,
    csv_content: str,
    copy_fn: Callable = shutil.copy2,
    replace_fn: Callable = os.replace
) -> None:
    """
    Escribe conjuntamente y de forma atómica el par JSON y CSV.
    Restaura el estado previo de los archivos tanto si existían como si NO existían originalmente.
    Admite inyección de copy_fn y replace_fn para pruebas de simulación sin interruptores privados.
    """
    j_path = Path(json_path).resolve()
    c_path = Path(csv_path).resolve()

    j_dir = j_path.parent
    c_dir = c_path.parent
    j_dir.mkdir(parents=True, exist_ok=True)
    c_dir.mkdir(parents=True, exist_ok=True)

    json_existed = j_path.exists()
    csv_existed = c_path.exists()

    timestamp_ns = time.time_ns()
    pid = os.getpid()

    j_tmp = j_dir / f"{j_path.name}.tmp.{pid}_{timestamp_ns}"
    c_tmp = c_dir / f"{c_path.name}.tmp.{pid}_{timestamp_ns}"

    j_bak = j_dir / f"{j_path.name}.bak.{pid}_{timestamp_ns}"
    c_bak = c_dir / f"{c_path.name}.bak.{pid}_{timestamp_ns}"

    created_baks: List[Path] = []

    try:
        # Step 1: Write and fsync both temp files
        with open(j_tmp, "w", encoding="utf-8") as f:
            f.write(json_content)
            f.flush()
            os.fsync(f.fileno())

        with open(c_tmp, "w", encoding="utf-8") as f:
            f.write(csv_content)
            f.flush()
            os.fsync(f.fileno())

        # Step 2: Create backups if originals exist (originals remain intact during backup creation)
        if json_existed:
            copy_fn(j_path, j_bak)
            created_baks.append(j_bak)

        if csv_existed:
            copy_fn(c_path, c_bak)
            created_baks.append(c_bak)

        # Step 3: Replace target files with temp files
        try:
            replace_fn(j_tmp, j_path)
            replace_fn(c_tmp, c_path)
        except Exception as replace_err:
            # Rollback targets
            if json_existed and j_bak in created_baks and j_bak.exists():
                replace_fn(j_bak, j_path)
            elif not json_existed and j_path.exists():
                j_path.unlink(missing_ok=True)

            if csv_existed and c_bak in created_baks and c_bak.exists():
                replace_fn(c_bak, c_path)
            elif not csv_existed and c_path.exists():
                c_path.unlink(missing_ok=True)

            raise replace_err

        # Cleanup backup files after success
        for bak in created_baks:
            if bak.exists():
                try:
                    bak.unlink()
                except OSError:
                    pass

        # Sync directory after success
        for d in set([j_dir, c_dir]):
            _sync_dir(d)

    except Exception:
        # Rollback targets if exception happened before or during replace
        if json_existed and j_bak in created_baks and j_bak.exists():
            try:
                replace_fn(j_bak, j_path)
            except OSError:
                pass
        elif not json_existed and j_path.exists():
            j_path.unlink(missing_ok=True)

        if csv_existed and c_bak in created_baks and c_bak.exists():
            try:
                replace_fn(c_bak, c_path)
            except OSError:
                pass
        elif not csv_existed and c_path.exists():
            c_path.unlink(missing_ok=True)

        # Clean up any leftover backup or temp files
        for bak in created_baks:
            if bak.exists():
                try:
                    bak.unlink()
                except OSError:
                    pass

        for tmp_file in (j_tmp, c_tmp):
            if tmp_file.exists():
                try:
                    tmp_file.unlink()
                except OSError:
                    pass

        for d in set([j_dir, c_dir]):
            _sync_dir(d)

        raise

def _sync_dir(dir_path: Path):
    try:
        fd = os.open(dir_path, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except (OSError, AttributeError):
        pass

def compute_retrieval_metrics(
    retrieved_chunks: List[str],
    expected_refs: List[str],
    expected_keywords: List[str],
    categoria: str
) -> Tuple[float, float]:
    """Calcula la Precisión y Cobertura pura para un caso de recuperación."""
    if categoria == "fuera_de_alcance":
        return 1.0, 1.0

    relevant_chunks_count = 0
    matching_refs = set()

    for chunk in retrieved_chunks:
        chunk_lower = chunk.lower()
        for ref in expected_refs:
            ref_clean = ref.replace("Art. ", "").replace(" - Reglamento", "").lower()
            if any(w in chunk_lower for w in ref_clean.split() if len(w) > 3):
                matching_refs.add(ref)

        kw_hits = sum(1 for kw in expected_keywords if kw.lower() in chunk_lower)
        if kw_hits >= 1 or any(ref.lower() in chunk_lower for ref in expected_refs if ref != "NO_APLICA"):
            relevant_chunks_count += 1

    precision = (relevant_chunks_count / len(retrieved_chunks)) if retrieved_chunks else 0.0
    valid_expected_refs = [r for r in expected_refs if r != "NO_APLICA"]
    if valid_expected_refs:
        cobertura = len(matching_refs) / len(valid_expected_refs)
    else:
        cobertura = 1.0 if relevant_chunks_count > 0 else 0.0

    precision = round(min(max(precision, 0.0), 1.0), 4)
    cobertura = round(min(max(cobertura, 0.0), 1.0), 4)
    return precision, cobertura

def compute_generation_metrics(
    bot_response: str,
    expected_keywords: List[str],
    categoria: str
) -> float:
    """Calcula la Pertinencia (Grounding léxico) pura para un caso de generación."""
    bot_response_lower = bot_response.lower()
    if categoria == "fuera_de_alcance":
        refusal_markers = [
            "no tengo esa información",
            "no se encuentra en mi base",
            "no cuento con esa información",
            "base de datos de la universidad"
        ]
        has_refusal = any(marker in bot_response_lower for marker in refusal_markers)
        pertinencia = 1.0 if has_refusal else 0.2
    else:
        keyword_hits = sum(1 for kw in expected_keywords if kw.lower() in bot_response_lower)
        kw_ratio = keyword_hits / len(expected_keywords) if expected_keywords else 1.0
        is_valid_len = len(bot_response) >= 30
        pertinencia = (kw_ratio * 0.7) + (0.3 if is_valid_len else 0.0)

    pertinencia = round(min(max(pertinencia, 0.0), 1.0), 4)
    return pertinencia

def classify_case_result(
    categoria: str,
    cobertura: Optional[float],
    pertinencia: Optional[float],
    technical_error: Optional[str] = None,
    is_skipped: bool = False
) -> str:
    """
    Clasifica semánticamente el resultado funcional de un caso.
    - fuera_de_alcance: success si pertinencia >= 1.0 (se abstuvo); de lo contrario model_failure.
    - facil/ambiguo: model_failure si cobertura == 0 y pertinencia <= 0.3; de lo contrario success.
    """
    if is_skipped:
        return "skipped"
    if technical_error is not None or cobertura is None or pertinencia is None:
        return "infrastructure_error"

    if categoria == "fuera_de_alcance":
        if pertinencia >= 1.0:
            return "success"
        else:
            return "model_failure"
    else:
        if cobertura == 0.0 and pertinencia <= 0.3:
            return "model_failure"
        else:
            return "success"

def calculate_global_metrics(detalles_casos: List[Dict[str, Any]]) -> Tuple[Dict[str, float], Dict[str, Any]]:
    """
    Calcula métricas globales y por categoría excluyendo casos con errores de infraestructura o skipped.
    """
    evaluables = [
        c for c in detalles_casos
        if c.get("status") in ("success", "model_failure") or
           ("status" not in c and c.get("precision") is not None)
    ]

    if not evaluables:
        globales = {"precision_global": 0.0, "cobertura_global": 0.0, "pertinencia_global": 0.0}
        return globales, {}

    avg_prec = sum(c["precision"] for c in evaluables if c.get("precision") is not None) / len(evaluables)
    avg_cob = sum(c["cobertura"] for c in evaluables if c.get("cobertura") is not None) / len(evaluables)
    avg_pert = sum(c["pertinencia"] for c in evaluables if c.get("pertinencia") is not None) / len(evaluables)

    globales = {
        "precision_global": round(avg_prec, 4),
        "cobertura_global": round(avg_cob, 4),
        "pertinencia_global": round(avg_pert, 4)
    }

    cat_groups: Dict[str, List[Dict[str, Any]]] = {}
    for c in evaluables:
        cat = c["categoria"]
        if cat not in cat_groups:
            cat_groups[cat] = []
        cat_groups[cat].append(c)

    desglose = {}
    for cat_name, cases in cat_groups.items():
        n = len(cases)
        c_prec = sum(c["precision"] for c in cases if c.get("precision") is not None) / n if n > 0 else 0.0
        c_cob = sum(c["cobertura"] for c in cases if c.get("cobertura") is not None) / n if n > 0 else 0.0
        c_pert = sum(c["pertinencia"] for c in cases if c.get("pertinencia") is not None) / n if n > 0 else 0.0
        desglose[cat_name] = {
            "total_casos": n,
            "precision": round(c_prec, 4),
            "cobertura": round(c_cob, 4),
            "pertinencia": round(c_pert, 4)
        }

    return globales, desglose
