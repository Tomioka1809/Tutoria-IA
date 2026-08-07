# Métricas de evaluación del RAG

> Complementa `07_rag_operacion.md`, que describe **cómo funciona** el pipeline.
> Este documento explica **cómo se mide** y por qué se eligió cada métrica.

---

## 1. Por qué tres capas y no un número

Un RAG puede fallar en dos sitios distintos que se arreglan de forma opuesta:
si el fragmento correcto nunca llegó al LLM, el problema es de **recuperación**
y se corrige en el corpus o en la búsqueda; si llegó y la respuesta lo ignoró,
el problema es de **generación** y se corrige en el prompt o en el modelo. Un
promedio único los confunde y no dice dónde intervenir.

Por eso la literatura separa las métricas en capas
([RAGAS](https://arxiv.org/abs/2309.15217),
[survey de evaluación de RAG](https://arxiv.org/html/2504.14891v1)). Aquí se
usan tres:

| Capa | Pregunta que responde | Estado |
|---|---|---|
| Recuperación | ¿Llegó el texto correcto al LLM, y arriba? | Medida por completo |
| Abstención | ¿Se calla cuando no puede sostener una respuesta? | Medida, muestra pequeña |
| Generación | ¿La respuesta se sostiene en lo recuperado? | Solo exactitud de citas |

Falta *faithfulness* con juez LLM. Está justificado en §7.

---

## 2. El error que hace inútil un promedio global

La evaluación v1 publicaba **precisión global 0.33**. Ese número mezclaba los
casos fuera de alcance, que puntúan 1.0 de forma trivial porque no hay nada que
recuperar. Sobre las consultas dentro de alcance la precisión real era 2 de 12.

De ahí dos reglas que este runner respeta:

1. **Los casos fuera de alcance nunca entran en un promedio de recuperación.**
   Se miden aparte, como decisión de abstención.
2. **Un caso sin cita de artículo no cuenta como fallo de artículo.** Preguntar
   por la misión de la carrera no tiene artículo que acertar; contarlo como 0
   castigaría al sistema por una pregunta que no es articulable.

---

## 3. Cómo se define "relevante" aquí

Un fragmento recuperado es **relevante** si satisface alguna de las citas que el
golden set espera. La comparación es estricta: **artículo y documento**.

```python
cita_cubierta("Art. 14 - Reglamento de Tutoría", articulo="Art. 14", documento="Estatuto")
# False: el número acierta pero la norma no
```

La medición anterior comparaba el número de artículo contra el conjunto de
artículos recuperados, sin mirar el documento. Como `Art. 14` existe en casi
todos los reglamentos, bastaba recuperar el Art. 14 de cualquier norma para dar
por acertada una cita del Reglamento de Tutoría.

> **Sobre el impacto real:** al endurecer el criterio, **ningún caso cambió de
> resultado** (`casos_perdidos_por_medicion_estricta: []`). El arreglo es
> defensivo, no una corrección de números publicados. El runner informa
> explícitamente cuáles casos perdería, para que un cambio futuro se note.

### El conjunto relevante se estima por pooling

Un artículo largo se parte en varios fragmentos y **todos** satisfacen la misma
cita. Por eso el total de relevantes se cuenta sobre los fragmentos recuperados
hasta `K_METRICAS = 20`, no sobre la cantidad de citas esperadas.

Contarlo mal produjo dos números imposibles antes de corregirlo:

| Síntoma | Causa |
|---|---|
| `nDCG@6 = 1.585` | El ideal se armaba con 1 relevante cuando había 3, así que el DCG real superaba al ideal |
| `Precision@6 = 0.417` con techo `0.182` | El techo suponía un fragmento por cita |

El pooling es una **cota inferior**: podría haber fragmentos relevantes por
debajo del rango 20 que no se cuentan.

---

## 4. Tabla de métricas

Valores de la corrida actual (golden set v2, 36 casos: 32 en alcance,
3 fuera de alcance, 1 pendiente de documento y excluido).

### 4.1 Recuperación

| Métrica | Qué mide | Valor | Lectura |
|---|---|---|---|
| **Acierto de documento** | El documento esperado está entre los recuperados | **32/32 (100%)** | Siempre entrega la fuente correcta |
| **Acierto de artículo** | El artículo exacto está entre los recuperados | **16/19 (84%)** | Los 3 fallos están en §6 |
| **Recall@6** | Proporción de citas esperadas presentes en lo entregado | **0.875** | Sube a 0.95 con k=12 |
| **MRR** | Posición del primer acierto (`1/rank`) | **0.815** | 24 de 29 casos aciertan en la posición 1 |
| **nDCG@6** | Calidad del orden completo, no solo del primero | **0.775** | |
| **Precision@6** | Proporción de lo entregado que es relevante | **0.417** | Su techo es **0.526**: leerla sola engaña |
| **F1@6** | Media armónica de precisión y recall | **0.510** | Arrastra el techo de la precisión |
| **Cobertura de palabras** | Términos clave presentes en lo recuperado | **0.938** | Aproximación de recall a nivel de contenido |

**Por qué Precision@k es baja y no es un problema.** Si un caso espera una cita
y se entregan 6 fragmentos, la precisión no puede pasar de 1/6 aunque la
recuperación sea perfecta. El runner reporta el techo `min(relevantes, k)/k`
junto al valor; **la precisión suelta no significa nada en este sistema**.

### 4.2 Abstención, como clasificador binario

Positivo = el sistema se calla ([convención de
AbstentionBench](https://arxiv.org/html/2506.09038v1)). Aquí sí aplican
accuracy, precisión, recall y F1 en su sentido clásico:

|  | Se abstuvo | Respondió |
|---|---|---|
| **Fuera de alcance** | TP = 3 | FN = 0 |
| **En alcance** | FP = 0 | TN = 32 |

precisión 1.000 · recall 1.000 · **F1 1.000** · accuracy 1.000

> ⚠️ **Son 3 casos fuera de alcance.** Un F1 perfecto sobre n=3 no es evidencia
> de nada. El runner imprime este aviso solo. Para que sea concluyente hacen
> falta 20-30 casos fuera de alcance, incluyendo los difíciles: otra
> universidad, premisa falsa, y preguntas cuyo documento no existe.

### 4.3 Generación

| Métrica | Qué mide | Estado |
|---|---|---|
| **Exactitud de citas** | Que los artículos nombrados en la respuesta estuvieran en el contexto entregado | Implementada; requiere `--con-generacion` |

Es determinista, sin juez LLM. El sistema responde citando articulado, y un
número de artículo inventado es la alucinación más costosa que puede cometer
porque **suena verificable**. No mide si la cita sostiene lo que se afirma: eso
es *faithfulness* y pide un juez (§7).

### 4.4 Operación

| Métrica | Valor (orden de magnitud) |
|---|---|
| Latencia de recuperación p50 | ~20 ms |
| Latencia de recuperación p95 | ~30 ms |
| Máximo observado | 50-65 ms |

Mide solo la recuperación híbrida contra PostgreSQL, sin el embedding de la
consulta ni la generación, que dominan el tiempo real que percibe el estudiante.

A diferencia del resto, **estos valores cambian entre corridas** porque dependen
de la carga de la máquina y del caché de PostgreSQL. Sirven para descartar que
la recuperación sea el cuello de botella, no como cifra a citar.

---

## 5. Gráficos

En `backend/tests/resultados/graficos/`, regenerables sin gastar cuota.

| Archivo | Qué muestra | Para qué sirve |
|---|---|---|
| `01_acierto_por_dominio.png` | Barras de acierto de documento y artículo en los 8 dominios | Localiza dónde falla: `movilidad` 2/4 y `enrutamiento` 1/2 |
| `02_confusion_abstencion.png` | Matriz 2×2 con F1, precisión y recall | Justifica los términos clásicos; incluye el aviso de muestra |
| `03_curva_recall_k.png` | Recall@k para k=1..20, con la línea de `limit=6` | **Decide el parámetro**: recall pasa de 0.875 a 0.953 con k=12 |
| `04_posicion_primer_acierto.png` | Histograma de la posición del primer relevante | El MRR en forma legible: 24 casos aciertan en la posición 1 |
| `05_resumen_metricas.png` | Barras horizontales de todas las métricas, con el techo de Precision@k marcado | Vista de conjunto para el informe |
| `06_calibracion_umbral.png` | Recall en alcance contra falsos positivos, por umbral | Muestra por qué 0.34 y no otro |
| `07_calibracion_peso_autoridad.png` | Acierto de artículo por peso, de 0.0 a 2.0 | Muestra que el valor es el mínimo que alcanza el óptimo |
| `08_latencia_recuperacion.png` | Histograma con p50 y p95 marcados | Viabilidad operativa |

Los gráficos 6 y 7 salen de `calibrar_umbral` y `calibrar_peso_autoridad`, no
del runner. **Hay que regenerarlos cuando cambia el golden set**, o mostrarán un
barrido hecho sobre otra muestra que el resto del informe.

---

## 6. Qué dicen los números de esta corrida

**Los 3 fallos de artículo** (documento correcto en los tres, así que el sistema
entrega la fuente y falla el artículo exacto):

| Caso | Qué pasa |
|---|---|
| 115 | *"¿cuántos créditos puedo matricular por movilidad?"* — la respuesta está en el Art. 8 del Reglamento Académico, pero los reglamentos de movilidad y subvenciones quedan más cerca de la pregunta y lo desplazan |
| 118 | *"¿hay apoyo económico para viajar a un congreso?"* — recupera el reglamento de subvenciones correcto, pero los Art. 11 y 27 en vez del Art. 6 |
| 122 | *"¿a qué oficina voy si tengo un problema económico?"* — responde desde documentos de índice en lugar del ROF o el Estatuto |

**El límite de 6 fragmentos deja recall sobre la mesa.** La curva `03` muestra
que subir a 12 llevaría el recall de 0.875 a 0.953. No se cambió porque el
parámetro afecta al costo por consulta y a la dilución del contexto, y eso pide
su propia medición del lado de la generación.

**El peso de autoridad admite bajarse.** Con el golden set ampliado a 32 casos
en alcance, el barrido da 16/19 desde **0.1**, no desde 0.2:

| Peso | Acierto de artículo |
|---|---|
| 0.0 | 14/19 |
| **0.1** | **16/19** |
| 0.2 (actual) … 2.0 | 16/19 |

Por la regla que el propio proyecto se fijó —*el menor valor que alcanza el
resultado*— correspondería 0.1. **No se cambió**: el barrido anterior, con 20
casos, daba 0.2, y dos muestras distintas dando dos mínimos distintos sugiere
que la frontera es inestable y no que 0.1 sea mejor. Cambiarlo pide más casos.

---

## 7. Lo que falta y por qué

1. **Faithfulness y answer relevancy con juez LLM.** Son las métricas centrales
   de RAGAS y aquí no están. Dos razones: piden ejecutar la generación de los 32
   casos más una llamada de juez por caso, y la cuota de Gemini ya se agota
   indexando el corpus; y un juez del mismo modelo que genera introduce sesgo a
   favor de sus propias respuestas. La exactitud de citas cubre el fallo más
   caro de este sistema sin ninguno de los dos costes.

2. **Muestra fuera de alcance.** 3 casos no sostienen un F1 de abstención.

3. **Sin variabilidad entre corridas.** Se reporta un único valor por métrica.
   La recuperación es determinista (el orden se desempata por id), así que
   repetir daría lo mismo; la generación no lo es, y cuando se midan métricas de
   generación harán falta varias corridas e intervalos.

4. **El conjunto relevante es una cota inferior** por el pooling a k=20.

5. **Sin comparación contra una alternativa.** Las métricas dicen cómo va este
   sistema, no si es mejor que solo búsqueda léxica o solo vectorial. Un
   *ablation* (sin RRF, sin autoridad, sin rama léxica) es la comparación
   natural y el barrido del peso de autoridad ya es un caso particular.

---

## 8. Cómo reproducir

```bash
# 1. Evaluacion (necesita la base y Gemini: correr dentro del contenedor)
docker compose exec backend python -m tests.run_eval_v2 \
    --json tests/resultados/fase5_eval_v2_corpus_completo.json

# Con generacion, para obtener ademas la exactitud de citas
docker compose exec backend python -m tests.run_eval_v2 --con-generacion \
    --json tests/resultados/fase5_eval_v2_corpus_completo.json

# 2. Barridos de calibracion (regenerar si cambio el golden set)
docker compose exec backend python -m scripts.calibrar_umbral --set v2 \
    --json tests/resultados/fase3_calibracion.json
docker compose exec backend python -m scripts.calibrar_peso_autoridad \
    --json tests/resultados/fase4_calibracion_peso.json

# 3. Graficos (leen los JSON: no tocan la base ni gastan cuota)
pip install -r backend/requirements-dev.txt
cd backend && python -m scripts.graficar_evaluacion
```

### Dónde vive cada cosa

| Archivo | Responsabilidad |
|---|---|
| `backend/scripts/metricas_rag.py` | Métricas puras: relevancia, P@k, R@k, F1, MRR, nDCG, matriz de abstención. Sin base de datos ni Gemini |
| `backend/tests/run_eval_v2.py` | Ejecuta el pipeline contra el golden set y escribe el informe JSON |
| `backend/scripts/graficar_evaluacion.py` | Dibuja desde los JSON ya generados |
| `backend/tests/unit/test_metricas_rag.py` | 31 pruebas de las métricas, varias de regresión |
| `backend/tests/unit/test_graficar_evaluacion.py` | 15 pruebas de la preparación de datos y humo de los PNG |

La curva de recall vive **solo** en `metricas_rag.curva_recall_media`: cuando el
runner y el graficador la calculaban por separado, uno excluía los casos con
menos de k fragmentos y el otro arrastraba su último valor, y el informe y el
gráfico mostraban números distintos para el mismo k.

---

## 9. Glosario de fórmulas

Con relevancia binaria `rel_i ∈ {0,1}` en la posición `i`:

| Métrica | Fórmula |
|---|---|
| Precision@k | `(Σ rel_i para i≤k) / k` |
| Techo de Precision@k | `min(relevantes disponibles, k) / k` |
| Recall@k | `citas esperadas cubiertas en el top-k / total de citas esperadas` |
| F1@k | `2·P·R / (P+R)` |
| RR | `1 / posición del primer relevante`, 0 si no hay ninguno |
| MRR | media de RR sobre las consultas |
| DCG@k | `Σ rel_i / log₂(i+1)` |
| nDCG@k | `DCG@k / DCG@k del orden ideal` |
| Precisión de abstención | `TP / (TP+FP)` |
| Recall de abstención | `TP / (TP+FN)` |

---

## 10. Fuentes

- [RAGAS: Automated Evaluation of Retrieval Augmented Generation](https://arxiv.org/abs/2309.15217) (EACL 2024) — faithfulness, answer relevance, context relevance
- [Retrieval Augmented Generation Evaluation in the Era of Large Language Models: A Comprehensive Survey](https://arxiv.org/html/2504.14891v1) (2025) — taxonomía de métricas de recuperación, generación, seguridad y eficiencia
- [AbstentionBench: Reasoning LLMs Fail on Unanswerable Questions](https://arxiv.org/html/2506.09038v1) — abstention precision, recall y F1
- [Métricas de Ragas](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/)
- [How to Evaluate Retrieval Quality in RAG Pipelines: Precision@k, Recall@k y F1@k](https://towardsdatascience.com/how-to-evaluate-retrieval-quality-in-rag-pipelines-precisionk-recallk-and-f1k/)
- [DCG@k y NDCG@k](https://towardsdatascience.com/how-to-evaluate-retrieval-quality-in-rag-pipelines-part-3-dcgk-and-ndcgk/)
