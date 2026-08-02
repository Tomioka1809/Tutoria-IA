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
from scripts.rebuild_corpus_embeddings import rebuild_corpus_embeddings


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
                       documento="Doc", articulo=None)
        # Mismo texto con otro id: no debe ocupar dos de los pocos lugares que
        # se le entregan al LLM.
        c1_dup = MagicMock(id=2, text_content="Chunk 1", source="reglamento",
                           documento="Doc", articulo=None)
        c2 = MagicMock(id=3, text_content="Chunk 2 matricula", source="malla",
                       documento="Doc", articulo=None)

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

        solo_vector = MagicMock(id=1, text_content="A", source="s", documento="D", articulo=None)
        ambos = MagicMock(id=2, text_content="B", source="s", documento="D", articulo=None)

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

    # Functional Tests for rebuild_corpus_embeddings.py
    @patch("scripts.rebuild_corpus_embeddings.settings")
    @patch("scripts.rebuild_corpus_embeddings.SessionLocal")
    @patch("scripts.rebuild_corpus_embeddings.GeminiAdapter")
    async def test_09_rebuild_script_missing_key(self, mock_adapter_cls, mock_session_cls, mock_settings):
        mock_settings.GEMINI_API_KEY = ""
        with self.assertRaises(RuntimeError):
            await rebuild_corpus_embeddings()
        mock_session_cls.assert_not_called()
        mock_adapter_cls.assert_not_called()

    @patch("scripts.rebuild_corpus_embeddings.settings")
    @patch("scripts.rebuild_corpus_embeddings.SessionLocal")
    @patch("scripts.rebuild_corpus_embeddings.GeminiAdapter")
    async def test_10_rebuild_script_normal_execution(self, mock_adapter_cls, mock_session_cls, mock_settings):
        mock_settings.GEMINI_API_KEY = "valid_key"
        mock_adapter = AsyncMock()
        mock_adapter.compute_embedding.return_value = [0.1] * 768
        mock_adapter_cls.return_value = mock_adapter

        chunk1 = MagicMock(id=1, text_content="c1", embedding=None)
        chunk2 = MagicMock(id=2, text_content="c2", embedding=None)

        session_instance = AsyncMock()
        session_result = MagicMock()
        session_result.scalars().all.return_value = [chunk1, chunk2]
        session_instance.execute.return_value = session_result
        mock_session_cls.return_value.__aenter__.return_value = session_instance

        count = await rebuild_corpus_embeddings(dry_run=False)

        self.assertEqual(count, 2)
        mock_adapter_cls.assert_called_once_with(api_key="valid_key", allow_embedding_fallback=False)
        self.assertEqual(chunk1.embedding, [0.1] * 768)
        self.assertEqual(chunk2.embedding, [0.1] * 768)
        session_instance.commit.assert_called_once()
        session_instance.rollback.assert_not_called()

    @patch("scripts.rebuild_corpus_embeddings.settings")
    @patch("scripts.rebuild_corpus_embeddings.SessionLocal")
    @patch("scripts.rebuild_corpus_embeddings.GeminiAdapter")
    async def test_11_rebuild_script_dry_run(self, mock_adapter_cls, mock_session_cls, mock_settings):
        mock_settings.GEMINI_API_KEY = "valid_key"
        mock_adapter = AsyncMock()
        mock_adapter.compute_embedding.return_value = [0.2] * 768
        mock_adapter_cls.return_value = mock_adapter

        chunk1 = MagicMock(id=1, text_content="c1", embedding=None)
        session_instance = AsyncMock()
        session_result = MagicMock()
        session_result.scalars().all.return_value = [chunk1]
        session_instance.execute.return_value = session_result
        mock_session_cls.return_value.__aenter__.return_value = session_instance

        count = await rebuild_corpus_embeddings(dry_run=True)

        self.assertEqual(count, 1)
        self.assertIsNone(chunk1.embedding)
        session_instance.commit.assert_not_called()
        session_instance.rollback.assert_called_once()

    @patch("scripts.rebuild_corpus_embeddings.settings")
    @patch("scripts.rebuild_corpus_embeddings.SessionLocal")
    @patch("scripts.rebuild_corpus_embeddings.GeminiAdapter")
    async def test_12_rebuild_script_intermediate_failure(self, mock_adapter_cls, mock_session_cls, mock_settings):
        mock_settings.GEMINI_API_KEY = "valid_key"
        mock_adapter = AsyncMock()
        mock_adapter.compute_embedding.side_effect = [
            [0.1] * 768,
            RuntimeError("API Failure on chunk 2")
        ]
        mock_adapter_cls.return_value = mock_adapter

        chunk1 = MagicMock(id=1, text_content="c1", embedding=None)
        chunk2 = MagicMock(id=2, text_content="c2", embedding=None)

        session_instance = AsyncMock()
        session_result = MagicMock()
        session_result.scalars().all.return_value = [chunk1, chunk2]
        session_instance.execute.return_value = session_result
        mock_session_cls.return_value.__aenter__.return_value = session_instance

        with self.assertRaises(RuntimeError):
            await rebuild_corpus_embeddings(dry_run=False)

        self.assertIsNone(chunk1.embedding)
        self.assertIsNone(chunk2.embedding)
        session_instance.commit.assert_not_called()
        session_instance.rollback.assert_called_once()

    @patch("scripts.rebuild_corpus_embeddings.settings")
    @patch("scripts.rebuild_corpus_embeddings.SessionLocal")
    @patch("scripts.rebuild_corpus_embeddings.GeminiAdapter")
    async def test_13_rebuild_script_invalid_dimension(self, mock_adapter_cls, mock_session_cls, mock_settings):
        mock_settings.GEMINI_API_KEY = "valid_key"
        mock_adapter = AsyncMock()
        mock_adapter.compute_embedding.return_value = [0.1] * 500
        mock_adapter_cls.return_value = mock_adapter

        chunk1 = MagicMock(id=1, text_content="c1", embedding=None)
        session_instance = AsyncMock()
        session_result = MagicMock()
        session_result.scalars().all.return_value = [chunk1]
        session_instance.execute.return_value = session_result
        mock_session_cls.return_value.__aenter__.return_value = session_instance

        with self.assertRaises(RuntimeError):
            await rebuild_corpus_embeddings(dry_run=False)

        session_instance.commit.assert_not_called()
        session_instance.rollback.assert_called_once()

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
        self.assertIn("b2f8d3c15e47", heads[0])

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
