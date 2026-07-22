import os
import tempfile
import pytest
import shutil
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

from tests.evaluation_support import (
    EvaluationConfig,
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
        calls = 0
        async def mock_op():
            nonlocal calls
            calls += 1
            if calls < 3:
                raise ConnectionError("503 Service Unavailable")
            return "SUCCESS"

        sleep_mock = AsyncMock()
        cfg = EvaluationConfig(max_retries=3, initial_backoff=0.01)
        res, attempts = await execute_with_retry(mock_op, config=cfg, sleep_fn=sleep_mock)

        assert res == "SUCCESS"
        assert attempts == 3
        assert calls == 3
    asyncio.run(_run())

# 2. InfrastructureError conserva attempts
def test_infrastructure_error_retains_attempts():
    async def _run():
        calls = 0
        async def mock_op():
            nonlocal calls
            calls += 1
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
def test_case_limit_32_is_partial():
    cfg = EvaluationConfig(case_limit=32)
    is_partial = (cfg.case_limit is not None or cfg.case_ids is not None)
    assert is_partial is True
    assert is_official_complete_run(32, 32, 32, 0, 0, is_partial=is_partial) is False

# 11. CASE_IDS con todos los 32 IDs sigue siendo parcial
def test_case_ids_all_32_is_partial():
    all_32 = list(range(1, 33))
    cfg = EvaluationConfig(case_ids=all_32)
    is_partial = (cfg.case_limit is not None or cfg.case_ids is not None)
    assert is_partial is True
    assert is_official_complete_run(32, 32, 32, 0, 0, is_partial=is_partial) is False

# 12. Sin filtros puede ser oficial
def test_no_filters_can_be_official():
    cfg = EvaluationConfig(case_limit=None, case_ids=None)
    is_partial = (cfg.case_limit is not None or cfg.case_ids is not None)
    assert is_partial is False
    assert is_official_complete_run(32, 32, 32, 0, 0, is_partial=is_partial) is True

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

# === NUEVAS PRUEBAS UNITARIAS DE FUNCIONES PURAS DEL VERIFICADOR ===

# 37. Preguntas iguales: aprobación
def test_case_coherence_equal_questions_pass():
    g = {"id": 1, "categoria": "facil", "pregunta": "¿Cuál es el horario?"}
    j = {"id": 1, "categoria": "facil", "pregunta": "¿Cuál es el horario?", "status": "success", "attempts": 1, "technical_error": None, "precision": 1.0, "cobertura": 1.0, "pertinencia": 1.0}
    # CSV new format: ID(0), Categoria(1), Estado_Ejecucion(2), Intentos(3), Error_Tecnico(4), Pregunta(5), Precision(6), Cobertura(7), Pertinencia(8), Respuesta_Bot(9)
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
        "facil": {"total_casos": 15, "precision": 0.5, "cobertura": 0.5}  # missing pertinencia
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
