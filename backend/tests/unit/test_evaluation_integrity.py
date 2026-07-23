import json
import os
import io
import csv
import tempfile
import pytest
import shutil
import asyncio
import unittest.mock
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, call

from app.application.dtos.rag_dtos import RAGRetrievalPolicy, RetrievedChunkDTO
from app.application.use_cases.chat_use_cases import ChatUseCase
from app.infrastructure.adapters.gemini_adapter import GeminiAdapter

from tests.test_retrieval import RetrievalEvaluator, run_retrieval_benchmark
from tests.test_generation import GenerationEvaluator, run_generation_benchmark
from tests.run_eval import build_export_payloads

from tests.evaluation_support import (
    EvaluationConfig,
    EvaluationGeminiAdapter,
    GeminiRateLimiter,
    derive_case_eval_identity,
    truncate_technical_error,
    extract_retry_delay,
    execute_with_retry,
    is_transient_error,
    sanitize_secret_message,
    generate_secure_run_id,
    compute_golden_set_hash,
    atomic_write_artifact_pair,
    calculate_global_metrics,
    parse_case_ids,
    filter_golden_set_cases,
    validate_output_directory,
    is_official_complete_run,
    classify_case_result,
    InfrastructureError,
    NonRetryableError
)

from tests.verify_evaluation_integrity import (
    validate_global_metrics,
    validate_category_breakdown,
    validate_case_coherence
)

# 1. Retry exitoso y número de intentos
def test_retry_success_and_attempts():
    async def _run():
        calls_count = 0
        async def mock_op():
            nonlocal calls_count
            calls_count += 1
            if calls_count < 3:
                raise ConnectionError("503 Service Unavailable")
            return "SUCCESS"

        sleep_mock = AsyncMock()
        cfg = EvaluationConfig(max_retries=3, initial_backoff=0.01)
        res, attempts = await execute_with_retry(mock_op, config=cfg, sleep_fn=sleep_mock)

        assert res == "SUCCESS"
        assert attempts == 3
        assert calls_count == 3
    asyncio.run(_run())

# 2. InfrastructureError conserva attempts
def test_infrastructure_error_retains_attempts():
    async def _run():
        calls_count = 0
        async def mock_op():
            nonlocal calls_count
            calls_count += 1
            raise ConnectionError("500 Internal Server Error")

        sleep_mock = AsyncMock()
        cfg = EvaluationConfig(max_retries=2, initial_backoff=0.01)

        with pytest.raises(InfrastructureError) as exc_info:
            await execute_with_retry(mock_op, config=cfg, sleep_fn=sleep_mock)

        err = exc_info.value
        assert err.attempts == 3  # 1 initial + 2 retries = 3
        assert "500" in err.sanitized_message
        assert err.error_type == "ConnectionError"
    asyncio.run(_run())

# 3. NonRetryableError conserva attempts
def test_non_retryable_error_retains_attempts():
    async def _run():
        async def mock_fail():
            raise ValueError("Formato de consulta inválido")

        cfg = EvaluationConfig(max_retries=3)

        with pytest.raises(NonRetryableError) as exc_info:
            await execute_with_retry(mock_fail, config=cfg)

        err = exc_info.value
        assert err.attempts == 1
        assert "Formato" in err.sanitized_message
        assert err.error_type == "ValueError"
    asyncio.run(_run())

# 4. 401 no se reintenta
def test_401_no_retry():
    async def _run():
        async def mock_401():
            err = Exception("HTTP 401 Unauthorized")
            err.status_code = 401
            raise err

        cfg = EvaluationConfig(max_retries=3)
        with pytest.raises(NonRetryableError) as exc_info:
            await execute_with_retry(mock_401, config=cfg)

        assert exc_info.value.attempts == 1
    asyncio.run(_run())

# 5. Parsing válido de IDs
def test_valid_case_ids_parsing():
    parsed = parse_case_ids("1, 2, 5, 10", valid_ids={1, 2, 5, 10, 15})
    assert parsed == [1, 2, 5, 10]

# 6. Token vacío rechazado
def test_empty_token_rejected():
    with pytest.raises(ValueError):
        parse_case_ids("1, , 3")

# 7. Token no numérico rechazado
def test_non_numeric_token_rejected():
    with pytest.raises(ValueError):
        parse_case_ids("1, abc, 3")

# 8. Duplicado rechazado
def test_duplicate_id_rejected():
    with pytest.raises(ValueError):
        parse_case_ids("1, 2, 1")

# 9. ID inexistente rechazado
def test_non_existent_id_rejected():
    with pytest.raises(ValueError):
        parse_case_ids("1, 99", valid_ids={1, 2, 3})

# 10. CASE_LIMIT=32 sigue siendo ejecución parcial
def test_case_limit_15_is_partial():
    cfg = EvaluationConfig(case_limit=15)
    is_partial = (cfg.case_limit is not None or cfg.case_ids is not None)
    assert is_partial is True
    assert is_official_complete_run(15, 15, 15, 0, 0, is_partial=is_partial) is False

# 11. CASE_IDS con todos los 32 IDs sigue siendo parcial
def test_case_ids_all_15_is_partial():
    all_32 = list(range(1, 33))
    cfg = EvaluationConfig(case_ids=all_32)
    is_partial = (cfg.case_limit is not None or cfg.case_ids is not None)
    assert is_partial is True
    assert is_official_complete_run(15, 15, 15, 0, 0, is_partial=is_partial) is False

# 12. Sin filtros puede ser oficial
def test_no_filters_can_be_official():
    cfg = EvaluationConfig(case_limit=None, case_ids=None)
    is_partial = (cfg.case_limit is not None or cfg.case_ids is not None)
    assert is_partial is False
    assert is_official_complete_run(15, 15, 15, 0, 0, is_partial=is_partial) is True

# 13. Directorio oficial rechazado para filtros
def test_official_dir_rejected_for_filters():
    repo_root = Path("/app").resolve()
    official_dir = Path("/app/backend/tests/resultados").resolve()
    with pytest.raises(ValueError) as exc_info:
        validate_output_directory(output_dir_str=str(official_dir), is_partial=True, repo_root=repo_root, official_dir=official_dir)
    assert "directorio oficial" in str(exc_info.value)

# 14. Subdirectorio oficial rechazado
def test_official_subdir_rejected_for_filters():
    repo_root = Path("/app").resolve()
    official_dir = Path("/app/backend/tests/resultados").resolve()
    subdir = official_dir / "partial_test"
    with pytest.raises(ValueError) as exc_info:
        validate_output_directory(output_dir_str=str(subdir), is_partial=True, repo_root=repo_root, official_dir=official_dir)
    assert "subdirectorios" in str(exc_info.value)

# 15. Directorio temporal aceptado
def test_valid_temp_dir_accepted():
    repo_root = Path("/app").resolve()
    official_dir = Path("/app/backend/tests/resultados").resolve()
    tmp_target = Path("/tmp/eval_run_test")
    res = validate_output_directory(output_dir_str=str(tmp_target), is_partial=True, repo_root=repo_root, official_dir=official_dir)
    assert res == tmp_target.resolve()

# 16. success classification
def test_classification_success():
    res = classify_case_result(categoria="facil", cobertura=1.0, pertinencia=0.8)
    assert res == "success"

# 17. model_failure interno
def test_classification_model_failure_internal():
    res = classify_case_result(categoria="facil", cobertura=0.0, pertinencia=0.3)
    assert res == "model_failure"

# 18. model_failure fuera de alcance
def test_classification_model_failure_fuera_de_alcance():
    res = classify_case_result(categoria="fuera_de_alcance", cobertura=1.0, pertinencia=0.2)
    assert res == "model_failure"

# 19. infrastructure_error classification
def test_classification_infrastructure_error():
    res = classify_case_result(categoria="facil", cobertura=None, pertinencia=None, technical_error="503 Error")
    assert res == "infrastructure_error"

# 20. skipped classification
def test_classification_skipped():
    res = classify_case_result(categoria="facil", cobertura=None, pertinencia=None, is_skipped=True)
    assert res == "skipped"

# 21. Exclusión de errores técnicos de métricas
def test_metrics_exclude_technical_errors():
    detalles = [
        {"id": 1, "categoria": "facil", "status": "success", "precision": 1.0, "cobertura": 1.0, "pertinencia": 1.0},
        {"id": 2, "categoria": "facil", "status": "infrastructure_error", "precision": None, "cobertura": None, "pertinencia": None}
    ]
    globales, _ = calculate_global_metrics(detalles)
    assert globales["precision_global"] == 1.0
    assert globales["cobertura_global"] == 1.0
    assert globales["pertinencia_global"] == 1.0

# 22. Escritura conjunta exitosa
def test_atomic_write_artifact_pair_success():
    with tempfile.TemporaryDirectory() as tmp_dir:
        j_path = Path(tmp_dir) / "eval_results.json"
        c_path = Path(tmp_dir) / "eval_results.csv"

        atomic_write_artifact_pair(j_path, '{"a": 1}', c_path, "ID,Val\n1,2")

        assert j_path.exists()
        assert c_path.exists()
        assert j_path.read_text(encoding="utf-8") == '{"a": 1}'
        assert c_path.read_text(encoding="utf-8") == "ID,Val\n1,2"

# 23. Fallo del segundo respaldo mantiene originales intactos
def test_atomic_write_failure_during_backup2_keeps_originals():
    with tempfile.TemporaryDirectory() as tmp_dir:
        j_path = Path(tmp_dir) / "eval_results.json"
        c_path = Path(tmp_dir) / "eval_results.csv"

        j_path.write_text('{"orig_json": true}', encoding="utf-8")
        c_path.write_text("orig_csv\n1", encoding="utf-8")

        copy_calls = 0
        def failing_copy(src, dst):
            nonlocal copy_calls
            copy_calls += 1
            if copy_calls == 2:
                raise RuntimeError("Failed on 2nd copy")
            shutil.copy2(src, dst)

        with pytest.raises(RuntimeError):
            atomic_write_artifact_pair(
                j_path, '{"new_json": true}',
                c_path, "new_csv\n2",
                copy_fn=failing_copy
            )

        assert j_path.read_text(encoding="utf-8") == '{"orig_json": true}'
        assert c_path.read_text(encoding="utf-8") == "orig_csv\n1"

# 24. Fallo en el primer reemplazo restaura originales
def test_atomic_write_failure_during_replace1_restores_originals():
    with tempfile.TemporaryDirectory() as tmp_dir:
        j_path = Path(tmp_dir) / "eval_results.json"
        c_path = Path(tmp_dir) / "eval_results.csv"

        j_path.write_text('{"orig_json": true}', encoding="utf-8")
        c_path.write_text("orig_csv\n1", encoding="utf-8")

        def failing_replace(src, dst):
            raise RuntimeError("Failed on 1st replace")

        with pytest.raises(RuntimeError):
            atomic_write_artifact_pair(
                j_path, '{"new_json": true}',
                c_path, "new_csv\n2",
                replace_fn=failing_replace
            )

        assert j_path.read_text(encoding="utf-8") == '{"orig_json": true}'
        assert c_path.read_text(encoding="utf-8") == "orig_csv\n1"

# 25. Fallo en el segundo reemplazo restaura originales
def test_atomic_write_failure_during_replace2_restores_originals():
    with tempfile.TemporaryDirectory() as tmp_dir:
        j_path = Path(tmp_dir) / "eval_results.json"
        c_path = Path(tmp_dir) / "eval_results.csv"

        j_path.write_text('{"orig_json": true}', encoding="utf-8")
        c_path.write_text("orig_csv\n1", encoding="utf-8")

        replace_calls = 0
        def failing_replace2(src, dst):
            nonlocal replace_calls
            replace_calls += 1
            if replace_calls == 2:
                raise RuntimeError("Failed on 2nd replace")
            os.replace(src, dst)

        with pytest.raises(RuntimeError):
            atomic_write_artifact_pair(
                j_path, '{"new_json": true}',
                c_path, "new_csv\n2",
                replace_fn=failing_replace2
            )

        assert j_path.read_text(encoding="utf-8") == '{"orig_json": true}'
        assert c_path.read_text(encoding="utf-8") == "orig_csv\n1"

# 26. No quedan temporales ni respaldos tras éxito o error
def test_no_leftover_tmp_or_bak_files():
    with tempfile.TemporaryDirectory() as tmp_dir:
        j_path = Path(tmp_dir) / "eval_results.json"
        c_path = Path(tmp_dir) / "eval_results.csv"

        atomic_write_artifact_pair(j_path, '{"a": 1}', c_path, "ID,Val\n1,2")

        leftovers = list(Path(tmp_dir).glob("*.tmp*")) + list(Path(tmp_dir).glob("*.bak*"))
        assert len(leftovers) == 0

        replace_calls = 0
        def failing_replace2(src, dst):
            nonlocal replace_calls
            replace_calls += 1
            if replace_calls == 2:
                raise RuntimeError("Failed on 2nd replace")
            os.replace(src, dst)

        with pytest.raises(RuntimeError):
            atomic_write_artifact_pair(j_path, '{"a": 2}', c_path, "ID,Val\n2,2", replace_fn=failing_replace2)

        leftovers = list(Path(tmp_dir).glob("*.tmp*")) + list(Path(tmp_dir).glob("*.bak*"))
        assert len(leftovers) == 0

# 27. Sanitización DSN PostgreSQL con arroba en la contraseña
def test_sanitization_postgresql_with_at_symbol():
    msg = "Error connecting to postgresql://admin_user:P@ssword123!@localhost:5432/tutoria_db"
    clean = sanitize_secret_message(msg)
    assert "admin_user" not in clean
    assert "P@ssword123!" not in clean
    assert "ssword123" not in clean
    assert "postgresql://[REDACTED]:[REDACTED]@localhost:5432/tutoria_db" in clean

# 28. Sanitización URL MySQL
def test_sanitization_mysql_url_encoded():
    msg = "Access denied for mysql://user%20name:pass%40123@127.0.0.1:3306/db"
    clean = sanitize_secret_message(msg)
    assert "user%20name" not in clean
    assert "pass%40123" not in clean
    assert "mysql://[REDACTED]:[REDACTED]@127.0.0.1:3306/db" in clean

# 29. Sanitización Bearer y API key
def test_sanitization_bearer_and_api_key():
    msg = "Failed request api_key='AIzaSyC123456789' and Bearer eyJhbGciOiJIUzI1NiIn0"
    clean = sanitize_secret_message(msg)
    assert "AIzaSyC123456789" not in clean
    assert "eyJhbGciOiJIUzI1NiIn0" not in clean
    assert "[REDACTED]" in clean

# 30. run_id automático no colisiona
def test_automatic_run_id_uniqueness():
    id1 = generate_secure_run_id()
    id2 = generate_secure_run_id()
    assert id1 != id2
    assert id1.startswith("eval_run_")
    assert len(id1) > 20

# 31. run_id manual inválido se rechaza
def test_manual_run_id_validation():
    assert generate_secure_run_id("valid_run-1.0") == "valid_run-1.0"
    with pytest.raises(ValueError):
        generate_secure_run_id("   ")
    with pytest.raises(ValueError):
        generate_secure_run_id("../invalid_path")
    with pytest.raises(ValueError):
        generate_secure_run_id("invalid/id")

# 32. Hash SHA-256 estable
def test_sha256_hash_stability():
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as f:
        f.write('{"test": 1}')
        t_name = f.name

    try:
        h1 = compute_golden_set_hash(t_name)
        h2 = compute_golden_set_hash(t_name)
        assert h1 == h2
        assert len(h1) == 64
    finally:
        os.remove(t_name)

# 33. Recomputación global
def test_global_metrics_recomputation():
    detalles = [
        {"id": 1, "categoria": "facil", "status": "success", "precision": 0.5, "cobertura": 0.8, "pertinencia": 1.0},
        {"id": 2, "categoria": "facil", "status": "success", "precision": 0.5, "cobertura": 0.2, "pertinencia": 0.6}
    ]
    globales, _ = calculate_global_metrics(detalles)
    assert globales["precision_global"] == 0.5
    assert globales["cobertura_global"] == 0.5
    assert globales["pertinencia_global"] == 0.8

# 34. Recomputación por categoría
def test_category_breakdown_recomputation():
    detalles = [
        {"id": 1, "categoria": "facil", "status": "success", "precision": 1.0, "cobertura": 1.0, "pertinencia": 1.0},
        {"id": 2, "categoria": "ambiguo", "status": "success", "precision": 0.5, "cobertura": 0.5, "pertinencia": 0.5}
    ]
    _, desglose = calculate_global_metrics(detalles)
    assert desglose["facil"]["total_casos"] == 1
    assert desglose["facil"]["precision"] == 1.0
    assert desglose["ambiguo"]["total_casos"] == 1
    assert desglose["ambiguo"]["precision"] == 0.5

# 35. Empty run_id in EvaluationConfig
def test_empty_run_id_in_evaluation_config():
    with pytest.raises(ValueError):
        EvaluationConfig(run_id="")
    with pytest.raises(ValueError):
        EvaluationConfig(run_id="   ")

    os.environ["EVAL_RUN_ID"] = ""
    try:
        with pytest.raises(ValueError):
            EvaluationConfig()
    finally:
        os.environ.pop("EVAL_RUN_ID", None)

# 36. Replacement failure without previous target files leaves neither JSON nor CSV
def test_atomic_write_replace_failure_without_previous_targets_leaves_no_files():
    with tempfile.TemporaryDirectory() as tmp_dir:
        j_path = Path(tmp_dir) / "eval_results.json"
        c_path = Path(tmp_dir) / "eval_results.csv"

        replace_calls = 0
        def failing_replace2(src, dst):
            nonlocal replace_calls
            replace_calls += 1
            if replace_calls == 2:
                raise RuntimeError("Failed 2nd replace")
            os.replace(src, dst)

        with pytest.raises(RuntimeError):
            atomic_write_artifact_pair(
                j_path, '{"new": true}',
                c_path, "new_csv\n1",
                replace_fn=failing_replace2
            )

        assert not j_path.exists()
        assert not c_path.exists()
        leftovers = list(Path(tmp_dir).glob("*.tmp*")) + list(Path(tmp_dir).glob("*.bak*"))
        assert len(leftovers) == 0

# === PRUEBAS UNITARIAS DE FUNCIONES PURAS DEL VERIFICADOR ===

# 37. Preguntas iguales: aprobación
def test_case_coherence_equal_questions_pass():
    g = {"id": 1, "categoria": "facil", "pregunta": "¿Cuál es el horario?"}
    j = {"id": 1, "categoria": "facil", "pregunta": "¿Cuál es el horario?", "status": "success", "attempts": 1, "technical_error": None, "precision": 1.0, "cobertura": 1.0, "pertinencia": 1.0}
    c_new = ["1", "facil", "success", "1", "", "¿Cuál es el horario?", "1.0", "1.0", "1.0", "Respuesta"]

    errs = validate_case_coherence(g, j, c_new, is_new_format=True)
    assert errs == []

# 38. Pregunta JSON diferente al Golden Set: rechazo
def test_case_coherence_json_question_mismatch_reject():
    g = {"id": 1, "categoria": "facil", "pregunta": "¿Cuál es el horario?"}
    j = {"id": 1, "categoria": "facil", "pregunta": "¿Cuál es el horario alterado?", "status": "success", "attempts": 1, "technical_error": None, "precision": 1.0, "cobertura": 1.0, "pertinencia": 1.0}
    c_new = ["1", "facil", "success", "1", "", "¿Cuál es el horario?", "1.0", "1.0", "1.0", "Respuesta"]

    errs = validate_case_coherence(g, j, c_new, is_new_format=True)
    assert len(errs) > 0
    assert "Incoherencia de pregunta" in errs[0]

# 39. Pregunta CSV diferente al JSON: rechazo
def test_case_coherence_csv_question_mismatch_reject():
    g = {"id": 1, "categoria": "facil", "pregunta": "¿Cuál es el horario?"}
    j = {"id": 1, "categoria": "facil", "pregunta": "¿Cuál es el horario?", "status": "success", "attempts": 1, "technical_error": None, "precision": 1.0, "cobertura": 1.0, "pertinencia": 1.0}
    c_new = ["1", "facil", "success", "1", "", "¿Otro texto?", "1.0", "1.0", "1.0", "Respuesta"]

    errs = validate_case_coherence(g, j, c_new, is_new_format=True)
    assert len(errs) > 0
    assert "Incoherencia de pregunta" in errs[0]

# 40. Error técnico None en JSON y CSV vacío: aprobación
def test_case_coherence_technical_error_none_and_empty_pass():
    g = {"id": 1, "categoria": "facil", "pregunta": "P1"}
    j = {"id": 1, "categoria": "facil", "pregunta": "P1", "status": "success", "attempts": 1, "technical_error": None, "precision": 1.0, "cobertura": 1.0, "pertinencia": 1.0}
    c_new = ["1", "facil", "success", "1", "", "P1", "1.0", "1.0", "1.0", "R1"]

    errs = validate_case_coherence(g, j, c_new, is_new_format=True)
    assert errs == []

# 41. Error técnico diferente: rechazo
def test_case_coherence_technical_error_mismatch_reject():
    g = {"id": 1, "categoria": "facil", "pregunta": "P1"}
    j = {"id": 1, "categoria": "facil", "pregunta": "P1", "status": "infrastructure_error", "attempts": 2, "technical_error": "Timeout 504", "precision": None, "cobertura": None, "pertinencia": None}
    c_new = ["1", "facil", "infrastructure_error", "2", "Connection refused 500", "P1", "", "", "", ""]

    errs = validate_case_coherence(g, j, c_new, is_new_format=True)
    assert len(errs) > 0
    assert "Incoherencia de Error_Tecnico" in errs[0]

# 42. Métrica global obligatoria ausente: rechazo
def test_validate_global_metrics_missing_key_reject():
    recalc = {"precision_global": 0.5, "cobertura_global": 0.8, "pertinencia_global": 0.7}
    stored_incomplete = {"precision_global": 0.5, "cobertura_global": 0.8}

    errs = validate_global_metrics(recalc, stored_incomplete)
    assert len(errs) > 0
    assert "pertinencia_global" in errs[0]

# 43. Categoría almacenada ausente en desglose: rechazo
def test_validate_category_breakdown_missing_category_reject():
    recalc = {
        "facil": {"total_casos": 15, "precision": 0.5, "cobertura": 0.5, "pertinencia": 0.5},
        "ambiguo": {"total_casos": 10, "precision": 0.4, "cobertura": 0.4, "pertinencia": 0.4}
    }
    stored_missing = {
        "facil": {"total_casos": 15, "precision": 0.5, "cobertura": 0.5, "pertinencia": 0.5}
    }

    errs = validate_category_breakdown(recalc, stored_missing)
    assert len(errs) > 0
    assert "ambiguo" in errs[0]

# 44. Categoría almacenada adicional no esperada: rechazo
def test_validate_category_breakdown_extra_category_reject():
    recalc = {
        "facil": {"total_casos": 15, "precision": 0.5, "cobertura": 0.5, "pertinencia": 0.5}
    }
    stored_extra = {
        "facil": {"total_casos": 15, "precision": 0.5, "cobertura": 0.5, "pertinencia": 0.5},
        "inexistente": {"total_casos": 1, "precision": 1.0, "cobertura": 1.0, "pertinencia": 1.0}
    }

    errs = validate_category_breakdown(recalc, stored_extra)
    assert len(errs) > 0
    assert "inexistente" in errs[0]

# 45. Métrica de categoría ausente: rechazo
def test_validate_category_breakdown_missing_metric_key_reject():
    recalc = {
        "facil": {"total_casos": 15, "precision": 0.5, "cobertura": 0.5, "pertinencia": 0.5}
    }
    stored_missing_key = {
        "facil": {"total_casos": 15, "precision": 0.5, "cobertura": 0.5}
    }

    errs = validate_category_breakdown(recalc, stored_missing_key)
    assert len(errs) > 0
    assert "pertinencia" in errs[0]

# 46. Diferencia float menor o igual a 0.0001: aprobación
def test_float_difference_within_tolerance_pass():
    recalc_g = {"precision_global": 0.33333, "cobertura_global": 1.0, "pertinencia_global": 0.50004}
    stored_g = {"precision_global": 0.3333, "cobertura_global": 1.0, "pertinencia_global": 0.5}

    errs = validate_global_metrics(recalc_g, stored_g, tol=0.0001)
    assert errs == []

# 47. Diferencia float mayor a 0.0001: rechazo
def test_float_difference_exceeding_tolerance_reject():
    recalc_g = {"precision_global": 0.3500, "cobertura_global": 1.0, "pertinencia_global": 0.5}
    stored_g = {"precision_global": 0.3333, "cobertura_global": 1.0, "pertinencia_global": 0.5}

    errs = validate_global_metrics(recalc_g, stored_g, tol=0.0001)
    assert len(errs) > 0
    assert "precision_global" in errs[0]

# 48. RAGRetrievalPolicy pasa los valores al objeto
def test_rag_retrieval_policy_contract_values():
    policy = RAGRetrievalPolicy(limit=6, max_cosine_distance=0.45, keyword_fallback_limit=2)
    assert policy.limit == 6
    assert policy.max_cosine_distance == 0.45
    assert policy.keyword_fallback_limit == 2

# 49 & 50. search_similar recibe max_cosine_distance y keyword_fallback_limit
def test_search_similar_receives_keyword_only_args():
    async def _run():
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_repo = AsyncMock()
        mock_chunk = RetrievedChunkDTO(text="Texto del reglamento UNSAAC", source="Reglamento")
        mock_repo.search_similar.return_value = [mock_chunk]

        with unittest.mock.patch("tests.test_retrieval.CorpusRepository", return_value=mock_repo), \
             unittest.mock.patch.object(GeminiAdapter, "compute_embedding", new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [0.1] * 768
            evaluator = RetrievalEvaluator()
            item = {"id": 1, "categoria": "facil", "pregunta": "¿Qué es tutoría?", "articulos_referencia": ["Art. 1"], "palabras_clave_esperadas": ["tutoría"]}
            res = await evaluator.evaluate_item(item, mock_db)
            assert res["status"] == "success"
            mock_repo.search_similar.assert_called_once()
            kwargs = mock_repo.search_similar.call_args.kwargs
            assert kwargs.get("max_cosine_distance") == 0.45
            assert kwargs.get("keyword_fallback_limit") == 2
    asyncio.run(_run())

# 51. RetrievedChunkDTO se transforma correctamente a texto para métricas
def test_retrieved_chunk_dto_transformation_to_text():
    chunk = RetrievedChunkDTO(text="Art. 10 Reglamento de Tutoría UNSAAC", source="norma.pdf")
    retrieved_texts = [chunk.text]
    assert retrieved_texts == ["Art. 10 Reglamento de Tutoría UNSAAC"]

# 52. Un objeto de retrieval inválido produce infrastructure_error
def test_invalid_retrieved_object_produces_infra_error():
    async def _run():
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_repo = AsyncMock()
        mock_repo.search_similar.return_value = ["invalid_str_object"]

        with unittest.mock.patch("tests.test_retrieval.CorpusRepository", return_value=mock_repo), \
             unittest.mock.patch.object(GeminiAdapter, "compute_embedding", new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [0.1] * 768
            evaluator = RetrievalEvaluator()
            item = {"id": 1, "categoria": "facil", "pregunta": "P1", "articulos_referencia": [], "palabras_clave_esperadas": []}
            res = await evaluator.evaluate_item(item, mock_db)
            assert res["status"] == "infrastructure_error"
            assert "RetrievedChunkDTO" in res["technical_error"]
    asyncio.run(_run())

# 53, 54, 55. ChatUseCase recibe tutor_assignment_repo, calendar_repo, rag_policy
def test_chat_use_case_receives_complete_dependencies():
    mock_chat = MagicMock()
    mock_corpus = MagicMock()
    mock_llm = MagicMock()
    mock_tutor = MagicMock()
    mock_cal = MagicMock()
    policy = RAGRetrievalPolicy(limit=6, max_cosine_distance=0.45, keyword_fallback_limit=2)

    use_case = ChatUseCase(
        chat_repo=mock_chat,
        corpus_repo=mock_corpus,
        llm=mock_llm,
        tutor_assignment_repo=mock_tutor,
        calendar_repo=mock_cal,
        rag_policy=policy
    )

    assert use_case.tutor_assignment_repo == mock_tutor
    assert use_case.calendar_repo == mock_cal
    assert use_case.rag_policy == policy

# 56 & 57. send_chat_message recibe user_id, user_role, user_content
def test_send_chat_message_named_arguments_invocation():
    async def _run():
        mock_user = MagicMock()
        mock_user.id = 42
        mock_user.role = "estudiante"
        mock_db = AsyncMock()
        mock_db.add = MagicMock()

        mock_use_case = AsyncMock()
        mock_msg = MagicMock()
        mock_msg.content = "Respuesta oficial"
        mock_use_case.send_chat_message.return_value = mock_msg

        with unittest.mock.patch("tests.test_generation.ChatUseCase", return_value=mock_use_case), \
             unittest.mock.patch("tests.test_generation.ChatRepository"), \
             unittest.mock.patch("tests.test_generation.CorpusRepository"), \
             unittest.mock.patch("tests.test_generation.TutorAssignmentRepository"), \
             unittest.mock.patch("tests.test_generation.CalendarRepository"), \
             unittest.mock.patch.object(GenerationEvaluator, "cleanup_case_eval_user", new_callable=AsyncMock):
            evaluator = GenerationEvaluator()
            item = {"id": 1, "categoria": "facil", "pregunta": "¿Consulta?", "palabras_clave_esperadas": []}
            res = await evaluator.evaluate_item(item, mock_user, mock_db)
            assert res["status"] == "success"
            mock_use_case.send_chat_message.assert_called_once_with(
                user_id=42,
                user_role="estudiante",
                user_content="¿Consulta?"
            )
    asyncio.run(_run())

# 58. GeminiAdapter mantiene fallback de generación por defecto
def test_gemini_adapter_generation_fallback_default_true():
    adapter = GeminiAdapter(api_key="")
    assert adapter.allow_generation_fallback is True

# 59. GeminiAdapter en modo estricto vuelve a lanzar el error de generación
def test_gemini_adapter_strict_generation_mode_raises():
    async def _run():
        adapter = GeminiAdapter(api_key="", allow_generation_fallback=False)
        with pytest.raises(RuntimeError) as exc_info:
            await adapter.generate_response("instr", [], "msg")
        assert "strict generation mode" in str(exc_info.value)
    asyncio.run(_run())

# 60. GeminiAdapter en modo estricto no usa fallback de embedding
def test_gemini_adapter_strict_embedding_mode_raises():
    async def _run():
        adapter = GeminiAdapter(api_key="", allow_embedding_fallback=False)
        with pytest.raises(RuntimeError) as exc_info:
            await adapter.compute_embedding("msg")
        assert "strict embedding mode" in str(exc_info.value)
    asyncio.run(_run())

# 61. API_KEY_INVALID se clasifica como no reintentable
def test_api_key_invalid_non_retryable():
    err = Exception("API key not valid. API_KEY_INVALID 400 Bad Request")
    assert is_transient_error(err) is False

# 62. Un fallo al construir ChatUseCase produce un resultado infrastructure_error y no un traceback
def test_chat_use_case_construction_failure_produces_infra_error():
    async def _run():
        mock_user = MagicMock()
        mock_user.id = 10
        mock_user.role = "tutor"
        mock_db = AsyncMock()
        mock_db.add = MagicMock()

        with unittest.mock.patch("tests.test_generation.ChatUseCase", side_effect=RuntimeError("Error en dependencias de ChatUseCase")), \
             unittest.mock.patch.object(GenerationEvaluator, "cleanup_case_eval_user", new_callable=AsyncMock):
            evaluator = GenerationEvaluator()
            item = {"id": 1, "categoria": "facil", "pregunta": "¿Consulta?", "palabras_clave_esperadas": []}
            res = await evaluator.evaluate_item(item, mock_user, mock_db)
            assert res["status"] == "infrastructure_error"
            assert "Error en dependencias" in res["technical_error"]
    asyncio.run(_run())

# 63. Un fallo al crear el usuario de evaluación produce diagnósticos para todos los casos seleccionados
def test_failure_creating_eval_user_produces_diagnostics_for_all_selected():
    async def _run():
        golden_subset = [
            {"id": 1, "categoria": "facil", "pregunta": "P1"},
            {"id": 2, "categoria": "ambiguo", "pregunta": "P2"}
        ]
        with unittest.mock.patch("tests.test_generation.SessionLocal") as mock_session_cls, \
             unittest.mock.patch("tests.test_generation.GenerationEvaluator.create_case_eval_user", side_effect=RuntimeError("BD inalcanzable")):
            mock_db = AsyncMock()
            mock_db.add = MagicMock()
            mock_session_cls.return_value.__aenter__.return_value = mock_db

            results = await run_generation_benchmark("dummy_path", items=golden_subset)
            assert len(results) == 2
            assert all(r["status"] == "infrastructure_error" for r in results)
            assert all("BD inalcanzable" in r["technical_error"] for r in results)
    asyncio.run(_run())

# 64. Los errores técnicos quedan excluidos de las métricas
def test_technical_errors_excluded_from_metrics_summary():
    detalles = [
        {"id": 1, "categoria": "facil", "status": "success", "precision": 0.8, "cobertura": 0.8, "pertinencia": 0.8},
        {"id": 2, "categoria": "facil", "status": "infrastructure_error", "precision": None, "cobertura": None, "pertinencia": None}
    ]
    globales, desglose = calculate_global_metrics(detalles)
    assert globales["precision_global"] == 0.8
    assert desglose["facil"]["total_casos"] == 1

# 65. Los resultados oficiales siguen protegidos
def test_official_results_protection_policy():
    assert is_official_complete_run(15, 15, 15, 1, 0, is_partial=False) is False
    assert is_official_complete_run(15, 15, 15, 0, 0, is_partial=False) is True

# 66. Un 429 en embedding realiza exactamente 1 + EVAL_MAX_RETRIES solicitudes
def test_embedding_429_exact_attempts_without_nesting():
    async def _run():
        calls_count = 0
        async def mock_embed(*args, **kwargs):
            nonlocal calls_count
            calls_count += 1
            raise ConnectionError("429 RESOURCE_EXHAUSTED")

        sleep_mock = AsyncMock()
        cfg = EvaluationConfig(max_retries=3)
        eval_llm = EvaluationGeminiAdapter(api_key="fake_key", config=cfg, sleep_fn=sleep_mock)

        with unittest.mock.patch.object(GeminiAdapter, "compute_embedding", side_effect=mock_embed):
            with pytest.raises(InfrastructureError) as exc_info:
                await eval_llm.compute_embedding("texto")
            assert calls_count == 4
            assert exc_info.value.attempts == 4
    asyncio.run(_run())

# 67. Un 429 en generación realiza exactamente 1 + EVAL_MAX_RETRIES solicitudes
def test_generation_429_exact_attempts_without_nesting():
    async def _run():
        calls_count = 0
        async def mock_gen(*args, **kwargs):
            nonlocal calls_count
            calls_count += 1
            raise ConnectionError("503 Service Unavailable")

        sleep_mock = AsyncMock()
        cfg = EvaluationConfig(max_retries=2)
        eval_llm = EvaluationGeminiAdapter(api_key="fake_key", config=cfg, sleep_fn=sleep_mock)

        with unittest.mock.patch.object(GeminiAdapter, "generate_response", side_effect=mock_gen):
            with pytest.raises(InfrastructureError) as exc_info:
                await eval_llm.generate_response("instruction", [], "user_msg")
            assert calls_count == 3
            assert exc_info.value.attempts == 3
    asyncio.run(_run())

# 68. ChatUseCase.send_chat_message se invoca una sola vez aunque Gemini falle
def test_send_chat_message_invoked_once_on_gemini_failure():
    async def _run():
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.role = "estudiante"
        mock_db = AsyncMock()
        mock_db.add = MagicMock()

        send_calls = 0
        async def mock_send(*args, **kwargs):
            nonlocal send_calls
            send_calls += 1
            raise InfrastructureError("Error 500 en Gemini", attempts=4)

        mock_use_case = AsyncMock()
        mock_use_case.send_chat_message.side_effect = mock_send

        with unittest.mock.patch("tests.test_generation.ChatUseCase", return_value=mock_use_case), \
             unittest.mock.patch("tests.test_generation.ChatRepository"), \
             unittest.mock.patch("tests.test_generation.CorpusRepository"), \
             unittest.mock.patch("tests.test_generation.TutorAssignmentRepository"), \
             unittest.mock.patch("tests.test_generation.CalendarRepository"), \
             unittest.mock.patch.object(GenerationEvaluator, "cleanup_case_eval_user", new_callable=AsyncMock):
            evaluator = GenerationEvaluator()
            item = {"id": 1, "categoria": "facil", "pregunta": "P1", "palabras_clave_esperadas": []}
            res = await evaluator.evaluate_item(item, mock_user, mock_db)

            assert res["status"] == "infrastructure_error"
            assert send_calls == 1
            assert res["attempts"] == 4
    asyncio.run(_run())

# 69. Un fallo de generación no duplica save_message
def test_generation_failure_does_not_duplicate_save_message():
    async def _run():
        mock_chat_repo = AsyncMock()
        mock_chat_repo.get_or_create_conversation.return_value = MagicMock(id=99)
        mock_chat_repo.get_history.return_value = []

        mock_corpus = AsyncMock()
        mock_tutor = AsyncMock()
        mock_calendar = AsyncMock()

        mock_llm = AsyncMock()
        mock_llm.compute_embedding.return_value = [0.1] * 768
        mock_llm.generate_response.side_effect = RuntimeError("503 Gemini Error")

        use_case = ChatUseCase(
            chat_repo=mock_chat_repo,
            corpus_repo=mock_corpus,
            llm=mock_llm,
            tutor_assignment_repo=mock_tutor,
            calendar_repo=mock_calendar,
            rag_policy=RAGRetrievalPolicy()
        )

        with pytest.raises(RuntimeError):
            await use_case.send_chat_message(user_id=1, user_role="estudiante", user_content="Hola")

        assert mock_chat_repo.save_message.call_count == 1
        assert mock_chat_repo.save_message.call_args[0][1] == "user"
    asyncio.run(_run())

# 70. Un fallo de PostgreSQL en retrieval no solicita nuevamente el embedding
def test_pg_failure_in_retrieval_does_not_retrigger_embedding():
    async def _run():
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_repo = AsyncMock()
        embed_calls = 0

        async def mock_embed(question):
            nonlocal embed_calls
            embed_calls += 1
            return [0.1] * 768

        mock_repo.search_similar.side_effect = ConnectionError("DB Timeout 500")

        with unittest.mock.patch("tests.test_retrieval.CorpusRepository", return_value=mock_repo):
            cfg = EvaluationConfig(initial_backoff=0.001)
            evaluator = RetrievalEvaluator(config=cfg)
            evaluator.llm.compute_embedding = mock_embed
            item = {"id": 1, "categoria": "facil", "pregunta": "P1", "articulos_referencia": [], "palabras_clave_esperadas": []}

            res = await evaluator.evaluate_item(item, mock_db, config=cfg)
            assert res["status"] == "infrastructure_error"
            assert embed_calls == 1
            assert mock_repo.search_similar.call_count == 4
    asyncio.run(_run())

# 71. attempts coincide con la cantidad real de intentos
def test_attempts_matches_actual_attempts_count():
    async def _run():
        calls_count = 0
        async def mock_embed(*args, **kwargs):
            nonlocal calls_count
            calls_count += 1
            if calls_count < 2:
                raise ConnectionError("503 Error")
            return [0.2] * 768

        sleep_mock = AsyncMock()
        cfg = EvaluationConfig(max_retries=3)
        eval_llm = EvaluationGeminiAdapter(api_key="fake_key", config=cfg, sleep_fn=sleep_mock)

        with unittest.mock.patch.object(GeminiAdapter, "compute_embedding", side_effect=mock_embed):
            vec = await eval_llm.compute_embedding("consulta")
            assert len(vec) == 768
            assert eval_llm.last_embedding_attempts == 2
            assert calls_count == 2
    asyncio.run(_run())

# 72. API_KEY_INVALID realiza exactamente un intento
def test_api_key_invalid_exact_one_attempt():
    async def _run():
        calls_count = 0
        async def mock_gen(*args, **kwargs):
            nonlocal calls_count
            calls_count += 1
            raise ValueError("API key not valid. API_KEY_INVALID")

        sleep_mock = AsyncMock()
        cfg = EvaluationConfig(max_retries=3)
        eval_llm = EvaluationGeminiAdapter(api_key="fake_key", config=cfg, sleep_fn=sleep_mock)

        with unittest.mock.patch.object(GeminiAdapter, "generate_response", side_effect=mock_gen):
            with pytest.raises(NonRetryableError) as exc_info:
                await eval_llm.generate_response("instr", [], "msg")
            assert calls_count == 1
            assert exc_info.value.attempts == 1
    asyncio.run(_run())

# 73. La creación fallida de GenerationEvaluator produce diagnósticos para todos los casos
def test_failed_generation_evaluator_creation_produces_diagnostics():
    async def _run():
        golden_subset = [
            {"id": 1, "categoria": "facil", "pregunta": "P1"},
            {"id": 2, "categoria": "ambiguo", "pregunta": "P2"}
        ]
        with unittest.mock.patch("tests.test_generation.GenerationEvaluator", side_effect=RuntimeError("Fallo al inicializar GenerationEvaluator")):
            results = await run_generation_benchmark("dummy_path", items=golden_subset)
            assert len(results) == 2
            assert all(r["status"] == "infrastructure_error" for r in results)
            assert all("Fallo al inicializar GenerationEvaluator" in r["technical_error"] for r in results)
    asyncio.run(_run())

# 74. La creación fallida de RetrievalEvaluator produce diagnósticos para todos los casos
def test_failed_retrieval_evaluator_creation_produces_diagnostics():
    async def _run():
        golden_subset = [
            {"id": 1, "categoria": "facil", "pregunta": "P1"},
            {"id": 2, "categoria": "ambiguo", "pregunta": "P2"}
        ]
        with unittest.mock.patch("tests.test_retrieval.RetrievalEvaluator", side_effect=RuntimeError("Fallo al inicializar RetrievalEvaluator")):
            results = await run_retrieval_benchmark("dummy_path", items=golden_subset)
            assert len(results) == 2
            assert all(r["status"] == "infrastructure_error" for r in results)
            assert all("Fallo al inicializar RetrievalEvaluator" in r["technical_error"] for r in results)
    asyncio.run(_run())

# 75. El comportamiento predeterminado de producción de GeminiAdapter se mantiene compatible
def test_gemini_adapter_production_defaults():
    adapter = GeminiAdapter(api_key="dummy_key")
    assert adapter.allow_embedding_fallback is True
    assert adapter.allow_generation_fallback is True
    assert adapter.api_max_attempts == 3

# 76. No se realizan esperas reales en las pruebas
def test_no_real_sleeps_in_tests():
    async def _run():
        sleep_mock = AsyncMock()
        cfg = EvaluationConfig(max_retries=2, initial_backoff=10.0)
        calls_count = 0
        async def mock_op():
            nonlocal calls_count
            calls_count += 1
            if calls_count < 2:
                raise ConnectionError("503 Error")
            return "OK"

        start = asyncio.get_event_loop().time()
        res, attempts = await execute_with_retry(mock_op, config=cfg, sleep_fn=sleep_mock)
        end = asyncio.get_event_loop().time()

        assert res == "OK"
        assert attempts == 2
        assert sleep_mock.called
        assert (end - start) < 0.1
    asyncio.run(_run())

# 77. No se realizan conexiones reales a Gemini o PostgreSQL en pruebas
def test_no_real_network_connections():
    adapter = GeminiAdapter(api_key="", allow_embedding_fallback=False, allow_generation_fallback=False)
    assert adapter.client is None

# 78. Embedding usa 3 intentos y generación 1: el caso registra attempts=3
def test_embedding_3_attempts_generation_1_attempt_records_3():
    async def _run():
        mock_user = MagicMock(id=1, role="estudiante")
        mock_db = AsyncMock()
        mock_db.add = MagicMock()

        evaluator = GenerationEvaluator()

        async def mock_send(*args, **kwargs):
            evaluator.llm.last_embedding_attempts = 3
            evaluator.llm.last_generation_attempts = 1
            return MagicMock(content="Respuesta")

        mock_use_case = AsyncMock()
        mock_use_case.send_chat_message.side_effect = mock_send

        with unittest.mock.patch("tests.test_generation.ChatUseCase", return_value=mock_use_case), \
             unittest.mock.patch("tests.test_generation.ChatRepository"), \
             unittest.mock.patch("tests.test_generation.CorpusRepository"), \
             unittest.mock.patch("tests.test_generation.TutorAssignmentRepository"), \
             unittest.mock.patch("tests.test_generation.CalendarRepository"), \
             unittest.mock.patch.object(GenerationEvaluator, "cleanup_case_eval_user", new_callable=AsyncMock):
            item = {"id": 1, "categoria": "facil", "pregunta": "P1", "palabras_clave_esperadas": []}
            res = await evaluator.evaluate_item(item, mock_user, mock_db)
            assert res["status"] == "success"
            assert res["attempts"] == 3
    asyncio.run(_run())

# 79. Embedding usa 1 intento y generación 3: el caso registra attempts=3
def test_embedding_1_attempt_generation_3_attempts_records_3():
    async def _run():
        mock_user = MagicMock(id=1, role="estudiante")
        mock_db = AsyncMock()
        mock_db.add = MagicMock()

        evaluator = GenerationEvaluator()

        async def mock_send(*args, **kwargs):
            evaluator.llm.last_embedding_attempts = 1
            evaluator.llm.last_generation_attempts = 3
            return MagicMock(content="Respuesta")

        mock_use_case = AsyncMock()
        mock_use_case.send_chat_message.side_effect = mock_send

        with unittest.mock.patch("tests.test_generation.ChatUseCase", return_value=mock_use_case), \
             unittest.mock.patch("tests.test_generation.ChatRepository"), \
             unittest.mock.patch("tests.test_generation.CorpusRepository"), \
             unittest.mock.patch("tests.test_generation.TutorAssignmentRepository"), \
             unittest.mock.patch("tests.test_generation.CalendarRepository"), \
             unittest.mock.patch.object(GenerationEvaluator, "cleanup_case_eval_user", new_callable=AsyncMock):
            item = {"id": 1, "categoria": "facil", "pregunta": "P1", "palabras_clave_esperadas": []}
            res = await evaluator.evaluate_item(item, mock_user, mock_db)
            assert res["status"] == "success"
            assert res["attempts"] == 3
    asyncio.run(_run())

# 80. Embedding usa 2 intentos y generación falla en 1: el resultado infrastructure_error registra attempts=2
def test_embedding_2_attempts_generation_fails_on_1_records_attempts_2():
    async def _run():
        mock_user = MagicMock(id=1, role="estudiante")
        mock_db = AsyncMock()
        mock_db.add = MagicMock()

        evaluator = GenerationEvaluator()

        async def mock_send(*args, **kwargs):
            evaluator.llm.last_embedding_attempts = 2
            evaluator.llm.last_generation_attempts = 1
            raise InfrastructureError("Error 500 en Gemini", attempts=1)

        mock_use_case = AsyncMock()
        mock_use_case.send_chat_message.side_effect = mock_send

        with unittest.mock.patch("tests.test_generation.ChatUseCase", return_value=mock_use_case), \
             unittest.mock.patch("tests.test_generation.ChatRepository"), \
             unittest.mock.patch("tests.test_generation.CorpusRepository"), \
             unittest.mock.patch("tests.test_generation.TutorAssignmentRepository"), \
             unittest.mock.patch("tests.test_generation.CalendarRepository"), \
             unittest.mock.patch.object(GenerationEvaluator, "cleanup_case_eval_user", new_callable=AsyncMock):
            item = {"id": 1, "categoria": "facil", "pregunta": "P1", "palabras_clave_esperadas": []}
            res = await evaluator.evaluate_item(item, mock_user, mock_db)
            assert res["status"] == "infrastructure_error"
            assert res["attempts"] == 2
    asyncio.run(_run())

# 81. Los contadores se reinician antes del siguiente caso
def test_counters_reset_before_next_case():
    async def _run():
        eval_llm = EvaluationGeminiAdapter(api_key="fake")
        eval_llm.last_embedding_attempts = 5
        eval_llm.last_generation_attempts = 5
        eval_llm.embedding_requests = 10
        eval_llm.generation_requests = 10

        eval_llm.reset_attempt_counters()
        assert eval_llm.last_embedding_attempts == 0
        assert eval_llm.last_generation_attempts == 0
        assert eval_llm.embedding_requests == 0
        assert eval_llm.generation_requests == 0
    asyncio.run(_run())

# 82. Un fallo guarda el número de intentos en last_embedding_attempts o last_generation_attempts
def test_failure_stores_attempts_in_counters():
    async def _run():
        sleep_mock = AsyncMock()
        eval_llm = EvaluationGeminiAdapter(api_key="fake", sleep_fn=sleep_mock)

        async def failing_embed(*args, **kwargs):
            raise ConnectionError("503 Error")

        with unittest.mock.patch.object(GeminiAdapter, "compute_embedding", side_effect=failing_embed):
            with pytest.raises(InfrastructureError):
                await eval_llm.compute_embedding("query")
            assert eval_llm.last_embedding_attempts == 4
    asyncio.run(_run())

# 83. api_max_attempts inválido es rechazado
def test_api_max_attempts_validation():
    assert GeminiAdapter(api_key="", api_max_attempts=1).api_max_attempts == 1
    assert GeminiAdapter(api_key="", api_max_attempts=3).api_max_attempts == 3

    with pytest.raises(ValueError):
        GeminiAdapter(api_key="", api_max_attempts=0)
    with pytest.raises(ValueError):
        GeminiAdapter(api_key="", api_max_attempts=-1)
    with pytest.raises(ValueError):
        GeminiAdapter(api_key="", api_max_attempts=True)
    with pytest.raises(ValueError):
        GeminiAdapter(api_key="", api_max_attempts=1.5)

# === NUEVAS PRUEBAS GATE FASE 5C: IDENTIDAD DE 18 CHARS & EXACTAMENTE UN ROLLBACK EN LIMPIEZA ===

# 84. student_code contiene el token completo de 12 chars y tiene una longitud máxima de 18
def test_derive_case_eval_identity_token_and_length():
    id_run1 = derive_case_eval_identity("run_A", 1)
    id_run2 = derive_case_eval_identity("run_B", 1)
    id_case2 = derive_case_eval_identity("run_A", 2)

    token = id_run1["token"]
    student_code = id_run1["student_code"]

    assert token in student_code
    assert student_code.startswith("EV" + token)
    assert len(student_code) <= 18
    assert student_code != id_run2["student_code"]
    assert student_code != id_case2["student_code"]

# 85. Mismatches de verificación en cleanup ejecutan EXACTAMENTE 2 SELECTs, 0 DELETE, 0 commit, 1 rollback (Usuario Real)
def test_cleanup_mismatch_real_user_single_rollback():
    async def _run():
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_user = MagicMock(id=10, email="real_student@unsaac.edu.pe", role="estudiante")
        mock_profile = MagicMock(user_id=10, student_code="REAL001", full_name="Estudiante Real")

        mock_db.execute.side_effect = [
            MagicMock(scalars=lambda: MagicMock(first=lambda: mock_user)),
            MagicMock(scalars=lambda: MagicMock(first=lambda: mock_profile))
        ]

        evaluator = GenerationEvaluator()
        with pytest.raises(InfrastructureError):
            await evaluator.cleanup_case_eval_user(mock_db, user_id=10, run_id="run_test", case_id=1)

        assert mock_db.execute.call_count == 2
        assert mock_db.commit.call_count == 0
        assert mock_db.rollback.call_count == 1
    asyncio.run(_run())

# 86. Mismatch de correo: 2 SELECTs, 0 DELETE, 0 commit, 1 rollback
def test_cleanup_mismatch_email_single_rollback():
    async def _run():
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        identity = derive_case_eval_identity("run_test", 1)
        mock_user = MagicMock(id=10, email="eval_temp_wrong@eval.unsaac.edu.pe", role="estudiante")
        mock_profile = MagicMock(user_id=10, student_code=identity["student_code"], full_name=identity["full_name"])

        mock_db.execute.side_effect = [
            MagicMock(scalars=lambda: MagicMock(first=lambda: mock_user)),
            MagicMock(scalars=lambda: MagicMock(first=lambda: mock_profile))
        ]

        evaluator = GenerationEvaluator()
        with pytest.raises(InfrastructureError):
            await evaluator.cleanup_case_eval_user(mock_db, user_id=10, run_id="run_test", case_id=1)

        assert mock_db.execute.call_count == 2
        assert mock_db.commit.call_count == 0
        assert mock_db.rollback.call_count == 1
    asyncio.run(_run())

# 87. Mismatch de rol: 2 SELECTs, 0 DELETE, 0 commit, 1 rollback
def test_cleanup_mismatch_role_single_rollback():
    async def _run():
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        identity = derive_case_eval_identity("run_test", 1)
        mock_user = MagicMock(id=10, email=identity["email"], role="tutor")
        mock_profile = MagicMock(user_id=10, student_code=identity["student_code"], full_name=identity["full_name"])

        mock_db.execute.side_effect = [
            MagicMock(scalars=lambda: MagicMock(first=lambda: mock_user)),
            MagicMock(scalars=lambda: MagicMock(first=lambda: mock_profile))
        ]

        evaluator = GenerationEvaluator()
        with pytest.raises(InfrastructureError):
            await evaluator.cleanup_case_eval_user(mock_db, user_id=10, run_id="run_test", case_id=1)

        assert mock_db.execute.call_count == 2
        assert mock_db.commit.call_count == 0
        assert mock_db.rollback.call_count == 1
    asyncio.run(_run())

# 88. Mismatch de student_code: 2 SELECTs, 0 DELETE, 0 commit, 1 rollback
def test_cleanup_mismatch_student_code_single_rollback():
    async def _run():
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        identity = derive_case_eval_identity("run_test", 1)
        mock_user = MagicMock(id=10, email=identity["email"], role="estudiante")
        mock_profile = MagicMock(user_id=10, student_code="EV_WRONG_CODE", full_name=identity["full_name"])

        mock_db.execute.side_effect = [
            MagicMock(scalars=lambda: MagicMock(first=lambda: mock_user)),
            MagicMock(scalars=lambda: MagicMock(first=lambda: mock_profile))
        ]

        evaluator = GenerationEvaluator()
        with pytest.raises(InfrastructureError):
            await evaluator.cleanup_case_eval_user(mock_db, user_id=10, run_id="run_test", case_id=1)

        assert mock_db.execute.call_count == 2
        assert mock_db.commit.call_count == 0
        assert mock_db.rollback.call_count == 1
    asyncio.run(_run())

# 89. Mismatch de full_name: 2 SELECTs, 0 DELETE, 0 commit, 1 rollback
def test_cleanup_mismatch_full_name_single_rollback():
    async def _run():
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        identity = derive_case_eval_identity("run_test", 1)
        mock_user = MagicMock(id=10, email=identity["email"], role="estudiante")
        mock_profile = MagicMock(user_id=10, student_code=identity["student_code"], full_name="WRONG NAME")

        mock_db.execute.side_effect = [
            MagicMock(scalars=lambda: MagicMock(first=lambda: mock_user)),
            MagicMock(scalars=lambda: MagicMock(first=lambda: mock_profile))
        ]

        evaluator = GenerationEvaluator()
        with pytest.raises(InfrastructureError):
            await evaluator.cleanup_case_eval_user(mock_db, user_id=10, run_id="run_test", case_id=1)

        assert mock_db.execute.call_count == 2
        assert mock_db.commit.call_count == 0
        assert mock_db.rollback.call_count == 1
    asyncio.run(_run())

# 90. Mismatch de user_id en perfil: 2 SELECTs, 0 DELETE, 0 commit, 1 rollback
def test_cleanup_mismatch_profile_user_id_single_rollback():
    async def _run():
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        identity = derive_case_eval_identity("run_test", 1)
        mock_user = MagicMock(id=10, email=identity["email"], role="estudiante")
        mock_profile = MagicMock(user_id=999, student_code=identity["student_code"], full_name=identity["full_name"])

        mock_db.execute.side_effect = [
            MagicMock(scalars=lambda: MagicMock(first=lambda: mock_user)),
            MagicMock(scalars=lambda: MagicMock(first=lambda: mock_profile))
        ]

        evaluator = GenerationEvaluator()
        with pytest.raises(InfrastructureError):
            await evaluator.cleanup_case_eval_user(mock_db, user_id=10, run_id="run_test", case_id=1)

        assert mock_db.execute.call_count == 2
        assert mock_db.commit.call_count == 0
        assert mock_db.rollback.call_count == 1
    asyncio.run(_run())

# 91. Validación exacta de parámetros DELETE mediante compile().params
def test_cleanup_valid_user_exact_delete_parameters():
    async def _run():
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        identity = derive_case_eval_identity("run_params", 1)
        mock_user = MagicMock(id=10, email=identity["email"], role="estudiante")
        mock_profile = MagicMock(user_id=10, student_code=identity["student_code"], full_name=identity["full_name"])

        exec_statements = []
        def mock_exec(stmt, *args, **kwargs):
            exec_statements.append(stmt)
            stmt_str = str(stmt)
            if "users" in stmt_str and "SELECT" in stmt_str:
                return MagicMock(scalars=lambda: MagicMock(first=lambda: mock_user))
            if "student_profiles" in stmt_str and "SELECT" in stmt_str:
                return MagicMock(scalars=lambda: MagicMock(first=lambda: mock_profile))
            if "conversations" in stmt_str and "SELECT" in stmt_str:
                return MagicMock(scalars=lambda: MagicMock(all=lambda: [99]))
            return MagicMock()

        mock_db.execute.side_effect = mock_exec
        evaluator = GenerationEvaluator()

        await evaluator.cleanup_case_eval_user(mock_db, user_id=10, run_id="run_params", case_id=1)

        delete_stmts = [s for s in exec_statements if hasattr(s, "table") or "DELETE" in str(s).upper()]
        assert len(delete_stmts) == 4

        # 1. DELETE Message (conversation_id == 99)
        msg_stmt = delete_stmts[0]
        assert msg_stmt.table.name == "messages"
        msg_params = list(msg_stmt.compile().params.values())
        assert msg_params == [[99]] or msg_params == [99] or 99 in msg_params[0]

        # 2. DELETE Conversation (student_id == 10)
        conv_stmt = delete_stmts[1]
        assert conv_stmt.table.name == "conversations"
        assert list(conv_stmt.compile().params.values()) == [10]

        # 3. DELETE StudentProfile (user_id == 10)
        prof_stmt = delete_stmts[2]
        assert prof_stmt.table.name == "student_profiles"
        assert list(prof_stmt.compile().params.values()) == [10]

        # 4. DELETE User (id == 10)
        user_stmt = delete_stmts[3]
        assert user_stmt.table.name == "users"
        assert list(user_stmt.compile().params.values()) == [10]

        assert mock_db.commit.call_count == 1
        assert mock_db.rollback.call_count == 0
    asyncio.run(_run())

# 92. Aislamiento estricto de dos casos con repositorios independientes y FakeChatUseCase
def test_real_isolation_strict_two_repositories_and_fake_use_case():
    async def _run():
        events_log = []
        repo1_calls = []
        repo2_calls = []

        class FakeChatRepository:
            def __init__(self, repo_id):
                self.repo_id = repo_id

            async def get_history(self, uid):
                if self.repo_id == 1:
                    repo1_calls.append(uid)
                else:
                    repo2_calls.append(uid)
                return []

        repo1 = FakeChatRepository(1)
        repo2 = FakeChatRepository(2)

        def repo_factory(user_id):
            if user_id == 101:
                return repo1
            return repo2

        evaluator = GenerationEvaluator(config=EvaluationConfig(generation_min_interval=0))
        mock_db = AsyncMock()
        mock_db.add = MagicMock()

        async def mock_create(db, case_id, cfg):
            events_log.append(f"create_case_{case_id}")
            identity = derive_case_eval_identity(cfg.run_id, case_id)
            u = MagicMock(id=100 + case_id, role="estudiante")
            return u, identity

        async def mock_cleanup(db, user_id, run_id, case_id):
            events_log.append(f"cleanup_case_{case_id}")

        evaluator.create_case_eval_user = mock_create
        evaluator.cleanup_case_eval_user = mock_cleanup

        async def mock_send_chat_message(user_id, user_role, user_content):
            case_num = user_id - 100
            repo = repo_factory(user_id)
            history = await repo.get_history(user_id)
            assert history == []
            events_log.append(f"obtener_historial_case_{case_num}")
            events_log.append(f"enviar_case_{case_num}")
            return MagicMock(content=f"Respuesta caso {case_num}")

        mock_use_case = AsyncMock()
        mock_use_case.send_chat_message.side_effect = mock_send_chat_message

        with unittest.mock.patch("tests.test_generation.ChatUseCase", return_value=mock_use_case), \
             unittest.mock.patch("tests.test_generation.ChatRepository"), \
             unittest.mock.patch("tests.test_generation.CorpusRepository"), \
             unittest.mock.patch("tests.test_generation.TutorAssignmentRepository"), \
             unittest.mock.patch("tests.test_generation.CalendarRepository"):

            item1 = {"id": 1, "categoria": "facil", "pregunta": "P1", "palabras_clave_esperadas": []}
            item2 = {"id": 2, "categoria": "facil", "pregunta": "P2", "palabras_clave_esperadas": []}

            res1 = await evaluator.evaluate_item(item1, None, mock_db, config=EvaluationConfig(generation_min_interval=0))
            res2 = await evaluator.evaluate_item(item2, None, mock_db, config=EvaluationConfig(generation_min_interval=0))

            assert res1["status"] == "success"
            assert res2["status"] == "success"

            expected_sequence = [
                "create_case_1", "obtener_historial_case_1", "enviar_case_1", "cleanup_case_1",
                "create_case_2", "obtener_historial_case_2", "enviar_case_2", "cleanup_case_2"
            ]
            assert events_log == expected_sequence
            assert repo1_calls == [101]
            assert repo2_calls == [102]
            assert 101 not in repo2_calls
    asyncio.run(_run())

# 93. Cancelación del limitador no incrementa generation_requests y no llama a generate_content
def test_rate_limiter_cancellation_does_not_increment_counter():
    async def _run():
        async def cancelling_sleep(sec):
            raise asyncio.CancelledError()

        limiter = GeminiRateLimiter(min_interval_seconds=15.0, sleep_fn=cancelling_sleep)
        limiter.last_request_time = 100.0

        eval_llm = EvaluationGeminiAdapter(
            api_key="fake",
            config=EvaluationConfig(generation_min_interval=0),
            rate_limiter=limiter
        )
        eval_llm.rate_limiter.time_fn = lambda: 105.0

        mock_gen = AsyncMock()
        eval_llm.adapter.client = MagicMock()
        eval_llm.adapter.client.aio.models.generate_content = mock_gen

        with pytest.raises(asyncio.CancelledError):
            await eval_llm.generate_response("system", [], "msg")

        assert eval_llm.generation_requests == 0
        assert mock_gen.call_count == 0
    asyncio.run(_run())

# 94. test_two_tool_steps sin pausas reales usando generation_min_interval=0
def test_two_tool_steps_count_as_two_requests_no_real_wait():
    async def _run():
        calls_count = 0
        async def mock_gen(*args, **kwargs):
            nonlocal calls_count
            calls_count += 1
            if calls_count == 1:
                call_func = MagicMock()
                call_func.name = "get_time"
                call_func.args = {}
                cand = MagicMock()
                cand.content = "tool_call_content"
                return MagicMock(function_calls=[call_func], candidates=[cand])
            return MagicMock(function_calls=None, text="Respuesta final tras tool")

        eval_llm = EvaluationGeminiAdapter(
            api_key="fake_key",
            config=EvaluationConfig(generation_min_interval=0)
        )
        eval_llm.adapter.client = MagicMock()
        eval_llm.adapter.client.aio.models.generate_content.side_effect = mock_gen

        def get_time():
            return "12:00"

        start_t = asyncio.get_event_loop().time()
        res = await eval_llm.generate_response("system", [], "pregunta", tools=[get_time])
        end_t = asyncio.get_event_loop().time()

        assert res == "Respuesta final tras tool"
        assert eval_llm.generation_requests == 2
        assert (end_t - start_t) < 0.1
    asyncio.run(_run())

# 95. Prueba estricta de exportación de artefactos parseando CSV mediante csv.reader por posición
def test_real_artifact_export_parsed_with_csv_reader():
    cfg = EvaluationConfig(run_id="run_csv_strict")
    consolidated = [
        {
            "id": 1, "categoria": "facil", "pregunta": "¿P1?", "status": "success",
            "attempts": 1, "embedding_requests": 2, "generation_requests": 3,
            "technical_error": None, "precision": 1.0, "cobertura": 1.0,
            "pertinencia": 1.0, "bot_response": "Respuesta"
        }
    ]
    payload, csv_str = build_export_payloads(
        consolidated=consolidated,
        config=cfg,
        golden_hash="hash123",
        total_golden_cases=1,
        selected_items=[{"id": 1}],
        completed_count=1,
        infra_error_count=0,
        skipped_count=0,
        is_complete=True,
        cat_summary={"facil": {"total_casos": 1, "precision": 1.0, "cobertura": 1.0, "pertinencia": 1.0}},
        globales={"precision_global": 1.0, "cobertura_global": 1.0, "pertinencia_global": 1.0}
    )

    reader = list(csv.reader(io.StringIO(csv_str)))
    header = reader[0]
    data_row = reader[1]

    idx_emb = header.index("Solicitudes_Embedding")
    idx_gen = header.index("Solicitudes_Generacion")

    assert idx_emb == 10
    assert idx_gen == 11
    assert data_row[idx_emb] == "2"
    assert data_row[idx_gen] == "3"


# === PRUEBAS ADICIONALES DE LA MIGRACIÓN OFICIAL A 15 CASOS Y MANIFIESTO ===

def test_official_golden_set_15_cases_exact_ids():
    base_dir = Path(__file__).resolve().parent.parent
    golden_path = base_dir / "dataset" / "golden_set.json"
    assert golden_path.exists()
    with open(golden_path, "r", encoding="utf-8") as f:
        golden_set = json.load(f)
    assert len(golden_set) == 15
    ids = {item["id"] for item in golden_set}
    assert ids == {1, 3, 6, 8, 10, 13, 15, 16, 18, 20, 23, 25, 26, 29, 32}

def test_official_golden_set_category_distribution():
    base_dir = Path(__file__).resolve().parent.parent
    golden_path = base_dir / "dataset" / "golden_set.json"
    with open(golden_path, "r", encoding="utf-8") as f:
        golden_set = json.load(f)
    cat_counts = {}
    for item in golden_set:
        c = item["categoria"]
        cat_counts[c] = cat_counts.get(c, 0) + 1
    assert cat_counts == {"facil": 7, "ambiguo": 5, "fuera_de_alcance": 3}

def test_historical_golden_set_32_cases_intact():
    base_dir = Path(__file__).resolve().parent.parent
    golden_32_path = base_dir / "dataset" / "golden_set_32_historico.json"
    assert golden_32_path.exists()
    h32 = compute_golden_set_hash(golden_32_path)
    assert h32 == "e58db793eb82e26d7f0a84e32b9369b725131b2d9513dbcd3fa13fdf036438b1"
    with open(golden_32_path, "r", encoding="utf-8") as f:
        historical_set = json.load(f)
    assert len(historical_set) == 32
    assert [x["id"] for x in historical_set] == list(range(1, 33))

def test_golden_set_manifest_coherence_full():
    base_dir = Path(__file__).resolve().parent.parent
    manifest_path = base_dir / "dataset" / "golden_set_manifest.json"
    golden_15_path = base_dir / "dataset" / "golden_set.json"
    assert manifest_path.exists()
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["schema_version"] == "1.0"
    assert manifest["official_case_count"] == 15
    assert manifest["historical_case_count"] == 32
    assert manifest["historical_golden_set_path"] == "backend/tests/dataset/golden_set_32_historico.json"
    assert manifest["historical_golden_set_sha256"] == "e58db793eb82e26d7f0a84e32b9369b725131b2d9513dbcd3fa13fdf036438b1"
    assert manifest["official_golden_set_path"] == "backend/tests/dataset/golden_set.json"
    assert manifest["official_golden_set_sha256"] == compute_golden_set_hash(golden_15_path)
    assert manifest["selection_method"] == "muestreo_sistematico_estratificado_determinista"
    assert manifest["preserve_original_ids"] is True
    assert manifest["selected_source_ids"] == [1, 3, 6, 8, 10, 13, 15, 16, 18, 20, 23, 25, 26, 29, 32]
    assert manifest["category_distribution"] == {"facil": 7, "ambiguo": 5, "fuera_de_alcance": 3}
    assert manifest["models"] == {"generation": "gemini-3.5-flash-lite", "embedding": "gemini-embedding-2"}
    assert manifest["official_completion_criteria"] == {
        "total_cases": 15, "selected_cases": 15, "completed_cases": 15,
        "infrastructure_errors": 0, "skipped_cases": 0, "is_complete": True
    }
    assert isinstance(manifest["reason"], str) and len(manifest["reason"]) > 0

def test_deterministic_selection_reproduces_exact_original_objects():
    base_dir = Path(__file__).resolve().parent.parent
    golden_32_path = base_dir / "dataset" / "golden_set_32_historico.json"
    golden_15_path = base_dir / "dataset" / "golden_set.json"
    with open(golden_32_path, "r", encoding="utf-8") as f:
        historical_set = json.load(f)
    with open(golden_15_path, "r", encoding="utf-8") as f:
        official_set = json.load(f)
    historical_by_id = {item["id"]: item for item in historical_set}
    for item_15 in official_set:
        item_id = item_15["id"]
        orig_item = historical_by_id[item_id]
        assert item_15 == orig_item

def test_archived_historical_results_hashes():
    base_dir = Path(__file__).resolve().parent.parent
    hist_json = base_dir / "resultados" / "historico_32" / "eval_results_32.json"
    hist_csv = base_dir / "resultados" / "historico_32" / "eval_results_32.csv"
    assert hist_json.exists()
    assert hist_csv.exists()
    assert compute_golden_set_hash(hist_json) == "5e3c6837f8e3afabaf73bdce2f730a9615f837a67d6ce7e45bd11ac20195e34f"
    assert compute_golden_set_hash(hist_csv) == "4f0bf77f5647e6c730cb7ece159386bfdaec34f1c7fdd2e0adf6989a653add3c"

def test_absent_active_results_is_pending_state():
    base_dir = Path(__file__).resolve().parent.parent
    json_path = base_dir / "resultados" / "eval_results.json"
    csv_path = base_dir / "resultados" / "eval_results.csv"
    assert not json_path.exists()
    assert not csv_path.exists()

def test_official_completion_criteria_15_cases():
    assert is_official_complete_run(15, 15, 15, 0, 0, is_partial=False) is True
    assert is_official_complete_run(15, 15, 15, 1, 0, is_partial=False) is False
    assert is_official_complete_run(32, 32, 32, 0, 0, is_partial=False) is False

def test_filtered_run_with_15_ids_is_partial():
    all_15_ids = [1, 3, 6, 8, 10, 13, 15, 16, 18, 20, 23, 25, 26, 29, 32]
    cfg = EvaluationConfig(case_ids=all_15_ids)
    is_partial = (cfg.case_limit is not None or cfg.case_ids is not None)
    assert is_partial is True
    assert is_official_complete_run(15, 15, 15, 0, 0, is_partial=is_partial) is False

def test_artifact_payload_export_15_cases():
    cfg = EvaluationConfig(run_id="run_15_test")
    official_ids = [1, 3, 6, 8, 10, 13, 15, 16, 18, 20, 23, 25, 26, 29, 32]
    consolidated = [
        {
            "id": c_id, "categoria": "facil", "pregunta": f"P{c_id}", "status": "success",
            "attempts": 1, "embedding_requests": 1, "generation_requests": 1,
            "technical_error": None, "precision": 1.0, "cobertura": 1.0,
            "pertinencia": 1.0, "bot_response": "OK"
        }
        for c_id in official_ids
    ]
    payload, csv_str = build_export_payloads(
        consolidated=consolidated,
        config=cfg,
        golden_hash="hash15",
        total_golden_cases=15,
        selected_items=consolidated,
        completed_count=15,
        infra_error_count=0,
        skipped_count=0,
        is_complete=True,
        cat_summary={"facil": {"total_casos": 15, "precision": 1.0, "cobertura": 1.0, "pertinencia": 1.0}},
        globales={"precision_global": 1.0, "cobertura_global": 1.0, "pertinencia_global": 1.0}
    )
    assert payload["total_cases"] == 15
    assert payload["selected_cases"] == 15
    assert payload["completed_cases"] == 15
    assert payload["is_complete"] is True
    reader = list(csv.reader(io.StringIO(csv_str)))
    assert len(reader) == 16  # 1 header + 15 rows

def test_historical_results_not_confused_with_active():
    base_dir = Path(__file__).resolve().parent.parent
    active_json = base_dir / "resultados" / "eval_results.json"
    hist_json = base_dir / "resultados" / "historico_32" / "eval_results_32.json"
    assert not active_json.exists()
    assert hist_json.exists()

def test_manifest_all_fields_validation():
    base_dir = Path(__file__).resolve().parent.parent
    manifest_path = base_dir / "dataset" / "golden_set_manifest.json"
    assert manifest_path.exists()
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    required_keys = [
        "schema_version", "official_case_count", "historical_case_count",
        "historical_golden_set_path", "historical_golden_set_sha256",
        "official_golden_set_path", "official_golden_set_sha256",
        "selection_method", "preserve_original_ids", "selected_source_ids",
        "category_distribution", "models", "official_completion_criteria", "reason"
    ]
    for k in required_keys:
        assert k in data, f"Falta clave {k} en manifiesto"

def test_case_coherence_all_15_official_cases():
    base_dir = Path(__file__).resolve().parent.parent
    golden_path = base_dir / "dataset" / "golden_set.json"
    with open(golden_path, "r", encoding="utf-8") as f:
        golden_set = json.load(f)
    for case in golden_set:
        c_id = case["id"]
        c_cat = case["categoria"]
        c_q = case["pregunta"]
        json_item = {
            "id": c_id, "categoria": c_cat, "pregunta": c_q, "status": "success",
            "attempts": 1, "technical_error": None, "precision": 1.0, "cobertura": 1.0, "pertinencia": 1.0
        }
        csv_row = [str(c_id), c_cat, "success", "1", "", c_q, "1.0", "1.0", "1.0", "BotResp", "1", "1"]
        errs = validate_case_coherence(item_golden=case, item_json=json_item, csv_row=csv_row, is_new_format=True)
        assert errs == []

def test_verify_evaluation_integrity_main_function_execution():
    from tests.verify_evaluation_integrity import main as verify_main
    try:
        verify_main()
    except SystemExit as e:
        assert e.code == 0


# === PRUEBAS DE MIGRACIÓN AL MODELO GENERATIVO GEMINI 3.5 FLASH LITE ===

def test_active_generative_model_is_gemini_3_5_flash_lite():
    async def _run():
        adapter = GeminiAdapter(api_key="fake_key")
        called_models = []

        async def mock_generate_content(model, contents, config=None):
            called_models.append(model)
            mock_resp = MagicMock()
            mock_resp.text = "Respuesta de prueba"
            mock_resp.function_calls = []
            return mock_resp

        adapter.client = MagicMock()
        adapter.client.aio.models.generate_content = mock_generate_content

        res = await adapter.generate_response("instruction", [], "user_msg")
        assert res == "Respuesta de prueba"
        assert called_models == ["gemini-3.5-flash-lite"]
        assert "gemini-2.5-flash" not in called_models
    asyncio.run(_run())

def test_active_embedding_model_remains_gemini_embedding_2():
    async def _run():
        adapter = GeminiAdapter(api_key="fake_key")
        called_models = []

        async def mock_embed_content(model, contents, config=None):
            called_models.append(model)
            mock_resp = MagicMock()
            mock_resp.embeddings = [MagicMock(values=[0.1] * 768)]
            return mock_resp

        adapter.client = MagicMock()
        adapter.client.aio.models.embed_content = mock_embed_content

        res = await adapter.compute_embedding("texto")
        assert len(res) == 768
        assert called_models == ["gemini-embedding-2"]
    asyncio.run(_run())

def test_manifest_records_gemini_3_5_flash_lite_and_embedding_2():
    base_dir = Path(__file__).resolve().parent.parent
    manifest_path = base_dir / "dataset" / "golden_set_manifest.json"
    assert manifest_path.exists()
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["models"]["generation"] == "gemini-3.5-flash-lite"
    assert manifest["models"]["embedding"] == "gemini-embedding-2"

def test_run_eval_payload_records_gemini_3_5_flash_lite_and_embedding_2():
    cfg = EvaluationConfig(run_id="test_run")
    payload, _ = build_export_payloads(
        consolidated=[],
        config=cfg,
        golden_hash="hash",
        total_golden_cases=0,
        selected_items=[],
        completed_count=0,
        infra_error_count=0,
        skipped_count=0,
        is_complete=False,
        cat_summary={},
        globales={"precision_global": 0.0, "cobertura_global": 0.0, "pertinencia_global": 0.0}
    )
    assert payload["models"]["generation_model"] == "gemini-3.5-flash-lite"
    assert payload["models"]["embedding_model"] == "gemini-embedding-2"
    assert payload["models"]["generation_model"] != "gemini-2.5-flash"
    assert "gemini-2.5-flash" not in payload["models"].values()

def test_manifest_and_runner_declare_exact_same_models():
    base_dir = Path(__file__).resolve().parent.parent
    manifest_path = base_dir / "dataset" / "golden_set_manifest.json"
    assert manifest_path.exists()
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    cfg = EvaluationConfig(run_id="test_run")
    payload, _ = build_export_payloads(
        consolidated=[],
        config=cfg,
        golden_hash="hash",
        total_golden_cases=0,
        selected_items=[],
        completed_count=0,
        infra_error_count=0,
        skipped_count=0,
        is_complete=False,
        cat_summary={},
        globales={"precision_global": 0.0, "cobertura_global": 0.0, "pertinencia_global": 0.0}
    )

    manifest_gen = manifest["models"]["generation"]
    manifest_emb = manifest["models"]["embedding"]
    runner_gen = payload["models"]["generation_model"]
    runner_emb = payload["models"]["embedding_model"]

    assert manifest_gen == runner_gen == "gemini-3.5-flash-lite"
    assert manifest_emb == runner_emb == "gemini-embedding-2"
