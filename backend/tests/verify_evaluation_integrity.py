import csv
import json
import os
import sys
import hashlib
from pathlib import Path
from typing import List, Dict, Any

from tests.evaluation_support import (
    calculate_global_metrics,
    validate_output_directory,
    is_official_complete_run,
    compute_golden_set_hash
)

OFFICIAL_15_IDS = {1, 3, 6, 8, 10, 13, 15, 16, 18, 20, 23, 25, 26, 29, 32}
HISTORICAL_32_HASH = "e58db793eb82e26d7f0a84e32b9369b725131b2d9513dbcd3fa13fdf036438b1"
HISTORICAL_JSON_HASH = "5e3c6837f8e3afabaf73bdce2f730a9615f837a67d6ce7e45bd11ac20195e34f"
HISTORICAL_CSV_HASH = "4f0bf77f5647e6c730cb7ece159386bfdaec34f1c7fdd2e0adf6989a653add3c"

def validate_global_metrics(
    recalc_globales: Dict[str, float],
    stored_globales: Dict[str, float],
    tol: float = 0.0001
) -> List[str]:
    """Valida métricas globales almacenadas contra recalculadas."""
    errors = []
    required_globals = ("precision_global", "cobertura_global", "pertinencia_global")

    for k in required_globals:
        if k not in stored_globales:
            errors.append(f"Falta la métrica global obligatoria en JSON: '{k}'")
        else:
            diff = abs(recalc_globales[k] - stored_globales[k])
            if diff > tol:
                errors.append(f"Diferencia en métrica global '{k}': recalculado={recalc_globales[k]}, guardado={stored_globales[k]} (dif={diff})")

    return errors

def validate_category_breakdown(
    recalc_desglose: Dict[str, Dict[str, Any]],
    stored_desglose: Dict[str, Dict[str, Any]],
    tol: float = 0.0001
) -> List[str]:
    """Valida desglose por categoría almacenado contra recalculado."""
    errors = []
    recalc_cats = set(recalc_desglose.keys())
    stored_cats = set(stored_desglose.keys())

    missing_cats = recalc_cats - stored_cats
    extra_cats = stored_cats - recalc_cats

    if missing_cats:
        errors.append(f"Categorías ausentes en desglose almacenado: {sorted(list(missing_cats))}")
    if extra_cats:
        errors.append(f"Categorías adicionales no esperadas en desglose almacenado: {sorted(list(extra_cats))}")

    common_cats = recalc_cats & stored_cats
    required_cat_keys = ("total_casos", "precision", "cobertura", "pertinencia")

    for cat in sorted(list(common_cats)):
        r_info = recalc_desglose[cat]
        s_info = stored_desglose[cat]

        for k in required_cat_keys:
            if k not in s_info:
                errors.append(f"Falta la clave '{k}' en la categoría '{cat}' del desglose guardado")

        if "total_casos" in s_info and r_info["total_casos"] != s_info["total_casos"]:
            errors.append(f"Diferencia en total_casos para categoría '{cat}': recalculado={r_info['total_casos']}, guardado={s_info['total_casos']}")

        for mk in ("precision", "cobertura", "pertinencia"):
            if mk in s_info:
                diff = abs(r_info[mk] - s_info[mk])
                if diff > tol:
                    errors.append(f"Diferencia en '{cat}'.{mk}: recalculado={r_info[mk]}, guardado={s_info[mk]} (dif={diff})")

    return errors

def validate_case_coherence(
    item_golden: Dict[str, Any],
    item_json: Dict[str, Any],
    csv_row: List[str],
    is_new_format: bool,
    tol: float = 0.0001
) -> List[str]:
    """Valida coherencia individual entre Golden Set, JSON y CSV."""
    errors = []
    case_id = item_golden.get("id")

    g_cat = item_golden.get("categoria")
    j_cat = item_json.get("categoria")
    c_cat = csv_row[1] if len(csv_row) > 1 else None

    if not (g_cat == j_cat == c_cat):
        errors.append(f"Incoherencia de categoría para ID {case_id}: Golden='{g_cat}', JSON='{j_cat}', CSV='{c_cat}'")

    g_q = item_golden.get("pregunta")
    j_q = item_json.get("pregunta")
    c_q = csv_row[5] if is_new_format and len(csv_row) > 5 else (csv_row[2] if len(csv_row) > 2 else None)

    if not (g_q == j_q == c_q):
        errors.append(f"Incoherencia de pregunta para ID {case_id}")

    if is_new_format:
        c_status = csv_row[2] if len(csv_row) > 2 else None
        c_attempts = int(csv_row[3]) if len(csv_row) > 3 and csv_row[3].isdigit() else 0
        c_err = csv_row[4] if len(csv_row) > 4 else ""
        c_prec = float(csv_row[6]) if len(csv_row) > 6 and csv_row[6] != "" else None
        c_cob = float(csv_row[7]) if len(csv_row) > 7 and csv_row[7] != "" else None
        c_pert = float(csv_row[8]) if len(csv_row) > 8 and csv_row[8] != "" else None

        if item_json.get("status") != c_status:
            errors.append(f"Incoherencia de Estado_Ejecucion para ID {case_id}: JSON='{item_json.get('status')}', CSV='{c_status}'")

        if item_json.get("attempts") != c_attempts:
            errors.append(f"Incoherencia de Intentos para ID {case_id}: JSON={item_json.get('attempts')}, CSV={c_attempts}")

        j_err_norm = item_json.get("technical_error") or ""
        c_err_norm = c_err or ""
        if j_err_norm != c_err_norm:
            errors.append(f"Incoherencia de Error_Tecnico para ID {case_id}")

        for m_name, j_val, c_val in (("precision", item_json.get("precision"), c_prec), ("cobertura", item_json.get("cobertura"), c_cob), ("pertinencia", item_json.get("pertinencia"), c_pert)):
            if j_val is not None and c_val is not None:
                if abs(j_val - c_val) > tol:
                    errors.append(f"Diferencia de {m_name} JSON/CSV para ID {case_id}: JSON={j_val}, CSV={c_val}")
            elif j_val != c_val:
                errors.append(f"Diferencia nula de {m_name} JSON/CSV para ID {case_id}")

    return errors

def main():
    print("🔍 Iniciando Verificador de Integridad de Evaluación RAG (Fase 5C - Benchmark Oficial 15 Casos)...")
    pass_count = 0
    fail_count = 0

    def report_pass(msg: str):
        nonlocal pass_count
        print(f"✅ PASS: {msg}")
        pass_count += 1

    def report_fail(msg: str):
        nonlocal fail_count
        print(f"❌ FAIL: {msg}")
        fail_count += 1

    base_dir = Path(__file__).resolve().parent
    backend_dir = base_dir.parent
    repo_root = backend_dir.parent

    # 1. Validar Golden Set Oficial de 15 Casos
    golden_set_path = base_dir / "dataset" / "golden_set.json"
    golden_32_path = base_dir / "dataset" / "golden_set_32_historico.json"
    manifest_path = base_dir / "dataset" / "golden_set_manifest.json"

    if not golden_set_path.exists():
        report_fail("Golden Set oficial no encontrado en dataset/golden_set.json")
        golden_set = []
        golden_ids = set()
    else:
        try:
            with open(golden_set_path, "r", encoding="utf-8") as f:
                golden_set = json.load(f)

            golden_ids = {item.get("id") for item in golden_set if "id" in item}

            if len(golden_set) == 15:
                report_pass("Golden Set oficial posee exactamente 15 casos de prueba")
            else:
                report_fail(f"Golden Set oficial tiene {len(golden_set)} casos (se esperaban 15)")

            if golden_ids == OFFICIAL_15_IDS:
                report_pass(f"Golden Set oficial contiene los 15 IDs exactos del muestreo estratificado: {sorted(list(OFFICIAL_15_IDS))}")
            else:
                report_fail(f"IDs del Golden Set no coinciden con los 15 oficiales: {golden_ids}")

            cat_counts = {}
            for item in golden_set:
                c = item.get("categoria")
                cat_counts[c] = cat_counts.get(c, 0) + 1

            if cat_counts.get("facil") == 7 and cat_counts.get("ambiguo") == 5 and cat_counts.get("fuera_de_alcance") == 3:
                report_pass("Distribución estratificada oficial verificada (facil: 7, ambiguo: 5, fuera_de_alcance: 3)")
            else:
                report_fail(f"Distribución de categorías incorrecta: {cat_counts}")

            valid_fields = all(
                bool(item.get("pregunta")) and
                bool(item.get("respuesta_esperada")) and
                isinstance(item.get("articulos_referencia", []), list) and
                isinstance(item.get("palabras_clave_esperadas", []), list)
                for item in golden_set
            )
            if valid_fields:
                report_pass("Campos obligatorios del Golden Set oficial validados")
            else:
                report_fail("Campos obligatorios vacíos o de tipo incorrecto en Golden Set oficial")
        except Exception as e:
            report_fail(f"Error al leer Golden Set oficial: {e}")
            golden_set = []
            golden_ids = set()

    golden_item_by_id = {item["id"]: item for item in golden_set if "id" in item}

    # 2. Validar Banco Histórico de 32 y Manifiesto de Trazabilidad Completo
    if golden_32_path.exists():
        h32 = compute_golden_set_hash(golden_32_path)
        if h32 == HISTORICAL_32_HASH:
            report_pass("Banco histórico de 32 casos intacto con SHA-256 verificado")
        else:
            report_fail(f"Hash del banco histórico alterado: {h32}")
    else:
        report_fail("Falta el banco histórico de 32 casos en dataset/golden_set_32_historico.json")

    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            valid_manifest = (
                manifest.get("schema_version") == "1.0" and
                manifest.get("official_case_count") == 15 and
                manifest.get("historical_case_count") == 32 and
                manifest.get("historical_golden_set_path") == "backend/tests/dataset/golden_set_32_historico.json" and
                manifest.get("historical_golden_set_sha256") == HISTORICAL_32_HASH and
                manifest.get("official_golden_set_path") == "backend/tests/dataset/golden_set.json" and
                manifest.get("official_golden_set_sha256") == compute_golden_set_hash(golden_set_path) and
                manifest.get("selection_method") == "muestreo_sistematico_estratificado_determinista" and
                manifest.get("preserve_original_ids") is True and
                manifest.get("selected_source_ids") == sorted(list(OFFICIAL_15_IDS)) and
                manifest.get("category_distribution") == {"facil": 7, "ambiguo": 5, "fuera_de_alcance": 3} and
                manifest.get("models") == {"generation": "gemini-3.5-flash-lite", "embedding": "gemini-embedding-2"} and
                manifest.get("official_completion_criteria") == {
                    "total_cases": 15, "selected_cases": 15, "completed_cases": 15,
                    "infrastructure_errors": 0, "skipped_cases": 0, "is_complete": True
                } and
                isinstance(manifest.get("reason"), str) and len(manifest.get("reason", "")) > 0
            )

            if valid_manifest:
                report_pass("Manifiesto de trazabilidad golden_set_manifest.json validado completamente con todos los campos obligatorios")
            else:
                report_fail("Manifiesto de trazabilidad contiene valores incompletos o desincronizados")
        except Exception as e:
            report_fail(f"Error al leer manifiesto de trazabilidad: {e}")
    else:
        report_fail("Falta el manifiesto dataset/golden_set_manifest.json")

    # 3. Validar Archivos Históricos Archivados en historico_32/
    hist_json_path = base_dir / "resultados" / "historico_32" / "eval_results_32.json"
    hist_csv_path = base_dir / "resultados" / "historico_32" / "eval_results_32.csv"

    if hist_json_path.exists() and hist_csv_path.exists():
        j_hash = compute_golden_set_hash(hist_json_path)
        c_hash = compute_golden_set_hash(hist_csv_path)
        if j_hash == HISTORICAL_JSON_HASH and c_hash == HISTORICAL_CSV_HASH:
            report_pass("Resultados históricos de 32 casos archivados en historico_32/ con hashes preservados")
        else:
            report_fail("Hashes de resultados históricos archivados en historico_32/ no coinciden")
    else:
        report_fail("Faltan resultados históricos archivados en resultados/historico_32/")

    # 4. Validar Estado de Resultados Activos (Estado A: Pendiente / Estado B: Completado Estricto)
    json_path = base_dir / "resultados" / "eval_results.json"
    csv_path = base_dir / "resultados" / "eval_results.csv"

    if not json_path.exists() and not csv_path.exists():
        report_pass("Estado previo al benchmark oficial de 15 casos confirmado: resultados activos ausentes y pendientes de nueva ejecución")
    elif json_path.exists() and csv_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)

            # Verification of complete official metadata
            if (
                json_data.get("total_cases") == 15 and
                json_data.get("selected_cases") == 15 and
                json_data.get("completed_cases") == 15 and
                json_data.get("infrastructure_errors") == 0 and
                json_data.get("skipped_cases") == 0 and
                json_data.get("is_complete") is True
            ):
                report_pass("Metadatos de completitud de ejecución oficial validados (15/15/15/0/0, is_complete=True)")
            else:
                report_fail("Ejecución activa no cumple los criterios de completitud oficial 15/15/15/0/0")

            if json_data.get("golden_set_sha256") == compute_golden_set_hash(golden_set_path):
                report_pass("golden_set_sha256 del resultado activo coincide con el Golden Set oficial")
            else:
                report_fail("golden_set_sha256 del resultado activo no coincide con el Golden Set oficial")

            detalles = json_data.get("detalles_casos", [])
            if len(detalles) == 15:
                report_pass("Artefacto JSON activo contiene exactamente 15 detalles de casos")
            else:
                report_fail(f"Artefacto JSON activo contiene {len(detalles)} detalles (se esperaban 15)")

            with open(csv_path, "r", encoding="utf-8") as f:
                csv_reader = list(csv.reader(f))

            if len(csv_reader) == 16:
                report_pass("Artefacto CSV activo contiene 16 filas (1 encabezado + 15 casos)")
            else:
                report_fail(f"Artefacto CSV activo contiene {len(csv_reader)} filas (se esperaban 16)")

            csv_header = csv_reader[0] if csv_reader else []
            expected_csv_cols = [
                "ID", "Categoria", "Estado_Ejecucion", "Intentos", "Error_Tecnico",
                "Pregunta", "Precision", "Cobertura", "Pertinencia", "Respuesta_Bot",
                "Solicitudes_Embedding", "Solicitudes_Generacion"
            ]
            if csv_header == expected_csv_cols:
                report_pass("Encabezado CSV activo verificado con todas las columnas obligatorias")
            else:
                report_fail(f"Encabezado CSV activo no coincide con columnas esperadas: {csv_header}")

            json_item_by_id = {d.get("id"): d for d in detalles if "id" in d}
            json_ids = set(json_item_by_id.keys())

            csv_rows_by_id = {int(row[0]): row for row in csv_reader[1:] if row and row[0].isdigit()}
            csv_ids = set(csv_rows_by_id.keys())

            if json_ids == OFFICIAL_15_IDS and csv_ids == OFFICIAL_15_IDS:
                report_pass("Coincidencia exacta de IDs entre Golden Set oficial de 15, JSON y CSV")
            else:
                report_fail("IDs de resultados activos no coinciden con los 15 oficiales")

            is_new_csv_format = "Estado_Ejecucion" in csv_header
            case_coherence_failed = False
            for case_id in sorted(list(OFFICIAL_15_IDS)):
                g_item = golden_item_by_id.get(case_id, {})
                j_item = json_item_by_id.get(case_id, {})
                c_row = csv_rows_by_id.get(case_id, [])

                c_errors = validate_case_coherence(
                    item_golden=g_item,
                    item_json=j_item,
                    csv_row=c_row,
                    is_new_format=is_new_csv_format,
                    tol=0.0001
                )
                if c_errors:
                    case_coherence_failed = True
                    for err in c_errors:
                        report_fail(err)

            if not case_coherence_failed:
                report_pass("Coherencia individual de categoría, pregunta, estado, intentos, error y métricas verificada para los 15 casos")

            # Check bounded range [0.0, 1.0] and valid status types
            metrics_valid = True
            requests_valid = True
            status_valid = True

            for d in detalles:
                p, c, pert = d.get("precision"), d.get("cobertura"), d.get("pertinencia")
                for val in (p, c, pert):
                    if val is not None and not (0.0 <= val <= 1.0):
                        metrics_valid = False

                emb_req = d.get("embedding_requests")
                gen_req = d.get("generation_requests")
                if not (isinstance(emb_req, int) and emb_req >= 0 and isinstance(gen_req, int) and gen_req >= 0):
                    requests_valid = False

                st = d.get("status")
                if st not in ("success", "model_failure"):
                    status_valid = False

            if metrics_valid:
                report_pass("Métricas individuales acotadas en el rango [0.0, 1.0]")
            else:
                report_fail("Existen métricas fuera del rango [0.0, 1.0]")

            if requests_valid:
                report_pass("Contadores Solicitudes_Embedding y Solicitudes_Generacion son enteros mayores o iguales a 0")
            else:
                report_fail("Contadores de solicitudes inválidos en el JSON activo")

            if status_valid:
                report_pass("Estados de caso en corrida oficial limitados a success y model_failure (sin infrastructure_error ni skipped)")
            else:
                report_fail("Existen estados no permitidos en la corrida oficial activa")

            recalc_globales, recalc_desglose = calculate_global_metrics(detalles)
            stored_globales = json_data.get("metricas_globales", {})
            stored_desglose = json_data.get("desglose_categoria", {})

            global_errors = validate_global_metrics(recalc_globales, stored_globales, tol=0.0001)
            if global_errors:
                for err in global_errors:
                    report_fail(err)
            else:
                report_pass("Métricas globales recalculadas coinciden con el JSON dentro de tolerancia 0.0001")

            cat_errors = validate_category_breakdown(recalc_desglose, stored_desglose, tol=0.0001)
            if cat_errors:
                for err in cat_errors:
                    report_fail(err)
            else:
                report_pass("Desglose por categoría recalculado coincide con el JSON dentro de tolerancia 0.0001")

        except Exception as e:
            report_fail(f"Error al validar resultados activos: {e}")
    else:
        report_fail("Incoherencia en resultados activos: solo uno de los archivos JSON/CSV existe")

    # 5. Detectar Incompatibilidad Documental
    doc06_path = repo_root / "documentacion" / "06_reporte_final.md"
    doc00_path = repo_root / "documentacion" / "00_linea_base_verificada.md"
    doc05_path = repo_root / "documentacion" / "05_banco_pruebas.md"

    if doc06_path.exists():
        doc06_content = doc06_path.read_text(encoding="utf-8")
        doc06_lower = doc06_content.lower()
        if (
            "BORRADOR PROVISIONAL" not in doc06_content
            and "Estado: REPORTE FINAL VERIFICADO" in doc06_content
            and "15 casos" in doc06_content
            and ("Fase 6B: COMPLETADA" in doc06_content or "Fase 6B" in doc06_content)
            and "pendiente" not in doc06_lower
            and "requiere confirmación" not in doc06_lower
        ):
            report_pass("documentacion/06_reporte_final.md declara el estado final verificado y el alcance oficial de 15 casos")
        else:
            report_fail("documentacion/06_reporte_final.md no declara el estado final verificado o conserva términos provisionales/pendientes")
    else:
        report_fail("Falta documentacion/06_reporte_final.md")

    if doc00_path.exists():
        doc00_content = doc00_path.read_text(encoding="utf-8")
        if "15 casos" in doc00_content and "RESUELTO_TECNICAMENTE_EN_FASE_5C" in doc00_content and "MITIGADA_POR_REDEFINICION_FORMAL_DEL_ALCANCE" in doc00_content:
            report_pass("documentacion/00_linea_base_verificada.md registra el estado de F5-001 y F5-002 para 15 casos")
        else:
            report_fail("documentacion/00_linea_base_verificada.md no registra adecuadamente los estados de F5-001 y F5-002")
    else:
        report_fail("Falta documentacion/00_linea_base_verificada.md")

    if doc05_path.exists():
        doc05_content = doc05_path.read_text(encoding="utf-8")
        if "15 casos" in doc05_content and "estratificado" in doc05_content.lower():
            report_pass("documentacion/05_banco_pruebas.md documenta el muestreo estratificado oficial de 15 casos")
        else:
            report_fail("documentacion/05_banco_pruebas.md no documenta el alcance oficial de 15 casos")
    else:
        report_fail("Falta documentacion/05_banco_pruebas.md")

    # 6. Verificar Protecciones del Runner (15 Casos)
    try:
        official_dir = base_dir / "resultados"
        rejected_ok = False
        try:
            validate_output_directory(output_dir_str=str(official_dir), is_partial=True, repo_root=repo_root, official_dir=official_dir)
        except ValueError:
            rejected_ok = True

        if rejected_ok:
            report_pass("Validación estricta de directorio de salida rechaza asignación del directorio oficial a corridas parciales")
        else:
            report_fail("runner no rechaza el directorio oficial para ejecuciones parciales")

        if not is_official_complete_run(15, 15, 15, 1, 0, is_partial=False) and is_official_complete_run(15, 15, 15, 0, 0, is_partial=False):
            report_pass("Reglas de completitud de ejecución oficial validadas con is_official_complete_run (15 casos)")
        else:
            report_fail("Fallo en reglas de completitud de is_official_complete_run para 15 casos")

    except Exception as e:
        report_fail(f"Error al verificar funciones de protección del runner: {e}")

    print(f"\n📊 Resumen de Integridad: {pass_count} pruebas pasadas, {fail_count} fallidas.")
    if fail_count > 0:
        print("💥 Verificación de integridad FALLADA")
        sys.exit(1)
    else:
        print("🎉 Verificación exitosa de la integridad del banco de pruebas (exit code 0)")
        sys.exit(0)

if __name__ == "__main__":
    main()
