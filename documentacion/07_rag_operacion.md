# Pipeline RAG — Operación, parámetros y verificación

> Reemplaza el diseño descrito en `03_pipeline_rag.md`, que documenta la versión
> anterior (chunking por estructura JSON, recuperación con heurísticas léxicas).

---

## 1. Cómo se inicia

El índice vive en la tabla `corpus_chunks` de PostgreSQL con la extensión
`pgvector`. Se construye desde `backend/corpus_estructurado/`, no desde los PDF
directamente.

### Arranque automático (Docker)

`backend/docker-entrypoint.sh` corre antes de uvicorn:

```sh
alembic upgrade head          # esquema
python -m app.bootstrap_data  # admin, roster e índice del RAG
exec uvicorn ...
```

`bootstrap_data.ensure_corpus()` llama a la ingesta incremental. Es seguro
ejecutarla en cada arranque: compara hashes y solo embebe lo que falta. Si la
cuota de Gemini se agota a mitad de camino, la interrupción se captura, lo
indexado queda intacto y el contenedor arranca igual.

Variables de entorno:

| Variable | Efecto |
|---|---|
| `GEMINI_API_KEY` | Sin ella no hay ingesta ni chat |
| `AUTO_BOOTSTRAP=0` | Desactiva toda la siembra (las migraciones igual corren) |
| `AUTO_SEED_CORPUS=0` | Aplica migraciones y usuarios, pero no toca el índice |

### Construcción manual

```bash
# 0. Solo para los PDF escaneados: OCR en espanol antes de extraer
uvx --from docling docling convert <pdf> --to md --output <pdf-dir>/es_ocr \
    --ocr-lang es --ocr-mode full_page --device cpu

# 1. Extraer el articulado desde los PDF oficiales
python -m scripts.extract_pdf_corpus --pdf-dir /ruta/a/los/pdf
python -m scripts.extract_plan_estudios --md .../plan-estudios-2025.md
python -m scripts.extract_calendario  --md .../es_ocr/CRONOGRAMA-2026.md

# 1b. Fuentes que ya viven versionadas en backend/corpus_fuentes/ (no piden ruta)
python -m scripts.extract_malla --json corpus_fuentes/malla_2017_transcrita.json --plan 2017
python -m scripts.extract_catalogo_2017    # plan_estudios_2017 (catálogo del Centro de Cómputo)
python -m scripts.extract_escuela          # escuela_informatica (portal de la escuela)
python -m scripts.extract_becas_comedor    # becas_y_comedor (índice de apoyos)
python -m scripts.convert_corpus           # corpus heredado (respeta lo ya extraído de PDF)

# 2. Validar antes de indexar
python -m scripts.validate_corpus --estricto

# 3. Indexar (incremental: solo embebe lo nuevo o lo editado)
python -m scripts.ingest_corpus
python -m scripts.ingest_corpus --forzar   # reembebe todo
```

**Cambiar la API key es inocuo.** Los vectores viven en la base y no llevan
marca de la cuenta: se cambia `GEMINI_API_KEY`, se recrea el contenedor con
`docker compose up -d backend` (un `restart` no recarga variables de entorno) y
la ingesta retoma donde quedó.

**Cambiar el modelo de embeddings no lo es.** Dos modelos producen espacios
vectoriales distintos, así que una distancia entre un fragmento viejo y una
consulta nueva deja de significar algo y la búsqueda empeora sin que nada falle.
Cada chunk registra `modelo_embedding` y la ingesta se niega a continuar ante
una mezcla, indicando cómo reindexar.

---

## 2. Cómo funciona

### 2.1 Corpus

Un documento declara su procedencia y se descompone en **fragmentos**, que son
la unidad de recuperación. El esquema está en
`app/application/dtos/corpus_dtos.py`.

```json
{
  "procedencia": {
    "documento": "Reglamento de Tutoría Académica UNSAAC",
    "tipo": "reglamento",
    "resolucion": "Resolución Nro. CU-0220-2017-UNSAAC de 24.05.2017"
  },
  "fragmentos": [
    {
      "id": "reglamento_tutoria#art-14-1",
      "articulo": "Art. 14",
      "titulo": "Art. 14 - Asignación de Tutores",
      "seccion": ["Capítulo III", "asignacion-de-tutores"],
      "texto": "Reglamento de Tutoría... > Art. 14 - Asignación de Tutores\nEl número de tutorados..."
    }
  ]
}
```

Cada fragmento antepone su ruta jerárquica al texto para ser **autocontenido**:
aislado, `"veinticinco (25) estudiantes"` no se puede recuperar ni citar.

Estado actual: **1369 fragmentos, 20 documentos, 732 artículos**.

#### Fuentes versionadas (`backend/corpus_fuentes/`)

Los PDF no viven en el repositorio, pero sí las transcripciones de las fuentes
que no son PDF: la imagen de la malla 2017, el catálogo de asignaturas del
Centro de Cómputo y las páginas del portal de la escuela. Están en un formato
crudo y auditable, y su extractor las redacta en prosa.

Esto cierra un agujero real: `malla_2017.json` **no se podía regenerar** porque
su transcripción vivía fuera del repositorio, así que cualquier corrección
obligaba a editar a mano el archivo indexado.

| Fuente | Extractor | Documento que produce |
|---|---|---|
| `malla_2017_transcrita.json` | `extract_malla` | `malla_2017` |
| `catalogo_2017.json` | `extract_catalogo_2017` | `plan_estudios_2017` |
| `escuela_informatica.json` | `extract_escuela` | `escuela_informatica` |
| `becas_y_comedor.json` | `extract_becas_comedor` | `becas_y_comedor` |

Cada extractor **verifica antes de escribir**: `extract_malla` y
`extract_catalogo_2017` comprueban la transcripción contra los totales que la
propia fuente declara (219 créditos, 62 asignaturas, créditos por categoría) y
se niegan a emitir si no cuadra. Un crédito mal leído es peor que no tener el
dato: el sistema lo afirmaría con confianza.

#### Redacción y forma de la consulta

Un fragmento no solo tiene que **contener** la respuesta: tiene que parecerse a
la pregunta. Dos casos medidos, ambos resueltos en el texto y no aflojando el
umbral calibrado:

- El portal dice *"Escuela Profesional"* y el estudiante dice *"la carrera"*.
  *"¿Cuál es la visión de la carrera?"* quedaba a distancia **0.364** —fuera del
  corte de 0.34— y sin coincidencia léxica, porque la palabra "carrera" no
  aparecía en el texto.
- El chat reescribe las consultas de malla anteponiéndoles `malla curricular
  Plan <año>` (ver `reconstruct_query`). Solo las FAQ del plan 2025 estaban
  redactadas con esa forma, así que *"qué cursos llevo en el sexto ciclo de la
  malla 2017"* devolvía **seis fragmentos del 2025 y ninguno del 2017**. El año
  por sí solo no inclina el embedding.

### 2.1.1 Fuentes escaneadas

Tres documentos no tienen capa de texto y se extraen desde el Markdown de un OCR
en español (`docling`, ver §1). El parser de articulado es el mismo: lo que cambia
es de dónde sale el texto, no cómo se parte.

El Markdown del OCR trae tres estorbos que el extractor normaliza: las imágenes
van embebidas en base64 (2.44 MB de los 2.5 MB del reglamento de movilidad), el
encabezado de cada página sale como fila de tabla repetida, y los títulos llevan
`#`, que impedía reconocer `## Artículo 1°`.

### 2.2 Indexación

Cada fragmento se embebe con `task_type=RETRIEVAL_DOCUMENT` y se guarda con:

| Columna | Uso |
|---|---|
| `fragment_id` | Identidad estable → ingesta incremental |
| `content_hash` | Si no cambió, el embedding sigue valiendo |
| `documento`, `articulo` | Procedencia citable en la respuesta |
| `autoridad` | Jerarquía de fuente (ver 2.4) |
| `modelo_embedding` | Detección de mezcla de modelos |
| `busqueda_ts` | Columna generada, FTS en español con índice GIN |

### 2.3 Recuperación híbrida

Dos ramas independientes sobre el mismo pool:

- **Vectorial** — `cosine_distance` con índice HNSW. Captura similitud
  semántica aunque no compartan palabras.
- **Léxica** — `plainto_tsquery('spanish', ...)` con índice GIN. Captura
  códigos, números y nombres propios que el embedding diluye, y **lematiza**:
  `matricularse` encuentra `Matrícula`.

Se fusionan con **Reciprocal Rank Fusion**: cada rama aporta `1/(k + posición)`.
Al operar sobre posiciones y no sobre puntajes, no hace falta normalizar una
distancia coseno contra un `ts_rank`, que viven en escalas sin techo común.

La consulta se embebe con `task_type=RETRIEVAL_QUERY`. La búsqueda es
asimétrica: usar el mismo modo para pregunta y documento trata a una consulta
corta y un texto largo como si fueran comparables entre sí.

### 2.4 Reordenamiento por autoridad

La similitud semántica no distingue una norma citable de un resumen no
verificado que dice algo parecido. Medido: ante *"¿qué oficina se encarga del
bienestar?"*, el Art. 245 del Estatuto quedaba en la **posición 15 de 20**,
detrás de cinco fragmentos de paráfrasis, y con `limit=6` nunca llegaba al LLM.

| Nivel | Criterio |
|---|---|
| 3 | Citable por artículo |
| 2 | Documento con resolución declarada |
| 1 | Resto (glosario, FAQ, paráfrasis) |

El factor es multiplicativo sobre el puntaje RRF: reordena entre candidatos
comparables pero no rescata a uno claramente peor. Con el reordenamiento
activo, el Art. 245 pasa a la posición **4**.

### 2.5 Abstención

Dos cortes **en código**, antes de invocar al LLM, para no depender de que el
prompt lo convenza de callarse:

1. **Sin evidencia** — si ninguna rama devuelve fragmentos, se responde el
   mensaje de abstención sin llamar a Gemini.
2. **Institución externa** — si la consulta apunta a otra casa de estudios se
   corta antes de recuperar. Esto no lo resuelve el umbral: *"cuánto cuesta la
   matrícula en la UNSA"* queda a distancia 0.291, más cerca del corpus que
   varias preguntas legítimas, porque semánticamente **sí** es una consulta
   sobre matrícula universitaria. Lo que difiere es la institución.

   Se responde con una **aclaración**, no con una negativa, para que un falso
   positivo cueste un turno y no una consulta válida. Se excluyen los términos
   de vínculo (convenio, intercambio, movilidad, traslado, beca), porque
   movilidad es uno de los dominios del alcance.

---

## 3. Parámetros

Todos en `RAGRetrievalPolicy` (`app/application/dtos/rag_dtos.py`), inyectados
desde `app/infrastructure/api/dependencies.py`.

| Parámetro | Valor | Origen del valor |
|---|---|---|
| `limit` | 6 | Fragmentos entregados al LLM |
| `max_cosine_distance` | **0.34** | **Calibrado** — ver abajo |
| `candidatos_por_rama` | 20 | Candidatos por rama antes de fusionar |
| `rrf_k` | 60 | Constante habitual de RRF |
| `min_ts_rank` | 0.05 | Piso léxico; sin él, *"derivada de una función"* engancha el curso *Cálculo I* |
| `peso_autoridad` | **0.2** | **Calibrado** — ver abajo |
| `keyword_fallback_limit` | 2 | >0 habilita la rama léxica |
| `HISTORY_WINDOW_MESSAGES` | 20 | Tope de historial enviado al LLM |

Modelos: `gemini-embedding-2` a 768 dimensiones (embeddings),
`gemini-3.5-flash-lite` (generación).

### Calibración

Los dos parámetros marcados **no se eligieron a ojo**. Hay un script por cada
uno y sus informes quedan en `backend/tests/resultados/`.

```bash
python -m scripts.calibrar_umbral --set v2
python -m scripts.calibrar_peso_autoridad
```

**Umbral de distancia.** El valor anterior, 0.45, dejaba pasar **las tres**
consultas fuera de alcance y rompía la abstención.

| Umbral | Recall en alcance | Falsos positivos |
|---|---|---|
| 0.29 | 70% | 0 |
| **0.34** | **100%** | 1 |
| 0.45 (anterior) | 100% | 3 |

El único falso positivo a 0.34 es la consulta sobre otra universidad, que
resuelve la guarda institucional y no el umbral.

**Peso de autoridad.** El barrido embebe cada pregunta una sola vez y reutiliza
los vectores para los 11 pesos, así que cuesta lo mismo que una evaluación.

| Peso | Acierto de artículo | Acierto de documento |
|---|---|---|
| 0.0 | 12/16 | 20/20 |
| **0.2** | **15/16** | 20/20 |
| 0.5 → 2.0 | 15/16 | 20/20 |

Se toma 0.2 por ser el menor valor que alcanza el resultado: la menor
intervención sobre el orden que produce la fusión.

---

## 4. Pruebas que pasa

### 4.1 Suite automatizada

**445 pruebas.** Ejecutar desde la raíz del repositorio:

```bash
backend/venv/bin/python -m pytest -q
```

Archivos que cubren el RAG:

| Archivo | Qué protege |
|---|---|
| `test_corpus_schema.py` | Contrato del esquema; solo los reglamentos exigen articulado |
| `test_corpus_ingestion.py` | Conversión, descomposición de dicts grandes, auditoría de cobertura |
| `test_ingest_corpus.py` | Hash, clasificación incremental, orden intercalado, `task_type`, modo estricto, guarda de modelo |
| `test_pdf_extraction.py` | Parseo de articulado, jerarquía, corte de artículos largos |
| `test_plan_estudios.py`, `test_extract_malla.py`, `test_calendario.py` | Extractores tabulares y de OCR |
| `test_catalogo_2017.py` | Catálogo del plan 2017: verificación de totales, asignaturas de especialidad nombradas, discrepancias de código |
| `test_escuela_informatica.py` | Identidad de la carrera: misión, visión, autoridades, aniversario, círculos y eventos |
| `test_becas_comedor.py` | Que toda beca declare su fundamento y que las del Estado no se atribuyan a la UNSAAC |
| `test_validate_malla.py` | Verificación de transcripciones contra invariantes |
| `test_golden_set_v2.py` | Integridad del golden set; artículos inexistentes |
| `test_rag_quality.py` | RRF, índice de texto completo, ponderación por autoridad |
| `test_institucion_externa.py` | Guarda institucional y sus excepciones |
| `test_chat_abstention.py` | Corte por falta de evidencia |
| `test_evaluation_integrity.py` | Hashes del golden set v1 congelado |

Varias pruebas son **regresiones de defectos reales encontrados durante el
trabajo**, no casos hipotéticos: el chunk de 3729 caracteres que diluía nueve
temas, el orden alfabético que dejó un reglamento entero sin indexar, la
palabra clave dispersa que inflaba la cobertura, el `convert_corpus` que pisaba
el articulado.

### 4.2 Evaluación del RAG

> El detalle de **qué mide cada métrica, por qué se eligió y cómo leer los
> gráficos** está en [`08_metricas_evaluacion.md`](08_metricas_evaluacion.md).
> Aquí solo van los números de titular.

```bash
python -m tests.run_eval_v2 --json tests/resultados/fase5_eval_v2_corpus_completo.json
```

Contra `golden_set_v2.json` (36 casos, 9 dominios), corpus completo:

```
Acierto de artículo   : 16/19  ( 84%)     MRR          : 0.815
Acierto de documento  : 32/32  (100%)     nDCG@6       : 0.775
Cobertura de palabras :          94%      Recall@6     : 0.875
Abstención correcta   :  3/3   (100%)     Precision@6  : 0.417 (techo 0.526)
```

El runner recupera hasta k=20 para calcular las curvas @k de una sola pasada, y
recorta a `limit` para las métricas de titular: el top-6 de una consulta con
limit=20 es idéntico al de una con limit=6, porque la búsqueda arma la lista
completa ordenada y recorta al final.

> Medido sobre el corpus completo (20 documentos). El golden set creció de 26 a
> 36 casos: se agregó el dominio `escuela` y los casos de becas y plan 2017. El
> detalle de los tres que fallan está en §5.

| Dominio | artículo | documento |
|---|---|---|
| tutoria | 5/5 | 5/5 |
| apoyos | 4/4 | 6/6 |
| escuela | — | 6/6 |
| movilidad | 2/4 | 4/4 |
| trayectoria_academica | 4/4 | 6/6 |
| calendario, tramites | — | 3/3 |
| enrutamiento | 1/2 | 2/2 |

El acierto de artículo **era imposible de medir antes**: el golden set siempre
citó `"Art. 15 - Reglamento de Tutoría"`, pero el corpus era una paráfrasis sin
articulado y ninguna respuesta podía satisfacerlo.

El runner reproduce el pipeline completo, incluida la guarda institucional, y
**avisa si hay documentos sin indexar** para que las métricas no se lean fuera
de contexto.

### 4.3 Auditoría de cobertura

Responde si el texto necesario **existe** en el corpus, sin llamar a Gemini.
Define el techo alcanzable: ninguna mejora de recuperación puede superarlo.

```bash
python -m scripts.audit_corpus_coverage --set v2 --corpus corpus_estructurado
```

Mide co-ocurrencia dentro de una misma unidad, no presencia suelta: las
palabras de una consulta pueden aparecer en secciones sin relación entre sí y
dar un falso positivo.

### 4.4 Verificación extremo a extremo

```bash
TOK=$(curl -s -X POST localhost:8000/api/v1/auth/login \
  -d "username=<código>@unsaac.edu.pe&password=<código>" | jq -r .access_token)

curl -s -X POST localhost:8000/api/v1/chat/message \
  -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" \
  -d '{"content":"¿Cuántos estudiantes como máximo puede tener un tutor?"}'
```

Respuesta verificada:

> Según el Reglamento de Tutoría Académica de la UNSAAC, el número de tutorados
> por cada profesor, en la medida de lo posible, no debe superar los
> **veinticinco (25) estudiantes**. Si en algún centro no fuese posible alcanzar
> esta cifra, el límite puede aumentarse o se puede recurrir a docentes becarios
> bajo la supervisión de un profesor ordinario.

Y fuera de alcance:

> No cuento con información suficiente en la base oficial de la UNSAAC para
> responder con certeza.

---

## 5. Limitaciones conocidas

1. **Un caso del golden set espera un documento** que no está publicado: los
   requisitos para postular a la beca de comedor, que estarían en el Reglamento
   de Subsidios y Becas. Está marcado `pendiente_documento` y se excluye de las
   métricas, porque contarlo como fallo confundiría una brecha documental con un
   problema de búsqueda. No figura en el portal de transparencia ni en el índice
   de normas de gob.pe; el camino es pedirlo por acceso a la información pública.

   Los criterios de **prioridad** sí son citables (Estatuto Art. 252: situación
   socioeconómica baja o condición de invicto); lo que falta es el procedimiento
   formal de postulación.

   Los otros tres que estaban en esta lista se cerraron: las bases de movilidad
   OCRI las reemplaza el **Reglamento del Programa de Movilidad Académica**
   (CU-349-2026, Art. 1-25), la directiva de subvenciones el **Reglamento para
   el Otorgamiento de Subvenciones Económicas** (CU-667-2025, Art. 1-27), y el
   procedimiento de reserva de cupo del comedor, el **Manual de Usuario de
   Bienestar Universitario** (30.09.2024), incorporado en `becas_y_comedor`.

2. **`servicios_bienestar` no tiene fuente verificable, y se redujo a 5
   fragmentos.** El reordenamiento por autoridad no bastó para contenerlo: ante
   *"¿qué servicios de apoyo ofrece la universidad?"* ocupaba **cuatro de los
   seis** slots y dejaba fuera el artículo del Estatuto que responde. Se
   retiraron los ocho fragmentos que ya son citables en otro documento —las
   cinco unidades de bienestar (ROF Art. 106-115), la finalidad (Estatuto
   Art. 245-246), los beneficiarios (Art. 247) y las FAQ de beca y comedor—. Se
   conserva lo que no está en la norma: examen médico del ingresante, uso del
   estadio y orientación ante el estrés.

   La lista vive en `FRAGMENTOS_SUPERADOS` (`scripts/convert_corpus.py`), con la
   norma que reemplaza a cada uno.

   `reglamento_intercambio_estudiantil` y `malla_curricular_2017` se retiraron y
   ahora figuran en `DOCUMENTOS_RETIRADOS`. Antes, volver a correr
   `convert_corpus` los resucitaba y deshacía la decisión en silencio.

3. **`servicios_biblioteca` no tiene articulado.** El PDF está escaneado y el
   OCR corrompe la numeración (`Art 19` por `Art. 1°`, el `°` leído como `9`).
   Citar mal un artículo es peor que no citarlo. Además el documento cita la Ley
   23733, derogada por la Ley 30220 en 2014.

4. **Tres casos aciertan el documento y fallan el artículo.** El acierto de
   documento es 32/32, así que en los tres el sistema entrega la fuente correcta.

   | Caso | Qué pasa |
   |---|---|
   | 122 | *"¿a qué oficina voy si tengo un problema económico?"* responde desde `preguntas_frecuentes` en lugar del ROF o el Estatuto |
   | 115 | *"¿cuántos créditos puedo matricular por movilidad?"* — **regresión del cierre del corpus**. La respuesta está en el Art. 8 del Reglamento Académico, pero los reglamentos de movilidad y subvenciones, recién incorporados, quedan más cerca de la pregunta y lo desplazan |
   | 118 | *"¿hay apoyo económico para viajar a un congreso?"* recupera el reglamento de subvenciones correcto, pero los Art. 11 y 27 en vez del Art. 6, que es el que enumera las actividades subvencionables |

   El barrido de `calibrar_peso_autoridad` descarta que el peso sea la palanca:
   da 14/18 en los once valores probados, de 0.1 a 2.0. Los tres se resuelven
   con recuperación, no con jerarquía de fuente.

5. **El calendario caduca.** El esquema no tiene ventana de vigencia, así que un
   calendario vencido seguiría respondiéndose como actual. Aplica igual a las
   convocatorias, si se incorporan.

   Lo mismo vale para lo que se incorporó de la escuela: las **autoridades**
   cambian de gestión, los **eventos** cambian de fecha en cada edición y la
   **acreditación ICACIT** figura vigente hasta el 31.12.2025 con la escuela en
   proceso de acreditación continua. Los fragmentos afectados dicen en su propio
   texto que el dato corresponde a la última edición publicada, pero eso avisa,
   no caduca.

6. **El aniversario de la carrera no consta en resolución.** La celebración es en
   diciembre y las ediciones documentadas (XXV en 2018, XXVII el 11.12.2020)
   cuentan desde la reapertura de 1993, mientras que la fecha de creación que
   declara el portal es el 13.12.1971. El fragmento entrega las dos fechas y
   declara la contradicción en vez de resolverla a ojo.

7. **La imagen de la malla 2017 contradice al catálogo de matrícula** en cinco
   códigos (`ME351/IF351`, `FI370/IF370`, `EL371/LI371`, `ME356/ME359`,
   `DE901/DR901`). Vale el del catálogo, que es el registro contra el que se
   matricula. Los fragmentos de `malla_2017` entregan ambos y dicen cuál sirve
   para matricularse; `plan_estudios_2017` tiene además un fragmento dedicado a
   la discrepancia. No se ubicó una resolución que apruebe el plan 2017, así que
   `procedencia.resolucion` queda nula en los dos documentos.
