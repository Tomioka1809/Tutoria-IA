"""Genera los graficos de la evaluacion del RAG desde los informes JSON.

No toca la base de datos ni Gemini: lee lo que dejaron `run_eval_v2`,
`calibrar_umbral` y `calibrar_peso_autoridad`. Asi los graficos se rehacen
cuantas veces haga falta sin volver a gastar cuota, y se pueden regenerar desde
un informe viejo para comparar.

Las funciones que preparan los datos estan separadas del dibujo, porque lo que
puede estar mal es el calculo y no el color de la barra.

Uso:
    python -m scripts.graficar_evaluacion
    python -m scripts.graficar_evaluacion --informe tests/resultados/otro.json
"""
import argparse
import json
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from scripts.metricas_rag import curva_recall_media  # noqa: E402

RESULTADOS = os.path.join(BACKEND_DIR, "tests", "resultados")
INFORME_POR_DEFECTO = os.path.join(RESULTADOS, "fase5_eval_v2_corpus_completo.json")
CALIBRACION_UMBRAL = os.path.join(RESULTADOS, "fase3_calibracion.json")
CALIBRACION_PESO = os.path.join(RESULTADOS, "fase4_calibracion_peso.json")

# Paleta sobria y distinguible tambien en escala de grises, porque estos
# graficos terminan impresos en un informe.
AZUL = "#2B6CB0"
VERDE = "#2F855A"
NARANJA = "#C05621"
GRIS = "#718096"
ROJO = "#C53030"


# --------------------------------------------------------------------------
# Preparacion de datos (pura y comprobable)
# --------------------------------------------------------------------------

def acierto_por_dominio(detalle: list[dict]) -> list[dict]:
    """Aciertos de articulo y de documento agrupados por dominio."""
    en_alcance = [r for r in detalle if not r["fuera_de_alcance"]]
    dominios = sorted({r["dominio"] for r in en_alcance})

    filas = []
    for d in dominios:
        casos = [r for r in en_alcance if r["dominio"] == d]
        con_art = [r for r in casos if r.get("acierto_articulo") is not None]
        filas.append({
            "dominio": d,
            "casos": len(casos),
            "articulo_aciertos": sum(1 for r in con_art if r["acierto_articulo"]),
            "articulo_evaluables": len(con_art),
            "documento_aciertos": sum(1 for r in casos if r.get("acierto_documento")),
            "documento_evaluables": len(casos),
        })
    return filas


def curva_recall(detalle: list[dict]) -> tuple[list[int], list[float]]:
    """Recall@k medio por k. Delega en metricas_rag para no tener dos versiones."""
    curva = curva_recall_media(detalle)
    if not curva:
        return [], []
    ks = sorted(int(k) for k in curva)
    return ks, [curva[str(k)] for k in ks]


def posiciones_primer_acierto(detalle: list[dict]) -> list[int]:
    return [
        r["posicion_primer_acierto"]
        for r in detalle
        if not r["fuera_de_alcance"] and r.get("posicion_primer_acierto")
    ]


def curva_umbral(calibracion: dict) -> tuple[list[float], list[float], list[int]]:
    """Recall en alcance y falsos positivos para cada umbral candidato.

    Se calcula sobre la distancia minima que alcanza cada consulta: si esa
    distancia supera el umbral, no se recupera nada y el sistema se abstiene.
    """
    en_alcance = [d for _, d in calibracion["en_alcance"]]
    fuera = [d for _, d in calibracion["fuera_de_alcance"]]
    if not en_alcance:
        return [], [], []

    umbrales = [round(0.20 + 0.01 * i, 2) for i in range(31)]
    recalls = [sum(1 for d in en_alcance if d <= u) / len(en_alcance) for u in umbrales]
    falsos = [sum(1 for d in fuera if d <= u) for u in umbrales]
    return umbrales, recalls, falsos


def serie_peso_autoridad(calibracion: dict) -> tuple[list[float], list[float]]:
    med = calibracion["mediciones"]
    return [m["peso"] for m in med], [m["acierto_articulo"] for m in med]


def metricas_resumen(resumen: dict) -> list[tuple[str, float]]:
    """Metricas de titular en una escala comun 0-1, en orden de lectura."""
    pares = [
        ("Acierto de documento", resumen.get("acierto_documento")),
        ("Acierto de artículo", resumen.get("acierto_articulo")),
        ("Recall@k", resumen.get("recall_at_k")),
        ("Cobertura de palabras", resumen.get("cobertura_palabras_media")),
        ("MRR", resumen.get("mrr")),
        ("nDCG@k", resumen.get("ndcg_at_k")),
        ("F1@k", resumen.get("f1_at_k")),
        ("Precision@k", resumen.get("precision_at_k")),
    ]
    return [(n, v) for n, v in pares if v is not None]


# --------------------------------------------------------------------------
# Dibujo
# --------------------------------------------------------------------------

def _guardar(fig, destino: str, nombre: str) -> str:
    ruta = os.path.join(destino, nombre)
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    return ruta


def graficar(informe: dict, destino: str) -> list[str]:
    import matplotlib
    matplotlib.use("Agg")  # sin servidor grafico: esto corre en consola o CI
    import matplotlib.pyplot as plt
    import numpy as np

    plt.rcParams.update({"font.size": 9, "axes.grid": True, "grid.alpha": 0.25})

    detalle = informe["detalle"]
    resumen = informe["resumen"]
    limite = informe.get("politica", {}).get("limit", 6)
    generados = []

    # 1. Acierto por dominio -------------------------------------------------
    filas = acierto_por_dominio(detalle)
    if filas:
        fig, ax = plt.subplots(figsize=(9, 4.2))
        x = np.arange(len(filas))
        ancho = 0.38
        art = [f["articulo_aciertos"] / f["articulo_evaluables"] if f["articulo_evaluables"] else 0
               for f in filas]
        doc = [f["documento_aciertos"] / f["documento_evaluables"] for f in filas]

        ax.bar(x - ancho / 2, doc, ancho, label="Acierto de documento", color=AZUL)
        ax.bar(x + ancho / 2, art, ancho, label="Acierto de artículo", color=NARANJA)

        for i, f in enumerate(filas):
            ax.text(i - ancho / 2, doc[i] + 0.02,
                    f"{f['documento_aciertos']}/{f['documento_evaluables']}",
                    ha="center", fontsize=7.5)
            if f["articulo_evaluables"]:
                ax.text(i + ancho / 2, art[i] + 0.02,
                        f"{f['articulo_aciertos']}/{f['articulo_evaluables']}",
                        ha="center", fontsize=7.5)
            else:
                # Sin casos que citen articulado la barra vale 0 y podria leerse
                # como un fallo; se marca que no aplica.
                ax.text(i + ancho / 2, 0.02, "n/a", ha="center", fontsize=7.5, color=GRIS)

        ax.set_xticks(x)
        ax.set_xticklabels([f["dominio"] for f in filas], rotation=20, ha="right")
        ax.set_ylim(0, 1.15)
        ax.set_ylabel("proporción de aciertos")
        ax.set_title("Acierto de recuperación por dominio")
        # Fuera del area de datos: casi todas las barras llegan a 1.0 y una
        # leyenda dentro tapa los dominios de la derecha.
        ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.42), ncol=2, frameon=False)
        generados.append(_guardar(fig, destino, "01_acierto_por_dominio.png"))
        plt.close(fig)

    # 2. Matriz de confusion de la abstencion --------------------------------
    ab = resumen.get("abstencion")
    if ab:
        fig, ax = plt.subplots(figsize=(4.6, 4))
        matriz = np.array([[ab["tp"], ab["fn"]], [ab["fp"], ab["tn"]]])
        ax.imshow(matriz, cmap="Blues", vmin=0, vmax=max(matriz.max(), 1))
        ax.set_xticks([0, 1], ["se abstuvo", "respondió"])
        ax.set_yticks([0, 1], ["fuera de alcance", "en alcance"])
        for (i, j), v in np.ndenumerate(matriz):
            color = "white" if v > matriz.max() * 0.6 else "black"
            ax.text(j, i, str(v), ha="center", va="center", fontsize=17, color=color)
        ax.set_title(
            f"Decisión de abstención\nF1 {ab['f1']:.2f} · precisión {ab['precision']:.2f}"
            f" · recall {ab['recall']:.2f}"
        )
        ax.grid(False)
        pie = (f"n={ab['n']}. Solo {ab['tp'] + ab['fn']} casos fuera de alcance: "
               "muestra insuficiente para concluir.")
        fig.text(0.5, -0.04, pie, ha="center", fontsize=7.5, color=ROJO)
        generados.append(_guardar(fig, destino, "02_confusion_abstencion.png"))
        plt.close(fig)

    # 3. Curva Recall@k ------------------------------------------------------
    ks, medias = curva_recall(detalle)
    if ks:
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(ks, medias, marker="o", color=VERDE, linewidth=2)
        ax.axvline(limite, color=ROJO, linestyle="--", linewidth=1.2)
        ax.text(limite + 0.15, 0.05, f"limit={limite} (producción)", color=ROJO, fontsize=8)
        en_limite = medias[ks.index(limite)] if limite in ks else None
        if en_limite is not None:
            # Con un fondo opaco: la linea del limite pasa justo por encima y sin
            # el la etiqueta quedaba ilegible.
            ax.annotate(f"Recall@{limite} = {en_limite:.2f}", (limite, en_limite),
                        textcoords="offset points", xytext=(10, -18), fontsize=9,
                        color=VERDE,
                        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=VERDE, lw=0.8))
        ax.set_xlabel("k (fragmentos entregados al LLM)")
        ax.set_ylabel("Recall@k medio")
        ax.set_ylim(0, 1.05)
        ax.set_xticks(ks[::2])
        ax.set_title("Cuánto se ganaría entregando más fragmentos")
        generados.append(_guardar(fig, destino, "03_curva_recall_k.png"))
        plt.close(fig)

    # 4. Posicion del primer acierto -----------------------------------------
    posiciones = posiciones_primer_acierto(detalle)
    if posiciones:
        fig, ax = plt.subplots(figsize=(6.5, 3.8))
        topes = range(1, max(posiciones) + 2)
        ax.hist(posiciones, bins=[b - 0.5 for b in topes], color=AZUL, edgecolor="white")
        ax.set_xticks(range(1, max(posiciones) + 1))
        ax.set_xlabel("posición del primer fragmento relevante")
        ax.set_ylabel("casos")
        mrr = resumen.get("mrr")
        ax.set_title(f"Dónde aparece el primer acierto (MRR {mrr:.3f})" if mrr
                     else "Dónde aparece el primer acierto")
        generados.append(_guardar(fig, destino, "04_posicion_primer_acierto.png"))
        plt.close(fig)

    # 5. Resumen de metricas -------------------------------------------------
    pares = metricas_resumen(resumen)
    if pares:
        fig, ax = plt.subplots(figsize=(7, 4))
        nombres = [n for n, _ in pares][::-1]
        valores = [v for _, v in pares][::-1]
        colores = [VERDE if v >= 0.8 else (NARANJA if v >= 0.5 else GRIS) for v in valores]
        ax.barh(nombres, valores, color=colores)
        for i, v in enumerate(valores):
            ax.text(v + 0.015, i, f"{v:.3f}", va="center", fontsize=8.5)
        techo = resumen.get("techo_precision_at_k")
        if techo is not None and "Precision@k" in nombres:
            # Sin su techo, una precision de 0.42 se lee como un mal resultado
            # cuando el maximo alcanzable es 0.53.
            ax.scatter([techo], [nombres.index("Precision@k")], marker="|", s=260,
                       color=ROJO, zorder=3, label=f"techo de Precision@k ({techo:.2f})")
            ax.legend(loc="lower right", fontsize=8)
        ax.set_xlim(0, 1.12)
        ax.set_xlabel("valor (0 a 1)")
        ax.set_title("Métricas de recuperación del RAG")
        generados.append(_guardar(fig, destino, "05_resumen_metricas.png"))
        plt.close(fig)

    # 6. Calibracion del umbral ----------------------------------------------
    if os.path.exists(CALIBRACION_UMBRAL):
        with open(CALIBRACION_UMBRAL, encoding="utf-8") as fh:
            cal = json.load(fh)
        umbrales, recalls, falsos = curva_umbral(cal)
        if umbrales:
            fig, ax = plt.subplots(figsize=(7.5, 4))
            ax.plot(umbrales, recalls, color=VERDE, linewidth=2, label="recall en alcance")
            ax.set_xlabel("umbral de distancia coseno")
            ax.set_ylabel("recall en alcance", color=VERDE)
            ax.set_ylim(0, 1.05)

            ax2 = ax.twinx()
            ax2.plot(umbrales, falsos, color=ROJO, linewidth=2, linestyle="--",
                     label="falsos positivos fuera de alcance")
            ax2.set_ylabel("falsos positivos", color=ROJO)
            ax2.set_ylim(0, max(max(falsos), 1) + 0.5)
            ax2.grid(False)

            actual = informe.get("politica", {}).get("max_cosine_distance")
            if actual:
                ax.axvline(actual, color="black", linestyle=":", linewidth=1.4)
                ax.text(actual + 0.003, 0.08, f"valor calibrado {actual}", fontsize=8)

            ax.set_title("Calibración del umbral: recall contra falsos positivos")
            generados.append(_guardar(fig, destino, "06_calibracion_umbral.png"))
            plt.close(fig)

    # 7. Calibracion del peso de autoridad -----------------------------------
    if os.path.exists(CALIBRACION_PESO):
        with open(CALIBRACION_PESO, encoding="utf-8") as fh:
            cal = json.load(fh)
        pesos, aciertos = serie_peso_autoridad(cal)
        if pesos:
            fig, ax = plt.subplots(figsize=(7, 3.8))
            ax.plot(pesos, aciertos, marker="o", color=AZUL, linewidth=2)
            recomendado = cal.get("peso_recomendado")
            if recomendado is not None:
                ax.axvline(recomendado, color=ROJO, linestyle="--", linewidth=1.2)
                ax.text(recomendado + 0.03, min(aciertos) + 0.01,
                        f"mínimo que alcanza el óptimo ({recomendado})", fontsize=8, color=ROJO)
            ax.set_xlabel("peso de autoridad")
            ax.set_ylabel("acierto de artículo")
            ax.set_title("Barrido del peso de autoridad")
            generados.append(_guardar(fig, destino, "07_calibracion_peso_autoridad.png"))
            plt.close(fig)

    # 8. Latencia ------------------------------------------------------------
    latencias = [r["latencia_recuperacion_ms"] for r in detalle
                 if r.get("latencia_recuperacion_ms") is not None]
    if latencias:
        fig, ax = plt.subplots(figsize=(6.5, 3.4))
        ax.hist(latencias, bins=12, color=GRIS, edgecolor="white")
        lat = resumen.get("latencia_recuperacion_ms", {})
        for etiqueta, color in (("p50", VERDE), ("p95", NARANJA)):
            valor = lat.get(etiqueta)
            if valor:
                ax.axvline(valor, color=color, linestyle="--", linewidth=1.4)
                ax.text(valor, ax.get_ylim()[1] * 0.9, f" {etiqueta} {valor:.0f} ms",
                        color=color, fontsize=8)
        ax.set_xlabel("milisegundos")
        ax.set_ylabel("consultas")
        ax.set_title("Latencia de recuperación (sin generación)")
        generados.append(_guardar(fig, destino, "08_latencia_recuperacion.png"))
        plt.close(fig)

    return generados


def main() -> int:
    parser = argparse.ArgumentParser(description="Grafica la evaluacion del RAG")
    parser.add_argument("--informe", default=INFORME_POR_DEFECTO)
    parser.add_argument("--destino", default=os.path.join(RESULTADOS, "graficos"))
    args = parser.parse_args()

    if not os.path.exists(args.informe):
        print(f"No existe el informe {args.informe}. Corre antes tests.run_eval_v2 --json ...")
        return 1

    with open(args.informe, encoding="utf-8") as fh:
        informe = json.load(fh)

    os.makedirs(args.destino, exist_ok=True)
    generados = graficar(informe, args.destino)

    print(f"Informe   : {args.informe}")
    print(f"Generados : {len(generados)} graficos en {args.destino}")
    for ruta in generados:
        print(f"  - {os.path.basename(ruta)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
