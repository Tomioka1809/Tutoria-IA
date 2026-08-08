import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import os
import ast
import inspect
import sys
import subprocess
import shutil

from app.infrastructure.adapters.gemini_adapter import GeminiAdapter

from app.application.ports.repository_ports import CorpusRepositoryPort
from app.application.dtos.rag_dtos import RetrievedChunkDTO, RAGRetrievalPolicy
from app.application.use_cases.chat_use_cases import ChatUseCase
from app.infrastructure.database.repositories.corpus_repository import (
    CorpusRepository,
    fusionar_rrf,
)


class TestRAGQuality(unittest.IsolatedAsyncioTestCase):

    # 1. RAGRetrievalPolicy does NOT contain max_distance
    def test_01_rag_policy_has_no_max_distance(self):
        policy_fields = RAGRetrievalPolicy.model_fields.keys()
        self.assertNotIn("max_distance", policy_fields)
        self.assertIn("limit", policy_fields)
        self.assertIn("max_cosine_distance", policy_fields)
        self.assertIn("keyword_fallback_limit", policy_fields)

        with self.assertRaises(ValueError):
            RAGRetrievalPolicy(limit=5, keyword_fallback_limit=10)

    # 2. CorpusRepository does NOT contain distance_threshold
    def test_02_corpus_repo_has_no_distance_threshold(self):
        sig = inspect.signature(CorpusRepository.search_similar)
        params = sig.parameters.keys()
        self.assertNotIn("distance_threshold", params)
        self.assertIn("max_cosine_distance", params)
        self.assertIn("keyword_fallback_limit", params)

    # 3. Port and Repository signatures match
    def test_03_port_and_repository_signatures_match(self):
        port_sig = inspect.signature(CorpusRepositoryPort.search_similar)
        repo_sig = inspect.signature(CorpusRepository.search_similar)
        self.assertEqual(list(port_sig.parameters.keys()), list(repo_sig.parameters.keys()))

    # 4. Reciprocal Rank Fusion entre la rama vectorial y la lexica.
    # Reemplaza a la prueba de normalizacion de tildes: esa responsabilidad pasa a
    # la configuracion 'spanish' de Postgres, que ademas lematiza (con ella
    # "matricularse" encuentra "Matricula", cosa que el normalizador no hacia).
    def test_04_reciprocal_rank_fusion(self):
        vectorial = [10, 20, 30]
        lexica = [30, 40]

        puntajes = fusionar_rrf([vectorial, lexica], k=60)

        # 30 aparece en ambas ramas, asi que acumula y debe encabezar la fusion
        # pese a ir tercero en la vectorial y primero en la lexica.
        self.assertEqual(max(puntajes, key=puntajes.get), 30)
        self.assertAlmostEqual(puntajes[10], 1 / 61)
        self.assertAlmostEqual(puntajes[30], 1 / 63 + 1 / 61)
        # Un id presente en una sola rama conserva su aporte.
        self.assertAlmostEqual(puntajes[40], 1 / 62)

    def test_04b_rrf_sin_resultados(self):
        self.assertEqual(fusionar_rrf([[], []]), {})

    # 5. La rama lexica usa el indice de texto completo, no LIKE sobre la tabla.
    async def test_05_lexical_branch_uses_fulltext_index(self):
        mock_db = AsyncMock()
        repo = CorpusRepository(db=mock_db)

        vector_res = MagicMock()
        vector_res.all.return_value = []

        chunk = MagicMock(
            id=7,
            text_content="Requisitos para matrícula extemporánea UNSAAC",
            source="reglamento",
            documento="Reglamento Académico UNSAAC",
            articulo="Art. 9",
            autoridad=3,
        )
        lex_res = MagicMock()
        lex_res.all.return_value = [(chunk, 0.9)]

        mock_db.execute.side_effect = [vector_res, lex_res]

        results = await repo.search_similar(
            query_embedding=[0.1] * 768,
            limit=5,
            query_text="¿Cómo puedo realizar la matrícula extemporánea?",
            max_cosine_distance=0.45,
            keyword_fallback_limit=2,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].retrieval_method, "texto")
        # La procedencia viaja con el fragmento para que la respuesta pueda citarla.
        self.assertEqual(results[0].articulo, "Art. 9")
        self.assertEqual(results[0].documento, "Reglamento Académico UNSAAC")

        # Se compila con parametros ligados: el tipo regconfig del primer
        # argumento de plainto_tsquery no tiene renderizador literal.
        sql = str(mock_db.execute.call_args_list[1][0][0].compile())
        # El operador @@ contra plainto_tsquery aprovecha el indice GIN; el LIKE
        # anterior obligaba a recorrer la tabla entera en cada consulta.
        self.assertIn("@@", sql)
        self.assertIn("plainto_tsquery", sql)
        self.assertIn("ts_rank_cd", sql)
        self.assertNotIn("LIKE", sql.upper())

    # 6. Deduplicacion y limite sobre el resultado fusionado
    async def test_06_no_duplicates_and_limit_respected(self):
        mock_db = AsyncMock()
        repo = CorpusRepository(db=mock_db)

        c1 = MagicMock(id=1, text_content="Chunk 1", source="reglamento",
                       documento="Doc", articulo=None, autoridad=1)
        # Mismo texto con otro id: no debe ocupar dos de los pocos lugares que
        # se le entregan al LLM.
        c1_dup = MagicMock(id=2, text_content="Chunk 1", source="reglamento",
                           documento="Doc", articulo=None, autoridad=1)
        c2 = MagicMock(id=3, text_content="Chunk 2 matricula", source="malla",
                       documento="Doc", articulo=None, autoridad=1)

        vector_res = MagicMock()
        vector_res.all.return_value = [(c1, 0.2)]
        lex_res = MagicMock()
        lex_res.all.return_value = [(c1_dup, 0.8), (c2, 0.5)]

        mock_db.execute.side_effect = [vector_res, lex_res]

        res = await repo.search_similar(
            query_embedding=[0.1] * 768,
            limit=2,
            query_text="requisitos matricula extemporanea",
            max_cosine_distance=0.45,
            keyword_fallback_limit=2,
        )

        self.assertEqual([r.text for r in res], ["Chunk 1", "Chunk 2 matricula"])
        self.assertLessEqual(len(res), 2)

    # 6b. Un fragmento hallado por ambas ramas se marca como hibrido y encabeza.
    async def test_06b_hybrid_hit_ranks_first(self):
        mock_db = AsyncMock()
        repo = CorpusRepository(db=mock_db)

        solo_vector = MagicMock(id=1, text_content="A", source="s", documento="D", articulo=None, autoridad=1)
        ambos = MagicMock(id=2, text_content="B", source="s", documento="D", articulo=None, autoridad=1)

        vector_res = MagicMock()
        vector_res.all.return_value = [(solo_vector, 0.1), (ambos, 0.3)]
        lex_res = MagicMock()
        lex_res.all.return_value = [(ambos, 0.9)]

        mock_db.execute.side_effect = [vector_res, lex_res]

        res = await repo.search_similar(
            query_embedding=[0.1] * 768,
            limit=5,
            query_text="consulta",
            max_cosine_distance=0.45,
            keyword_fallback_limit=2,
        )

        self.assertEqual(res[0].text, "B")
        self.assertEqual(res[0].retrieval_method, "hibrido")
        self.assertEqual(res[1].retrieval_method, "vector")


    # 7. Short term minimum length (6+ chars)
    async def test_07_short_term_minimum_length(self):
        mock_db = AsyncMock()
        repo = CorpusRepository(db=mock_db)

        vector_res = MagicMock()
        vector_res.all.return_value = []
        mock_db.execute.return_value = vector_res

        res_short = await repo.search_similar(
            query_embedding=[0.1]*768,
            limit=5,
            query_text="hola",
            max_cosine_distance=0.45,
            keyword_fallback_limit=2
        )
        self.assertEqual(res_short, [])

    # 8. Out of domain query returns empty list
    async def test_08_out_of_domain_empty_list(self):
        mock_db = AsyncMock()
        repo = CorpusRepository(db=mock_db)

        vector_res = MagicMock()
        vector_res.all.return_value = []
        mock_db.execute.return_value = vector_res

        res = await repo.search_similar(
            query_embedding=[0.1]*768,
            limit=5,
            query_text="clima marte universo",
            max_cosine_distance=0.45,
            keyword_fallback_limit=2
        )
        self.assertEqual(res, [])

    # Los tests de rebuild_corpus_embeddings se retiran junto con el script:
    # re-embebia con el task_type por defecto (RETRIEVAL_QUERY), de modo que
    # correrlo habria reindexado el corpus como consultas y roto la asimetria.
    # Su funcion la cubre 'ingest_corpus --forzar', que si fija el task_type y
    # registra el modelo usado.

    # Portable Alembic Head Test
    def test_14_portable_alembic_head(self):
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        cmd = [sys.executable, "-m", "alembic", "heads"]
        res = subprocess.run(
            cmd,
            cwd=backend_dir,
            capture_output=True,
            text=True
        )
        self.assertEqual(
            res.returncode,
            0,
            f"Alembic heads failed with code {res.returncode}. Stderr: {res.stderr}"
        )
        heads = res.stdout.strip().splitlines()
        self.assertEqual(len(heads), 1, f"Expected 1 alembic head, got: {heads}")
        # Actualizar al agregar una migracion: la garantia que importa es que la
        # cadena siga siendo lineal y con una sola cabeza.
        self.assertIn("e7a3c9d15b28", heads[0])

    # Verification of no tracked API keys with pattern AIza
    @unittest.skipUnless(shutil.which("git"), "git executable not found in environment")
    def test_15_no_tracked_aiza_keys(self):

        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
        res = subprocess.run(
            ["git", "grep", "-IlE", "AIza[0-9A-Za-z_-]{20,}"],
            cwd=root_dir,
            capture_output=True,
            text=True
        )
        self.assertEqual(res.stdout.strip(), "", f"Tracked files contain API keys: {res.stdout}")

    # Pure application layer imports check
    def test_16_application_layer_purity(self):
        app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../app/application"))
        forbidden_prefixes = ["fastapi", "sqlalchemy", "app.infrastructure"]
        for root, _, files in os.walk(app_dir):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    with open(filepath, "r", encoding="utf-8") as f:
                        code = f.read()
                    parsed = ast.parse(code)
                    imported_modules = []
                    for node in ast.walk(parsed):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                imported_modules.append(alias.name)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                imported_modules.append(node.module)

                    for mod in imported_modules:
                        for prefix in forbidden_prefixes:
                            self.assertFalse(
                                mod.startswith(prefix),
                                f"Forbidden import '{mod}' found in {filepath}"
                            )


if __name__ == "__main__":
    unittest.main()


class TestPonderacionPorAutoridad(unittest.TestCase):
    """Regresion del fallo que motivo la Fase 4.

    Ante "que oficina se encarga del bienestar", el Art. 245 del Estatuto -la
    respuesta correcta- quedaba en la posicion 15 de 20, detras de cinco
    fragmentos de documentos heredados sin procedencia verificable. Con limit=6
    nunca llegaba al LLM. La similitud semantica sola no distingue una norma
    citable de un resumen que dice algo parecido.
    """

    def _chunk(self, autoridad):
        c = MagicMock()
        c.autoridad = autoridad
        return c

    def test_una_fuente_citable_supera_a_una_parafrasis_peor_rankeada(self):
        from app.infrastructure.database.repositories.corpus_repository import (
            ponderar_por_autoridad,
        )

        # La parafrasis va primera por similitud; la norma, decima.
        puntajes = {1: 1 / 61, 2: 1 / 70}
        chunks = {1: self._chunk(1), 2: self._chunk(3)}

        ponderados = ponderar_por_autoridad(puntajes, chunks, peso=0.5)
        self.assertGreater(ponderados[2], ponderados[1])

    def test_no_rescata_a_un_candidato_claramente_peor(self):
        """El factor reordena entre comparables, no invierte cualquier orden."""
        from app.infrastructure.database.repositories.corpus_repository import (
            ponderar_por_autoridad,
        )

        puntajes = {1: 1 / 61, 2: 1 / 500}
        chunks = {1: self._chunk(1), 2: self._chunk(3)}

        ponderados = ponderar_por_autoridad(puntajes, chunks, peso=0.5)
        self.assertGreater(ponderados[1], ponderados[2])

    def test_peso_cero_deja_la_fusion_intacta(self):
        """Permite medir el aporte del reordenamiento por separado."""
        from app.infrastructure.database.repositories.corpus_repository import (
            ponderar_por_autoridad,
        )

        puntajes = {1: 0.5, 2: 0.25}
        chunks = {1: self._chunk(1), 2: self._chunk(3)}
        self.assertEqual(ponderar_por_autoridad(puntajes, chunks, peso=0.0), puntajes)

    def test_un_chunk_sin_autoridad_no_rompe_el_calculo(self):
        from app.infrastructure.database.repositories.corpus_repository import (
            ponderar_por_autoridad,
        )

        ponderados = ponderar_por_autoridad({1: 0.5}, {}, peso=0.5)
        self.assertEqual(ponderados[1], 0.5)
