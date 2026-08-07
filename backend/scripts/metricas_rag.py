"""Metricas de recuperacion y de abstencion del RAG.

Funciones puras, sin base de datos ni Gemini, para que se puedan probar solas y
recalcular sobre un informe ya guardado sin volver a gastar cuota.

Tres decisiones que conviene conocer antes de leer los numeros:

1. **La relevancia es estricta.** Un fragmento cuenta como relevante solo si
   coinciden el articulo *y* el documento. La version anterior comparaba el
   articulo suelto contra el conjunto de articulos recuperados, y "Art. 14"
   existe en casi todos los reglamentos: bastaba recuperar el Art. 14 de
   cualquier norma para dar por acertada la cita del Reglamento de Tutoria.

2. **Precision@k tiene techo.** Si un caso espera una sola cita y se entregan
   seis fragmentos, la precision no puede pasar de 1/6 por mas perfecta que sea
   la recuperacion. Por eso se reporta junto a su techo `min(|Rel|, k)/k`, y
   suelta no significa nada.

3. **El positivo de la abstencion es "el sistema se calla".** Asi, recall mide
   cuantas consultas fuera de alcance detecto y precision cuantas veces que se
   callo tenia razon. Es la convencion de AbstentionBench.
"""
import math
import re
import unicodedata

RE_ARTICULO = re.compile(r"Art\.?\s*(\d+)", re.IGNORECASE)

# Un termino de menos de 5 letras ("de", "la", "UNSAAC") aparece en casi
# cualquier titulo y volveria trivial la comparacion de documentos.
MIN_LONGITUD_TERMINO = 5
UMBRAL_COINCIDENCIA_DOCUMENTO = 0.5


def normalizar(texto: str) -> str:
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(texto).casefold())
    limpio = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", limpio)).strip()


def partir_cita(cita: str) -> tuple[str | None, str]:
    """Separa "Art. 14 num. 2 - Reglamento de Tutoria" en ("Art. 14", documento)."""
    m = RE_ARTICULO.search(cita)
    articulo = f"Art. {m.group(1)}" if m else None
    documento = cita.split("-", 1)[1].strip() if "-" in cita else cita.strip()
    return articulo, documento


def documento_coincide(esperado: str, recuperado: str | None) -> bool:
    """Compara por terminos significativos: las redacciones no son identicas."""
    if not recuperado:
        return False
    terminos = {t for t in normalizar(esperado).split() if len(t) >= MIN_LONGITUD_TERMINO}
    if not terminos:
        return False
    objetivo = normalizar(recuperado)
    hallados = sum(1 for t in terminos if t in objetivo)
    return hallados / len(terminos) >= UMBRAL_COINCIDENCIA_DOCUMENTO


def cita_cubierta(cita_esperada: str, articulo: str | None, documento: str | None) -> bool:
    """True si el fragmento satisface esa cita esperada.

    Cuando la cita nombra un articulo se exigen los dos: el articulo suelto no
    identifica nada, porque la numeracion se repite entre reglamentos.
    """
    art_esperado, doc_esperado = partir_cita(cita_esperada)
    if not documento_coincide(doc_esperado, documento):
        return False
    if art_esperado is None:
        return True
    return articulo == art_esperado


def relevancias(chunks, citas_esperadas: list[str]) -> list[bool]:
    """Relevancia binaria de cada fragmento, en el orden en que se recuperaron."""
    return [
        any(cita_cubierta(c, ch.articulo, ch.documento) for c in citas_esperadas)
        for ch in chunks
    ]


def citas_cubiertas(chunks, citas_esperadas: list[str], k: int) -> list[str]:
    """Citas esperadas que aparecen en el top-k."""
    top = chunks[:k]
    return [
        cita
        for cita in citas_esperadas
        if any(cita_cubierta(cita, ch.articulo, ch.documento) for ch in top)
    ]


def precision_at_k(rels: list[bool], k: int) -> float:
    if k <= 0:
        return 0.0
    return sum(1 for r in rels[:k] if r) / k


def techo_precision_at_k(total_relevantes: int, k: int) -> float:
    """Precision maxima alcanzable: no se llenan k huecos con menos relevantes.

    `total_relevantes` es la cantidad de *fragmentos* relevantes disponibles, no
    la de citas esperadas. Un articulo largo se parte en varios fragmentos y
    todos satisfacen la misma cita, asi que contar citas subestima el techo: fue
    lo que produjo una precision medida (0.417) por encima de su propio techo
    (0.182), que es imposible por construccion.
    """
    if k <= 0:
        return 0.0
    return min(total_relevantes, k) / k


def recall_at_k(chunks, citas_esperadas: list[str], k: int) -> float:
    """Proporcion de las citas esperadas que aparece en el top-k."""
    if not citas_esperadas:
        return 0.0
    return len(citas_cubiertas(chunks, citas_esperadas, k)) / len(citas_esperadas)


def f1(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def reciprocal_rank(rels: list[bool]) -> float:
    """1/posicion del primer acierto; 0 si no hay ninguno."""
    for i, r in enumerate(rels, start=1):
        if r:
            return 1 / i
    return 0.0


def posicion_primer_acierto(rels: list[bool]) -> int | None:
    for i, r in enumerate(rels, start=1):
        if r:
            return i
    return None


def dcg_at_k(rels: list[bool], k: int) -> float:
    return sum(1 / math.log2(i + 1) for i, r in enumerate(rels[:k], start=1) if r)


def ndcg_at_k(rels: list[bool], total_relevantes: int, k: int) -> float:
    """nDCG con ganancia binaria.

    El ideal coloca arriba todos los fragmentos relevantes disponibles. Usar la
    cantidad de citas esperadas en su lugar rompe la metrica: como una cita la
    cubren varios fragmentos, el DCG real superaba al ideal y nDCG daba 1.585,
    cuando por definicion no puede pasar de 1.
    """
    ideal = dcg_at_k([True] * min(total_relevantes, k), k)
    if ideal == 0:
        return 0.0
    return dcg_at_k(rels, k) / ideal


def confusion_abstencion(casos: list[dict]) -> dict:
    """Matriz de confusion de la decision de callarse.

    Positivo = el sistema se abstiene. Cada caso necesita `fuera_de_alcance`
    (la verdad) y `se_abstuvo` (lo que hizo el sistema).
    """
    tp = sum(1 for c in casos if c["fuera_de_alcance"] and c["se_abstuvo"])
    fn = sum(1 for c in casos if c["fuera_de_alcance"] and not c["se_abstuvo"])
    fp = sum(1 for c in casos if not c["fuera_de_alcance"] and c["se_abstuvo"])
    tn = sum(1 for c in casos if not c["fuera_de_alcance"] and not c["se_abstuvo"])

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    total = tp + fn + fp + tn

    return {
        "tp": tp,
        "fn": fn,
        "fp": fp,
        "tn": tn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1(precision, recall), 4),
        "accuracy": round((tp + tn) / total, 4) if total else 0.0,
        "n": total,
    }


def curva_recall_media(detalle: list[dict], k_max: int = 20) -> dict[str, float]:
    """Recall@k medio para cada k, sobre los casos en alcance del informe.

    Vive aca y no en el runner ni en el graficador porque los dos la necesitan,
    y dos implementaciones de la misma curva ya divergieron una vez: una excluia
    los casos que recuperaron menos de k fragmentos y la otra los arrastraba,
    con lo que el informe y el grafico mostraban numeros distintos para el mismo k.

    Un caso que devolvio menos de k fragmentos arrastra su ultimo valor: es lo
    que el sistema entregaria con ese limite, no un dato ausente.
    """
    en_alcance = [r for r in detalle if not r.get("fuera_de_alcance") and r.get("recall_por_k")]
    if not en_alcance:
        return {}

    curva: dict[str, float] = {}
    for k in range(1, k_max + 1):
        valores = []
        for r in en_alcance:
            disponibles = r["recall_por_k"]
            clave = str(k)
            if clave in disponibles:
                valores.append(disponibles[clave])
            else:
                ultima = max(disponibles, key=lambda x: int(x))
                valores.append(disponibles[ultima])
        curva[str(k)] = round(sum(valores) / len(valores), 4)
    return curva


def percentil(valores: list[float], p: float) -> float | None:
    """Percentil por interpolacion lineal. p en [0, 100]."""
    if not valores:
        return None
    ordenados = sorted(valores)
    if len(ordenados) == 1:
        return ordenados[0]
    pos = (len(ordenados) - 1) * p / 100
    bajo = math.floor(pos)
    alto = math.ceil(pos)
    if bajo == alto:
        return ordenados[int(pos)]
    return ordenados[bajo] + (ordenados[alto] - ordenados[bajo]) * (pos - bajo)


def media(valores: list[float]) -> float | None:
    return sum(valores) / len(valores) if valores else None
