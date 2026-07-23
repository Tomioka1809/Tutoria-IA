import asyncio
import hashlib
import inspect
import json
import logging
import math
import os
import re
import shutil
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Tuple

from app.application.ports.llm_port import LLMPort
from app.infrastructure.adapters.gemini_adapter import GeminiAdapter

logger = logging.getLogger(__name__)

class InfrastructureError(Exception):
    """Excepción lanzada cuando ocurre un error de infraestructura no recuperable."""
    def __init__(self, message: str, attempts: int = 1, error_type: str = "InfrastructureError"):
        super().__init__(message)
        self.sanitized_message = truncate_technical_error(message)
        self.attempts = attempts
        self.error_type = error_type

class NonRetryableError(Exception):
    """Excepción lanzada cuando ocurre un error no transitorio que no debe reintentarse."""
    def __init__(self, message: str, attempts: int = 1, error_type: str = "NonRetryableError"):
        super().__init__(message)
        self.sanitized_message = truncate_technical_error(message)
        self.attempts = attempts
        self.error_type = error_type

def derive_case_eval_identity(run_id: str, case_id: int) -> Dict[str, str]:
    """
    Función pura para derivar la identidad temporal determinista de cada caso de prueba.
    Garantiza aislamiento total entre ejecuciones y entre casos.
    student_code incluye el token completo de 12 caracteres (longitud total: 18 caracteres).
    """
    token = hashlib.sha256(run_id.encode("utf-8")).hexdigest()[:12]
    email = f"eval_temp_{token}_{case_id}@eval.unsaac.edu.pe"
    student_code = f"EV{token}{case_id:04d}"
    full_name = f"EVAL {token} CASE {case_id}"
    marker = f"eval_run_{token}"

    return {
        "token": token,
        "email": email,
        "student_code": student_code,
        "full_name": full_name,
        "marker": marker,
        "role": "estudiante"
    }

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

    cleaned = re.sub(
        r'([a-zA-Z0-9\+\-\.]+://)([^/\s]+)@',
        _sanitize_url,
        msg
    )

    cleaned = re.sub(
        r'(?:api_key|apikey|token|password|passwd|secret|key)\s*[:=]\s*["\']?[A-Za-z0-9_\-\.]{4,}["\']?',
        '[REDACTED]',
        cleaned,
        flags=re.IGNORECASE
    )

    cleaned = re.sub(
        r'Bearer\s+[A-Za-z0-9_\-\.]+',
        'Bearer [REDACTED]',
        cleaned,
        flags=re.IGNORECASE
    )

    return cleaned

def truncate_technical_error(msg: str, max_len: int = 300) -> str:
    """
    Sanitiza y limita el mensaje técnico a una longitud razonable sin cortar secretos parcialmente
    ni incluir payloads pesados, links o metadata del SDK de Gemini.
    """
    if not msg:
        return ""

    cleaned = sanitize_secret_message(msg)

    # Filter out verbose SDK JSON payloads, metadata and links
    cleaned = re.sub(r'https?://\S+', '[LINK_REDACTED]', cleaned)
    cleaned = re.sub(r'quotaFailure\s*\{[^}]*\}', '[QUOTA_FAILURE_DETAILS]', cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'metadata\s*\{[^}]*\}', '[METADATA_REDACTED]', cleaned, flags=re.DOTALL)

    if len(cleaned) <= max_len:
        return cleaned

    truncated = cleaned[:max_len]
    last_space = truncated.rfind(" ")
    if last_space > max_len // 2:
        truncated = truncated[:last_space]

    return truncated + " ... [TRUNCATED]"

def extract_retry_delay(exc_or_msg: Any) -> Optional[float]:
    """Extrae la recomendación de espera (RetryInfo) de representaciones del SDK o cadenas de error."""
    msg = str(exc_or_msg)
    patterns = [
        r'[\'"]?retryDelay[\'"]?\s*:\s*[\'"]?(\d+(?:\.\d+)?)s?[\'"]?',
        r'(?:retry\s+in|retrydelay:?|retry_after:?)\s*(\d+(?:\.\d+)?)s?',
        r'retry\s+after\s+(\d+(?:\.\d+)?)s?'
    ]
    for pattern in patterns:
        match = re.search(pattern, msg, re.IGNORECASE)
        if match:
            try:
                val = float(match.group(1))
                if math.isfinite(val) and val >= 0:
                    return val
            except ValueError:
                pass
    return None

def classify_error_category(exc: Exception) -> str:
    """Clasifica una excepción en una categoría de diagnóstico concisa."""
    msg = str(exc).lower()
    if "429" in msg or "resource_exhausted" in msg or "quota" in msg:
        return "gemini_quota_exceeded_429"
    if "503" in msg or "unavailable" in msg:
        return "gemini_service_unavailable_503"
    if isinstance(exc, (TimeoutError, asyncio.TimeoutError)) or "timeout" in msg:
        return "timeout"
    if "401" in msg or "403" in msg or "api_key" in msg or "unauthorized" in msg:
        return "authentication_error"
    if "database" in msg or "psycopg" in msg or "sqlalchemy" in msg or "connection refused" in msg:
        return "database_error"
    return "unexpected_infrastructure_error"

def generate_secure_run_id(manual_id: Optional[str] = None) -> str:
    """Genera o valida un run_id seguro."""
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
    """Parsea una cadena de IDs separados por comas."""
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
    """Valida las políticas de directorio de salida."""
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
    """Determina si una ejecución es oficial y completa."""
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
        generation_min_interval: Optional[float] = None,
        retry_after_safety: Optional[float] = None,
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

        env_gen_interval = os.getenv("EVAL_GENERATION_MIN_INTERVAL_SECONDS")
        raw_gen_interval = generation_min_interval if generation_min_interval is not None else (float(env_gen_interval) if env_gen_interval else 15.0)
        if type(raw_gen_interval) is bool or not isinstance(raw_gen_interval, (int, float)) or not math.isfinite(raw_gen_interval) or raw_gen_interval < 0:
            raise ValueError("EVAL_GENERATION_MIN_INTERVAL_SECONDS debe ser un número finito mayor o igual a 0")
        self.generation_min_interval = float(raw_gen_interval)

        env_safety = os.getenv("EVAL_RETRY_AFTER_SAFETY_SECONDS")
        raw_safety = retry_after_safety if retry_after_safety is not None else (float(env_safety) if env_safety else 2.0)
        if type(raw_safety) is bool or not isinstance(raw_safety, (int, float)) or not math.isfinite(raw_safety) or raw_safety < 0:
            raise ValueError("EVAL_RETRY_AFTER_SAFETY_SECONDS debe ser un número finito mayor o igual a 0")
        self.retry_after_safety = float(raw_safety)

        env_limit = os.getenv("EVAL_CASE_LIMIT")
        self.case_limit = case_limit if case_limit is not None else (int(env_limit) if env_limit else None)
        if self.case_limit is not None and self.case_limit < 0:
            raise ValueError("EVAL_CASE_LIMIT debe ser no negativo")

        if case_ids is not None:
            self.case_ids = case_ids
        else:
            self.case_ids = parse_case_ids(os.getenv("EVAL_CASE_IDS"), valid_ids=valid_ids)

        self.output_dir = output_dir or os.getenv("EVAL_OUTPUT_DIR")

        raw_run_id = (
            run_id
            if run_id is not None
            else os.getenv("EVAL_RUN_ID")
        )
        self.run_id = generate_secure_run_id(raw_run_id)

def is_transient_error(exc: Exception) -> bool:
    """Determina si un error es transitorio."""
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
    non_retryable_terms = [
        "400", "401", "403", "unauthorized", "forbidden", "invalid_argument",
        "api_key_invalid", "api key not valid", "bad request"
    ]
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
    """Ejecuta una operación con reintentos adicionales configurados."""
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
            trunc_msg = truncate_technical_error(str(exc))
            err_type = type(exc).__name__
            err_cat = classify_error_category(exc)

            if not is_transient_error(exc):
                logger.warning("Error no transitorio: %s (%s) en intento %d: %s", err_cat, err_type, attempts, trunc_msg)
                raise NonRetryableError(trunc_msg, attempts=attempts, error_type=err_type) from exc

            if attempts >= max_attempts:
                logger.error("Reintentos agotados tras %d intentos: %s (%s)", attempts, err_cat, err_type)
                raise InfrastructureError(trunc_msg, attempts=attempts, error_type=err_type) from exc

            retry_after = extract_retry_delay(exc)
            if retry_after is not None:
                wait_time = max(backoff, retry_after + cfg.retry_after_safety)
            else:
                wait_time = min(backoff, cfg.max_backoff)

            logger.info("Error transitorio: %s (intento %d/%d, espera %.1fs)", err_cat, attempts, max_attempts, wait_time)

            res_sleep = sleep(wait_time)
            if asyncio.iscoroutine(res_sleep):
                await res_sleep
            backoff *= 2.0

class GeminiRateLimiter:
    """Limitador de cuota serializado para solicitudes de generación de Gemini."""
    def __init__(
        self,
        min_interval_seconds: float = 15.0,
        time_fn: Optional[Callable[[], float]] = None,
        sleep_fn: Optional[Callable[[float], Any]] = None
    ):
        if type(min_interval_seconds) is bool or not isinstance(min_interval_seconds, (int, float)) or not math.isfinite(min_interval_seconds) or min_interval_seconds < 0:
            raise ValueError("min_interval_seconds debe ser un número finito mayor o igual a 0")
        self.min_interval = float(min_interval_seconds)
        self._lock = asyncio.Lock()
        self.last_request_time: Optional[float] = None
        self.time_fn = time_fn or time.monotonic
        self.sleep_fn = sleep_fn or asyncio.sleep

    async def wait_if_needed(self):
        async with self._lock:
            now = self.time_fn()
            if self.last_request_time is not None and self.min_interval > 0:
                elapsed = now - self.last_request_time
                if elapsed < self.min_interval:
                    wait_sec = self.min_interval - elapsed
                    res = self.sleep_fn(wait_sec)
                    if asyncio.iscoroutine(res) or inspect.iscoroutine(res):
                        await res
            self.last_request_time = self.time_fn()

class EvaluationGeminiAdapter(LLMPort):
    """
    Adaptador de evaluación para el banco de pruebas RAG.
    Incrementa generation_requests solo DESPUÉS de completar la espera en el limitador.
    """
    def __init__(
        self,
        api_key: str,
        config: Optional[EvaluationConfig] = None,
        sleep_fn: Optional[Callable[[float], Any]] = None,
        rate_limiter: Optional[GeminiRateLimiter] = None
    ):
        self.config = config or EvaluationConfig()
        self.sleep_fn = sleep_fn
        self.rate_limiter = rate_limiter or GeminiRateLimiter(
            min_interval_seconds=self.config.generation_min_interval,
            sleep_fn=sleep_fn
        )

        async def _on_before_generate():
            if self.rate_limiter:
                await self.rate_limiter.wait_if_needed()
            self.generation_requests += 1

        self.adapter = GeminiAdapter(
            api_key=api_key,
            allow_embedding_fallback=False,
            allow_generation_fallback=False,
            api_max_attempts=1,
            before_generate_request=_on_before_generate
        )
        self.reset_attempt_counters()

    def reset_attempt_counters(self):
        self.last_embedding_attempts = 0
        self.last_generation_attempts = 0
        self.embedding_requests = 0
        self.generation_requests = 0

    async def compute_embedding(self, text: str) -> List[float]:
        async def _op():
            self.embedding_requests += 1
            return await self.adapter.compute_embedding(text)

        try:
            res, attempts = await execute_with_retry(
                _op,
                config=self.config,
                sleep_fn=self.sleep_fn
            )
            self.last_embedding_attempts = attempts
            return res
        except (InfrastructureError, NonRetryableError) as e:
            self.last_embedding_attempts = e.attempts
            raise e
        except Exception as e:
            self.last_embedding_attempts = getattr(e, "attempts", 1)
            raise e

    async def generate_response(
        self,
        system_instruction: str,
        history: List[Dict],
        user_message: str,
        tools: List = None
    ) -> str:
        async def _op():
            return await self.adapter.generate_response(
                system_instruction=system_instruction,
                history=history,
                user_message=user_message,
                tools=tools
            )

        try:
            res, attempts = await execute_with_retry(
                _op,
                config=self.config,
                sleep_fn=self.sleep_fn
            )
            self.last_generation_attempts = attempts
            return res
        except (InfrastructureError, NonRetryableError) as e:
            self.last_generation_attempts = e.attempts
            raise e
        except Exception as e:
            self.last_generation_attempts = getattr(e, "attempts", 1)
            raise e

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
    """Escribe conjuntamente y de forma atómica el par JSON y CSV."""
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
        with open(j_tmp, "w", encoding="utf-8") as f:
            f.write(json_content)
            f.flush()
            os.fsync(f.fileno())

        with open(c_tmp, "w", encoding="utf-8") as f:
            f.write(csv_content)
            f.flush()
            os.fsync(f.fileno())

        if json_existed:
            copy_fn(j_path, j_bak)
            created_baks.append(j_bak)

        if csv_existed:
            copy_fn(c_path, c_bak)
            created_baks.append(c_bak)

        try:
            replace_fn(j_tmp, j_path)
            replace_fn(c_tmp, c_path)
        except Exception as replace_err:
            if json_existed and j_bak in created_baks and j_bak.exists():
                replace_fn(j_bak, j_path)
            elif not json_existed and j_path.exists():
                j_path.unlink(missing_ok=True)

            if csv_existed and c_bak in created_baks and c_bak.exists():
                replace_fn(c_bak, c_path)
            elif not csv_existed and c_path.exists():
                c_path.unlink(missing_ok=True)

            raise replace_err

        for bak in created_baks:
            if bak.exists():
                try:
                    bak.unlink()
                except OSError:
                    pass

        for d in set([j_dir, c_dir]):
            _sync_dir(d)

    except Exception:
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
    """Clasifica semánticamente el resultado funcional de un caso."""
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
    """Calcula métricas globales y por categoría excluyendo casos con errores de infraestructura o skipped."""
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
