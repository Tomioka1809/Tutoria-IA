import asyncio
import csv
import io
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add parent backend directory to sys.path to allow imports
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Ensure all SQLAlchemy ORM models are registered
import app.infrastructure.database.base  # noqa

from tests.test_retrieval import run_retrieval_benchmark
from tests.test_generation import run_generation_benchmark
from tests.evaluation_support import (
    EvaluationConfig,
    compute_golden_set_hash,
    atomic_write_artifact_pair,
    calculate_global_metrics,
    sanitize_secret_message,
    truncate_technical_error,
    validate_output_directory,
    is_official_complete_run,
    classify_case_result,
    filter_golden_set_cases
)

def build_export_payloads(
    consolidated: List[Dict[str, Any]],
    config: EvaluationConfig,
    golden_hash: str,
    total_golden_cases: int,
    selected_items: List[Dict[str, Any]],
    completed_count: int,
    infra_error_count: int,
    skipped_count: int,
    is_complete: bool,
    cat_summary: Dict[str, Any],
    globales: Dict[str, float]
) -> Tuple[Dict[str, Any], str]:
    """Construye pura y atómicamente la estructura del diccionario JSON y la cadena CSV exportables."""
    export_payload = {
        "schema_version": "1.0.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": config.run_id,
        "golden_set_path": "dataset/golden_set.json",
        "golden_set_sha256": golden_hash,
        "total_cases": total_golden_cases,
        "selected_cases": len(selected_items),
        "completed_cases": completed_count,
        "infrastructure_errors": infra_error_count,
        "skipped_cases": skipped_count,
        "is_complete": is_complete,
        "models": {
            "generation_model": "gemini-2.5-flash",
            "embedding_model": "gemini-embedding-2"
        },
        "evaluation_config": {
            "max_retries": config.max_retries,
            "initial_backoff_seconds": config.initial_backoff,
            "max_backoff_seconds": config.max_backoff,
            "inter_case_delay_seconds": config.inter_case_delay,
            "generation_min_interval_seconds": config.generation_min_interval,
            "retry_after_safety_seconds": config.retry_after_safety,
            "case_limit": config.case_limit,
            "case_ids": config.case_ids
        },
        "metric_definitions": {
            "precision": "Proporción de fragmentos recuperados en Top-K que contienen palabras clave o referencias esperadas",
            "cobertura": "Proporción de artículos de referencia esperados que fueron recuperados por pgvector",
            "pertinencia": "Heurística léxica de pertinencia y abstención para fuera de alcance"
        },
        "metricas_globales": globales,
        "desglose_categoria": cat_summary,
        "detalles_casos": consolidated
    }

    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow([
        "ID", "Categoria", "Estado_Ejecucion", "Intentos", "Error_Tecnico",
        "Pregunta", "Precision", "Cobertura", "Pertinencia", "Respuesta_Bot",
        "Solicitudes_Embedding", "Solicitudes_Generacion"
    ])
    for row in consolidated:
        writer.writerow([
            row["id"],
            row["categoria"],
            row["status"],
            row["attempts"],
            truncate_technical_error(row.get("technical_error") or ""),
            row["pregunta"],
            row["precision"] if row["precision"] is not None else "",
            row["cobertura"] if row["cobertura"] is not None else "",
            row["pertinencia"] if row["pertinencia"] is not None else "",
            row["bot_response"].replace("\n", " ") if row.get("bot_response") else "",
            row.get("embedding_requests", 0),
            row.get("generation_requests", 0)
        ])

    return export_payload, csv_buffer.getvalue()

async def main():
    print("\n" + "="*80)
    print(" 🚀 EJECUTANDO BANCO DE PRUEBAS DEL CHATBOT RAG — TUTORIA (PAPER IEEE)")
    print("="*80 + "\n")

    base_dir = Path(__file__).resolve().parent
    repo_root = backend_dir.parent
    golden_set_path = base_dir / "dataset" / "golden_set.json"
    official_results_dir = base_dir / "resultados"

    golden_hash = compute_golden_set_hash(golden_set_path)

    with open(golden_set_path, "r", encoding="utf-8") as f:
        full_golden_set = json.load(f)

    total_golden_cases = len(full_golden_set)
    valid_ids = {item["id"] for item in full_golden_set}

    # Config and selection
    config = EvaluationConfig(valid_ids=valid_ids)

    # Real detection of partial runs: any configured filter defines a partial run
    is_partial = (
        config.case_limit is not None or
        config.case_ids is not None
    )

    selected_items = filter_golden_set_cases(
        golden_set=full_golden_set,
        case_limit=config.case_limit,
        case_ids=config.case_ids
    )

    selected_ids = {item["id"] for item in selected_items}

    # Validate output directory policy
    try:
        target_output_dir = validate_output_directory(
            output_dir_str=config.output_dir,
            is_partial=is_partial,
            repo_root=repo_root,
            official_dir=official_results_dir
        )
    except ValueError as val_err:
        print(f"❌ ERROR DE CONFIGURACIÓN DE SALIDA: {val_err}")
        sys.exit(1)

    print(f"1️⃣ Evaluando etapa de Recuperación Vectorial ({len(selected_items)} casos seleccionados)...")
    retrieval_results = await run_retrieval_benchmark(str(golden_set_path), config=config, items=selected_items)
    print(f"   ✓ {len(retrieval_results)} casos de prueba procesados en Recuperación.")

    print(f"\n2️⃣ Evaluando etapa de Generación y Grounding ({len(selected_items)} casos seleccionados)...")
    generation_results = await run_generation_benchmark(str(golden_set_path), config=config, items=selected_items)
    print(f"   ✓ {len(generation_results)} respuestas generadas y evaluadas.")

    # Merge & classification
    ret_map = {r["id"]: r for r in retrieval_results}
    gen_map = {g["id"]: g for g in generation_results}

    consolidated = []
    skipped_count = 0
    infra_error_count = 0
    completed_count = 0

    for item in full_golden_set:
        item_id = item["id"]
        cat = item["categoria"]
        question = item["pregunta"]

        if item_id not in selected_ids:
            skipped_count += 1
            consolidated.append({
                "id": item_id,
                "categoria": cat,
                "pregunta": question,
                "status": "skipped",
                "attempts": 0,
                "embedding_requests": 0,
                "generation_requests": 0,
                "technical_error": None,
                "precision": None,
                "cobertura": None,
                "pertinencia": None,
                "bot_response": ""
            })
            continue

        ret = ret_map.get(item_id, {})
        gen = gen_map.get(item_id, {})

        is_ret_infra = ret.get("status") == "infrastructure_error"
        is_gen_infra = gen.get("status") == "infrastructure_error"

        emb_req = ret.get("embedding_requests", 0) + gen.get("embedding_requests", 0)
        gen_req = gen.get("generation_requests", 0)

        if is_ret_infra or is_gen_infra:
            infra_error_count += 1
            tech_err = ret.get("technical_error") or gen.get("technical_error") or "Fallo de infraestructura no especificado"
            attempts = max(ret.get("attempts", 1), gen.get("attempts", 1))
            consolidated.append({
                "id": item_id,
                "categoria": cat,
                "pregunta": question,
                "status": "infrastructure_error",
                "attempts": attempts,
                "embedding_requests": emb_req,
                "generation_requests": gen_req,
                "technical_error": truncate_technical_error(tech_err),
                "precision": None,
                "cobertura": None,
                "pertinencia": None,
                "bot_response": gen.get("bot_response", "")
            })
        else:
            completed_count += 1
            prec = ret.get("precision", 0.0)
            cob = ret.get("cobertura", 0.0)
            pert = gen.get("pertinencia", 0.0)
            attempts = max(ret.get("attempts", 1), gen.get("attempts", 1))

            status = classify_case_result(
                categoria=cat,
                cobertura=cob,
                pertinencia=pert
            )

            consolidated.append({
                "id": item_id,
                "categoria": cat,
                "pregunta": question,
                "status": status,
                "attempts": attempts,
                "embedding_requests": emb_req,
                "generation_requests": gen_req,
                "technical_error": None,
                "precision": prec,
                "cobertura": cob,
                "pertinencia": pert,
                "bot_response": gen.get("bot_response", "")
            })

    is_complete = is_official_complete_run(
        total_cases=total_golden_cases,
        selected_cases=len(selected_items),
        completed_cases=completed_count,
        infra_errors=infra_error_count,
        skipped=skipped_count,
        is_partial=is_partial
    )

    # Compute global metrics from evaluable cases
    globales, cat_summary = calculate_global_metrics(consolidated)

    print("\n" + "="*80)
    print(" 📊 RESUMEN DE MÉTRICAS GLOBALES DEL SISTEMA RAG")
    print("="*80)
    print(f" ► Estado de Ejecución  : {'OFICIAL COMPLETA' if is_complete else 'PARCIAL / INCOMPLETA'}")
    print(f" ► Precisión Promedio  : {globales['precision_global'] * 100:.2f}%")
    print(f" ► Cobertura Promedio  : {globales['cobertura_global'] * 100:.2f}%")
    print(f" ► Pertinencia Promedio: {globales['pertinencia_global'] * 100:.2f}%")
    print("="*80)

    print("\n 📈 DESGLOSE POR CATEGORÍA DE CASOS DE PRUEBA:")
    print("-" * 70)
    print(f"{'Categoría':<20} | {'Precisión':<12} | {'Cobertura':<12} | {'Pertinencia':<12}")
    print("-" * 70)

    for cat_name, metrics in cat_summary.items():
        print(f"{cat_name:<20} | {metrics['precision']*100:6.2f}%      | {metrics['cobertura']*100:6.2f}%      | {metrics['pertinencia']*100:6.2f}%")

    print("-" * 70)

    # Build export payloads using pure function
    export_payload, csv_str = build_export_payloads(
        consolidated=consolidated,
        config=config,
        golden_hash=golden_hash,
        total_golden_cases=total_golden_cases,
        selected_items=selected_items,
        completed_count=completed_count,
        infra_error_count=infra_error_count,
        skipped_count=skipped_count,
        is_complete=is_complete,
        cat_summary=cat_summary,
        globales=globales
    )

    json_str = json.dumps(export_payload, ensure_ascii=False, indent=2)

    # Rule: If official run attempt but is NOT complete (e.g. infra_error_count > 0 or filters applied)
    if not is_partial and not is_complete:
        print("❌ ERROR: La ejecución oficial presentó errores de infraestructura.")
        print("   No se modificarán eval_results.json ni eval_results.csv en el directorio oficial.")
        print(f"   Errores de infraestructura registrados: {infra_error_count}")
        sys.exit(1)

    # Atomic write to target_output_dir
    output_json_path = target_output_dir / "eval_results.json"
    output_csv_path = target_output_dir / "eval_results.csv"

    atomic_write_artifact_pair(output_json_path, json_str, output_csv_path, csv_str)

    print(f"\n✅ Artefactos exportados atómicamente:")
    print(f"   📄 JSON: {output_json_path}")
    print(f"   📊 CSV : {output_csv_path}\n")

    if not is_complete:
        print("⚠️ AVISO: Ejecución parcial o incompleta procesada correctamente en EVAL_OUTPUT_DIR.")
        print("   Finalizando con código 1 (is_complete=false).")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
