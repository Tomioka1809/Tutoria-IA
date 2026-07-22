import csv
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

from tests.evaluation_support import (
    calculate_global_metrics,
    validate_output_directory,
    is_official_complete_run
)

def validate_global_metrics(
    recalc_globales: Dict[str, float],
    stored_globales: Dict[str, float],
    tol: float = 0.0001
) -> List[str]:
    """
    Valida que las métricas globales almacenadas contengan todas las claves requeridas
    y coincidan con las métricas recalculadas dentro de la tolerancia dada.
    """
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
    """
    Valida que el desglose por categoría almacenado coincida exactamente en categorías,
    conteo de casos y métricas numéricas con el desglose recalculado.
    """
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
    """
    Valida la coherencia de un caso individual entre Golden Set, JSON y CSV.
    Verifica que golden_question == json_question == csv_question.
    Normaliza Error_Tecnico (None == "") sin ignorar errores diferentes.
    """
    errors = []
    case_id = item_golden.get("id")

    # Categories
    g_cat = item_golden.get("categoria")
    j_cat = item_json.get("categoria")
    c_cat = csv_row[1] if len(csv_row) > 1 else None

    if not (g_cat == j_cat == c_cat):
        errors.append(f"Incoherencia de categoría para ID {case_id}: Golden='{g_cat}', JSON='{j_cat}', CSV='{c_cat}'")

    # Questions
    g_q = item_golden.get("pregunta")
    j_q = item_json.get("pregunta")
    if is_new_format:
        c_q = csv_row[5] if len(csv_row) > 5 else None
    else:
        c_q = csv_row[2] if len(csv_row) > 2 else None

    if not (g_q == j_q == c_q):
        errors.append(f"Incoherencia de pregunta para ID {case_id}")

    # Metrics & details JSON vs CSV
    if is_new_format:
        # CSV layout: ID(0), Categoria(1), Estado_Ejecucion(2), Intentos(3), Error_Tecnico(4), Pregunta(5), Precision(6), Cobertura(7), Pertinencia(8), Respuesta_Bot(9)
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
    else:
        # Historical CSV layout: ID(0), Categoria(1), Pregunta(2), Precision(3), Cobertura(4), Pertinencia(5), Respuesta_Bot(6)
        c_prec = float(csv_row[3]) if len(csv_row) > 3 and csv_row[3] != "" else None
        c_cob = float(csv_row[4]) if len(csv_row) > 4 and csv_row[4] != "" else None
        c_pert = float(csv_row[5]) if len(csv_row) > 5 and csv_row[5] != "" else None

        for m_name, j_val, c_val in (("precision", item_json.get("precision"), c_prec), ("cobertura", item_json.get("cobertura"), c_cob), ("pertinencia", item_json.get("pertinencia"), c_pert)):
            if j_val is not None and c_val is not None:
                if abs(j_val - c_val) > tol:
                    errors.append(f"Diferencia de {m_name} JSON/CSV histórico para ID {case_id}: JSON={j_val}, CSV={c_val}")
            elif j_val != c_val:
                errors.append(f"Diferencia nula de {m_name} en formato histórico para ID {case_id}")

    return errors

def main():
    print("🔍 Iniciando Verificador de Integridad y Robustez de Evaluación RAG (Fase 5A)...")
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

    # 1. Validar Golden Set
    golden_set_path = base_dir / "dataset" / "golden_set.json"
    if not golden_set_path.exists():
        report_fail("Golden Set no encontrado en dataset/golden_set.json")
        golden_set = []
        golden_ids = set()
    else:
        try:
            with open(golden_set_path, "r", encoding="utf-8") as f:
                golden_set = json.load(f)

            golden_ids = {item.get("id") for item in golden_set if "id" in item}

            if len(golden_set) == 32:
                report_pass("Golden Set posee exactamente 32 casos de prueba")
            else:
                report_fail(f"Golden Set tiene {len(golden_set)} casos (se esperaban 32)")

            ids = [item.get("id") for item in golden_set]
            if len(ids) == len(set(ids)) and set(ids) == set(range(1, 33)):
                report_pass("Golden Set contiene IDs únicos de 1 a 32")
            else:
                report_fail("IDs del Golden Set no son únicos o continuos de 1 a 32")

            valid_cats = {"facil", "ambiguo", "fuera_de_alcance"}
            cats = {item.get("categoria") for item in golden_set}
            if cats.issubset(valid_cats):
                report_pass("Categorías del Golden Set son válidas (facil, ambiguo, fuera_de_alcance)")
            else:
                report_fail(f"Categorías inválidas en Golden Set: {cats - valid_cats}")

            valid_fields = all(
                bool(item.get("pregunta")) and
                bool(item.get("respuesta_esperada")) and
                isinstance(item.get("articulos_referencia", []), list) and
                isinstance(item.get("palabras_clave_esperadas", []), list)
                for item in golden_set
            )
            if valid_fields:
                report_pass("Campos obligatorios del Golden Set validados")
            else:
                report_fail("Campos obligatorios vacíos o de tipo incorrecto en Golden Set")
        except Exception as e:
            report_fail(f"Error al leer Golden Set: {e}")
            golden_set = []
            golden_ids = set()

    golden_item_by_id = {item["id"]: item for item in golden_set if "id" in item}

    # 2. Validar Artefactos y Recalcular Métricas con Tolerancia (0.0001)
    json_path = base_dir / "resultados" / "eval_results.json"
    csv_path = base_dir / "resultados" / "eval_results.csv"

    if json_path.exists() and csv_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)

            detalles = json_data.get("detalles_casos", [])
            if len(detalles) == 32:
                report_pass("Artefacto JSON contiene 32 detalles de casos")
            else:
                report_fail(f"Artefacto JSON contiene {len(detalles)} detalles (se esperaban 32)")

            with open(csv_path, "r", encoding="utf-8") as f:
                csv_reader = list(csv.reader(f))

            if len(csv_reader) == 33:
                report_pass("Artefacto CSV contiene 33 filas (1 encabezado + 32 casos)")
            else:
                report_fail(f"Artefacto CSV contiene {len(csv_reader)} filas (se esperaban 33)")

            json_item_by_id = {d.get("id"): d for d in detalles if "id" in d}
            json_ids = set(json_item_by_id.keys())

            csv_header = csv_reader[0]
            is_new_csv_format = "Estado_Ejecucion" in csv_header

            csv_rows_by_id = {}
            for row in csv_reader[1:]:
                if row and row[0].isdigit():
                    csv_rows_by_id[int(row[0])] = row

            csv_ids = set(csv_rows_by_id.keys())

            if json_ids == golden_ids and csv_ids == golden_ids:
                report_pass("Coincidencia de IDs entre Golden Set real, JSON y CSV")
            else:
                report_fail("IDs no coinciden entre Golden Set real, JSON y CSV")

            # Validate Case Coherence using pure function
            case_coherence_failed = False
            for case_id in sorted(list(golden_ids)):
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
                report_pass("Coherencia de categorías, preguntas y métricas por ID entre Golden Set, JSON y CSV verificada")

            if not is_new_csv_format:
                report_pass("Formato CSV histórico detectado; comprobaciones de campos de ejecuciones nuevas excluidas adecuadamente")

            # Check individual metric ranges
            metrics_valid = True
            for d in detalles:
                p = d.get("precision")
                c = d.get("cobertura")
                pert = d.get("pertinencia")
                for val in (p, c, pert):
                    if val is not None and not (0.0 <= val <= 1.0):
                        metrics_valid = False

            if metrics_valid:
                report_pass("Métricas individuales acotadas en el rango [0.0, 1.0]")
            else:
                report_fail("Existen métricas fuera del rango [0.0, 1.0]")

            # Recalculate global metrics & category breakdown using pure functions
            recalc_globales, recalc_desglose = calculate_global_metrics(detalles)
            stored_globales = json_data.get("metricas_globales", {})
            stored_desglose = json_data.get("desglose_categoria", {})

            global_errors = validate_global_metrics(recalc_globales, stored_globales, tol=0.0001)
            if global_errors:
                for err in global_errors:
                    report_fail(err)
            else:
                report_pass("Métricas globales recalculadas coinciden exactamente con el JSON dentro de tolerancia 0.0001")

            cat_errors = validate_category_breakdown(recalc_desglose, stored_desglose, tol=0.0001)
            if cat_errors:
                for err in cat_errors:
                    report_fail(err)
            else:
                report_pass("Desglose por categoría recalculado coincide exactamente con el JSON dentro de tolerancia 0.0001")

        except Exception as e:
            report_fail(f"Error al validar artefactos JSON/CSV: {e}")
    else:
        report_fail("Faltan artefactos de resultados (eval_results.json o eval_results.csv)")

    # 3. Detectar Incompatibilidad Documental
    doc06_path = repo_root / "documentacion" / "06_reporte_final.md"
    doc00_path = repo_root / "documentacion" / "00_linea_base_verificada.md"

    if doc06_path.exists():
        with open(doc06_path, "r", encoding="utf-8") as f:
            doc06_content = f.read()

        if "86.98" in doc06_content or "95.83" in doc06_content or "92.50" in doc06_content:
            if ("no verificada" in doc06_content.lower() or "fase 5b" in doc06_content.lower() or "línea base histórica" in doc06_content.lower()):
                report_pass("documentacion/06_reporte_final.md documenta la inconsistencia de métricas históricas y la ejecución pendiente de Fase 5B")
            else:
                report_fail("documentacion/06_reporte_final.md presenta cifras 86.98%/95.83%/92.50% como resultados finales verificados")
        else:
            report_pass("documentacion/06_reporte_final.md ha retirado afirmaciones de métricas no verificadas")
    else:
        report_fail("Falta documentacion/06_reporte_final.md")

    if doc00_path.exists():
        with open(doc00_path, "r", encoding="utf-8") as f:
            doc00_content = f.read()

        if "F5-001" in doc00_content and "EN_CORRECCION_FASE_5A" in doc00_content:
            report_pass("documentacion/00_linea_base_verificada.md registra el hallazgo F5-001 en EN_CORRECCION_FASE_5A")
        else:
            report_fail("documentacion/00_linea_base_verificada.md NO contiene F5-001 en estado EN_CORRECCION_FASE_5A")
    else:
        report_fail("Falta documentacion/00_linea_base_verificada.md")

    # 4. Verificar Protecciones del Runner mediante Funciones Puras
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

        if not is_official_complete_run(32, 32, 32, 1, 0, is_partial=False) and is_official_complete_run(32, 32, 32, 0, 0, is_partial=False):
            report_pass("Reglas de completitud de ejecución oficial validadas con is_official_complete_run")
        else:
            report_fail("Fallo en reglas de completitud de is_official_complete_run")

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
