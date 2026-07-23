# Reporte Final y Correcciones Consolidadas — Proyecto TutorIA (Fase 6)

> **Estado: REPORTE FINAL VERIFICADO**
> La Fase 5 (Benchmark RAG y análisis cuantitativo) y la Fase 6 (Integración final, migración Pydantic V2, seguridad por entorno y verificación documental) han sido completadas con éxito. Este documento constituye el informe consolidado definitivo del proyecto.

Este documento representa el informe final verificado del proceso de auditoría, documentación, refactorización, endurecimiento de seguridad y evaluación experimental del sistema **TutorIA**, desarrollado para la gestión de tutorías académicas y asistencia conversacional RAG en el curso de Inteligencia Artificial (IF651, UNSAAC).

---

## 1. Resumen Ejecutivo del Proyecto

- **Estado General:** El sistema cuenta con una arquitectura Hexagonal sólida en el Backend (FastAPI, PostgreSQL `pgvector`) y una aplicación móvil Expo SDK 54 en el Frontend.
- **RAG & LLM:** Integración oficial con Google Gemini (modelo generativo activo `gemini-3.5-flash-lite`, modelo de embedding activo `gemini-embedding-2` de 768 dimensiones) combinando recuperación vectorial semántica con ejecución de herramientas en tiempo real (*Tool Calling*). Modo estricto sin fallbacks silenciosos activado en la suite de evaluación.
- **Evaluación Experimental (Paper IEEE):** Benchmark RAG oficial de 15 casos completado sin errores de infraestructura (`fase5c_official15_flashlite_20260723T033328Z`). Fase 5A completada (Integridad y robustez del evaluador); Fase 5B completada (Ejecución parcial controlada); Fase 5C completada (Ejecución oficial de 15 casos completada sin errores de infraestructura ni de red; con 13 casos clasificados como `model_failure` por criterios cuantitativos de calidad funcional); y Fase 5D completada (Análisis cuantitativo y cierre formal). **Fase 5 CERRADA**.
- **Fase 6 Completada:** Auditoría integral (Fase 6A), migración a Pydantic V2 y validación de seguridad por entorno `APP_ENV` (Fase 6B), y cierre documental definitivo con sincronización de verificadores (Fase 6C). **Cierre técnico del proyecto COMPLETADO**.

---

## 2. Arquitectura del Backend

- **Patrón:** Arquitectura Hexagonal (Puertos y Adaptadores).
- **Dominio:** Entidades puras, excepciones de dominio y DTOs centralizados en `app/domain/schemas/`.
- **Aplicación:** Casos de uso (`AuthUseCases`, `ChatUseCase`, `SessionUseCases`, `QuizUseCases`) desacoplados de FastAPI y SQLAlchemy.
- **Infraestructura:** Adaptadores Gemini API (`GeminiAdapter`), repositorios PostgreSQL con `pgvector` y middleware de seguridad JWT.

---

## 3. Frontend Expo / React Native

- **Framework:** Expo SDK 54 con React Native 0.81 y React 19.
- **Estilos y Estado:** NativeWind (Tailwind CSS) y Zustand para la gestión del estado global.
- **API & Errores:** Cliente Axios con resolución dinámica de URL (`resolveApiUrl()`), inyección automática de cabecera `Authorization: Bearer <token>`, normalización de errores (`api-error.ts`), filtrado de trazas sensibles y soporte i18n.
- **Calidad Estática:** 5 verificadores frontend ejecutados con exit code 0 (`verify:quality`, `lint`, `type-check`, etc.), sin advertencias ESLint.

---

## 4. Pipeline RAG

- **Búsqueda Vectorial:** `CorpusRepository` utiliza distancia coseno (`<=>`) sobre fragmentos indexados del reglamento universitario.
- **Umbral de Similitud:** Implementado `max_cosine_distance=0.45` en la política de recuperación (`RAGRetrievalPolicy`) para descartar contextos irrelevantes y activar abstención léxica.
- **Orquestación:** Búsqueda híbrida y *Tool Calling* integrados de forma determinista.

---

## 5. Modelos Activos

- **Modelo Generativo Activo:** `gemini-3.5-flash-lite` para respuestas conversacionales, generación de quizes, evaluación y Tool Calling.
- **Modelo de Embedding Activo:** `gemini-embedding-2` con vectores de 768 dimensiones.
- **Modelo Anterior Reemplazado:** `gemini-2.5-flash` retirado de las referencias activas.

---

## 6. Benchmark Oficial de 15 Casos

- **Identificador Oficial de Corrida:** `fase5c_official15_flashlite_20260723T033328Z`.
- **Estratificación:** 15 casos deterministas seleccionados del Golden Set (`facil`: 7, `ambiguo`: 5, `fuera_de_alcance`: 3).
- **Mecanismos de Control:** Rate-limiter de 15 segundos entre solicitudes LLM, escritura atómica de artefactos JSON/CSV y aislamiento transaccional por usuario temporal.

---

## 7. Resultados Cuantitativos Oficiales

### Métricas Globales del Benchmark (15 casos)
- **Precisión Global:** `0.3333` (33.33%)
- **Cobertura Global:** `0.3333` (33.33%)
- **Pertinencia Global:** `0.3111` (31.11%)

### Métricas por Categoría
- **Fácil (7 casos):** Precisión `0.2857`, Cobertura `0.2857`, Pertinencia `0.3667` (1 `success`, 6 `model_failure`).
- **Ambiguo (5 casos):** Precisión `0.0000`, Cobertura `0.0000`, Pertinencia `0.3000` (0 `success`, 5 `model_failure`).
- **Fuera de Alcance (3 casos):** Precisión `1.0000`*, Cobertura `1.0000`*, Pertinencia `0.2000` (3 `model_failure`).
  - *\*Nota: Las métricas de 1.0 en fuera de alcance constituyen una convención formal del marco evaluador.*

### Indicadores de Ejecución Oficial
- `total_cases`: 15
- `selected_cases`: 15
- `completed_cases`: 15
- `infrastructure_errors`: 0
- `skipped_cases`: 0
- `is_complete`: true
- `success`: 2
- `model_failure`: 13

---

## 8. Correcciones y Endurecimiento de la Fase 6B y Fase 6C

- **Migración a Pydantic V2 (Fase 6B-1):** 15 clases migradas en 12 archivos desde `class Config:` (`from_attributes = True`) hacia `model_config = ConfigDict(from_attributes=True)`, eliminando todas las advertencias internas de Pydantic V2.
- **Seguridad por Entorno (Fase 6B-2):**
  - Introducción explícita de `APP_ENV` (`development`, `test`, `production`).
  - Bloqueo en `production` de claves `SECRET_KEY` débiles, cortas (< 32 caracteres), predeterminadas o placeholders documentales.
  - Bloqueo en `production` de contraseñas por defecto o inseguras para `DB_PASSWORD`.
  - Preservación de fallbacks convenientes en entornos `development` y `test` para no romper el desarrollo local ni las pruebas automatizadas.
  - Integración transparente en el ciclo de vida `lifespan` de FastAPI en `main.py`.
  - La Fase 6B cerró con **162 pruebas aprobadas** tras incorporar 18 pruebas unitarias de seguridad.
- **Cierre Documental (Fase 6C):**
  - Sincronización de verificadores y adición de 2 pruebas unitarias de verificación documental, alcanzando el resultado final probado de **164 pruebas aprobadas**.

---

## 9. Validaciones Finales del Proyecto

- **Pruebas Unitarias Backend:** **164 pruebas aprobadas, 0 fallidas**.
- **Warnings:** **1 warning externo de `google-genai`**; cero warnings en el código fuente del proyecto.
- **Integridad RAG:** **24 PASS y 0 FAIL** en `verify_evaluation_integrity.py`.
- **Verificador de Fase 5:** **PASS=4, WARN=0, FAIL=0, SKIP=1** (`verificar_tutoria.py --fase 5`).
- **Frontend Quality:** 5 script verificadores del frontend aprobados con exit code 0.
- **Compilación:** `compileall` aprobado sin errores en backend y verificadores.
- **Hashes Protegidos:** Verificados intactos para todos los archivos JSON y CSV oficiales e históricos.
- **Seguridad:** Cero secretos reales expuestos en el código o control de versiones.

Al cierre de la Fase 6B, la suite alcanzó 162 pruebas aprobadas. Durante la Fase 6C se añadieron 2 pruebas documentales para validar el estado final del reporte y el rechazo del estado provisional, elevando el resultado final a 164 pruebas aprobadas.

---

## 10. Limitaciones y Recomendaciones Posteriores

### Incidencias Registradas para Fases Futuras
- **`F5D-001` (Recuperación Vectorial):** Identificada baja tasa de recuperación semántica en consultas de reglamento como recomendación técnica posterior.
- **`F5D-002` (Abstención Fuera de Dominio):** Registrada recomendación posterior para reforzar el prompt de abstención en consultas no académicas.
- **`F5D-003` (Heurísticas del Evaluador):** Registrada recomendación posterior para desacoplar las métricas de recuperación y generación en el evaluador.

### Observaciones Informativas
- **`MODULE_TYPELESS_PACKAGE_JSON`:** Aceptado como observación informativa menor del frontend.
- **CI/CD:** Ausencia de pipeline de integración continua registrada como mejora futura fuera del alcance técnico de esta fase.

---

## 11. Conclusiones Finales

1. El sistema **TutorIA** cuenta con una base de código limpia, modular y segura, alineada con la Arquitectura Hexagonal y los estándares modernos de desarrollo en Python 3.14 / React Native SDK 54.
2. El entorno de ejecución está protegido contra malas configuraciones de seguridad mediante la validación de `APP_ENV` y restricciones en producción.
3. El benchmark RAG oficial de 15 casos provee una línea base cuantitativa reproducible y documentada con trazabilidad completa.

---

## 12. Estado de Cierre de las Fases

- **Fase 5 (Benchmark RAG y Análisis Cuantitativo):** **CERRADA**
- **Fase 6A (Auditoría Integral y Definición de Estado Final):** **COMPLETADA**
- **Fase 6B (Migración Pydantic V2 y Seguridad por Entorno):** **COMPLETADA**
- **Fase 6C (Cierre Documental Definitivo):** **COMPLETADA**
- **Cierre Técnico del Proyecto:** **COMPLETADO**
- **Fase 6D:** Corresponde a la entrega operativa e integración Git, sin alteración de las conclusiones técnicas.
