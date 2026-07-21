import asyncio
import csv
import json
import os
import sys
from datetime import datetime

# Add parent backend directory to sys.path to allow imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Ensure all SQLAlchemy ORM models are registered
import app.infrastructure.database.base  # noqa

from tests.test_retrieval import run_retrieval_benchmark
from tests.test_generation import run_generation_benchmark

async def main():
    print("\n" + "="*80)
    print(" 🚀 EJECUTANDO BANCO DE PRUEBAS DEL CHATBOT RAG — TUTORIA (PAPER IEEE)")
    print("="*80 + "\n")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    golden_set_path = os.path.join(base_dir, "dataset", "golden_set.json")
    results_dir = os.path.join(base_dir, "resultados")

    os.makedirs(results_dir, exist_ok=True)

    print("1️⃣ Evaluando etapa de Recuperación Vectorial (Retrieval & pgvector)...")
    retrieval_results = await run_retrieval_benchmark(golden_set_path)
    print(f"   ✓ {len(retrieval_results)} casos de prueba procesados en Recuperación.")

    print("\n2️⃣ Evaluando etapa de Generación y Grounding (Gemini 2.5 Flash)...")
    generation_results = await run_generation_benchmark(golden_set_path)
    print(f"   ✓ {len(generation_results)} respuestas generadas y evaluadas.")

    # Merge results by ID
    ret_map = {r["id"]: r for r in retrieval_results}
    gen_map = {g["id"]: g for g in generation_results}

    consolidated = []
    cat_metrics = {
        "facil": {"precision": [], "cobertura": [], "pertinencia": []},
        "ambiguo": {"precision": [], "cobertura": [], "pertinencia": []},
        "fuera_de_alcance": {"precision": [], "cobertura": [], "pertinencia": []}
    }

    for item_id in ret_map:
        ret = ret_map[item_id]
        gen = gen_map.get(item_id, {})
        
        cat = ret["categoria"]
        prec = ret["precision"]
        cob = ret["cobertura"]
        pert = gen.get("pertinencia", 0.0)

        cat_metrics[cat]["precision"].append(prec)
        cat_metrics[cat]["cobertura"].append(cob)
        cat_metrics[cat]["pertinencia"].append(pert)

        consolidated.append({
            "id": item_id,
            "categoria": cat,
            "pregunta": ret["pregunta"],
            "precision": prec,
            "cobertura": cob,
            "pertinencia": pert,
            "bot_response": gen.get("bot_response", "")
        })

    # Calculate overall averages
    avg_prec = sum(c["precision"] for c in consolidated) / len(consolidated)
    avg_cob = sum(c["cobertura"] for c in consolidated) / len(consolidated)
    avg_pert = sum(c["pertinencia"] for c in consolidated) / len(consolidated)

    print("\n" + "="*80)
    print(" 📊 RESUMEN DE MÉTRICAS GLOBALES DEL SISTEMA RAG")
    print("="*80)
    print(f" ► Precisión Promedio  : {avg_prec * 100:.2f}%")
    print(f" ► Cobertura Promedio  : {avg_cob * 100:.2f}%")
    print(f" ► Pertinencia Promedio: {avg_pert * 100:.2f}%")
    print("="*80)

    print("\n 📈 DESGLOSE POR CATEGORÍA DE CASOS DE PRUEBA:")
    print("-" * 70)
    print(f"{'Categoría':<20} | {'Precisión':<12} | {'Cobertura':<12} | {'Pertinencia':<12}")
    print("-" * 70)

    cat_summary = {}
    for cat_name, values in cat_metrics.items():
        n = len(values["precision"])
        c_prec = sum(values["precision"]) / n if n > 0 else 0
        c_cob = sum(values["cobertura"]) / n if n > 0 else 0
        c_pert = sum(values["pertinencia"]) / n if n > 0 else 0

        cat_summary[cat_name] = {
            "total_casos": n,
            "precision": round(c_prec, 4),
            "cobertura": round(c_cob, 4),
            "pertinencia": round(c_pert, 4)
        }
        print(f"{cat_name:<20} | {c_prec*100:6.2f}%      | {c_cob*100:6.2f}%      | {c_pert*100:6.2f}%")

    print("-" * 70)

    # Export to JSON
    output_json_path = os.path.join(base_dir, "resultados", "eval_results.json")
    export_payload = {
        "timestamp": datetime.now().isoformat(),
        "total_casos": len(consolidated),
        "metricas_globales": {
            "precision_global": round(avg_prec, 4),
            "cobertura_global": round(avg_cob, 4),
            "pertinencia_global": round(avg_pert, 4)
        },
        "desglose_categoria": cat_summary,
        "detalles_casos": consolidated
    }

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(export_payload, f, ensure_ascii=False, indent=2)
        f.flush()

    # Export to CSV
    output_csv_path = os.path.join(base_dir, "resultados", "eval_results.csv")
    with open(output_csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Categoria", "Pregunta", "Precision", "Cobertura", "Pertinencia", "Respuesta_Bot"])
        for row in consolidated:
            writer.writerow([
                row["id"],
                row["categoria"],
                row["pregunta"],
                row["precision"],
                row["cobertura"],
                row["pertinencia"],
                row["bot_response"].replace("\n", " ")
            ])
        f.flush()

    print(f"\n✅ Resultados exportados exitosamente para cita en el Paper IEEE:")
    print(f"   📄 JSON: {output_json_path}")
    print(f"   📊 CSV : {output_csv_path}\n")

if __name__ == "__main__":
    asyncio.run(main())
