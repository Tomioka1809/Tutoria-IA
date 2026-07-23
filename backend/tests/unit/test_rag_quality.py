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
    _normalized_stopword_key,
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

    # 4. Normalized stop words key ("cómo" -> "como", "qué" -> "que")
    def test_04_normalized_stopword_key(self):
        self.assertEqual(_normalized_stopword_key("cómo"), "como")
        self.assertEqual(_normalized_stopword_key("qué"), "que")
        self.assertEqual(_normalized_stopword_key("dónde"), "donde")
        self.assertEqual(_normalized_stopword_key("cuál"), "cual")
        self.assertEqual(_normalized_stopword_key("matrícula"), "matricula")

    # 5. Lexical fallback OR matching & preservation of accented terms
    async def test_05_lexical_fallback_accent_and_matching(self):

        mock_db = AsyncMock()
        repo = CorpusRepository(db=mock_db)

        vector_res = MagicMock()
        vector_res.all.return_value = []

        kw_c1 = MagicMock(text_content="Requisitos para matrícula extemporánea UNSAAC", source="reglamento.json")
        kw_res = MagicMock()
        kw_res.scalars().all.return_value = [kw_c1]

        mock_db.execute.side_effect = [vector_res, kw_res]

        query = "¿Cómo puedo realizar la matrícula extemporánea?"
        results = await repo.search_similar(
            query_embedding=[0.1]*768,
            limit=5,
            query_text=query,
            max_cosine_distance=0.45,
            keyword_fallback_limit=2
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].text, "Requisitos para matrícula extemporánea UNSAAC")
        self.assertEqual(results[0].retrieval_method, "keyword")

        self.assertEqual(mock_db.execute.call_count, 2)
        kw_call_stmt = mock_db.execute.call_args_list[1][0][0]
        compiled_sql = str(kw_call_stmt.compile(compile_kwargs={"literal_binds": True}))

        self.assertIn("OR", compiled_sql.upper())
        self.assertIn("%matricula%", compiled_sql)
        self.assertIn("%extemporanea%", compiled_sql)
        self.assertNotIn("%cómo%", compiled_sql)
        self.assertNotIn("%puedo%", compiled_sql)
        self.assertNotIn("%realizar%", compiled_sql)

    # 6. Keyword fallback deduplication and limit
    async def test_06_no_duplicates_and_limit_respected(self):
        mock_db = AsyncMock()
        repo = CorpusRepository(db=mock_db)

        c1 = MagicMock(text_content="Chunk 1", source="reglamento.json")
        vector_res = MagicMock()
        vector_res.all.return_value = [(c1, 0.2)]

        kw_c1 = MagicMock(text_content="Chunk 1", source="reglamento.json")
        kw_c2 = MagicMock(text_content="Chunk 2 matricula extemporanea", source="malla.json")
        kw_res = MagicMock()
        kw_res.scalars().all.return_value = [kw_c1, kw_c2]

        mock_db.execute.side_effect = [vector_res, kw_res]

        res = await repo.search_similar(
            query_embedding=[0.1]*768,
            limit=2,
            query_text="requisitos matricula extemporanea",
            max_cosine_distance=0.45,
            keyword_fallback_limit=2
        )

        self.assertEqual(len(res), 2)
        self.assertEqual(res[0].text, "Chunk 1")
        self.assertEqual(res[0].retrieval_method, "vector")
        self.assertEqual(res[1].text, "Chunk 2 matricula extemporanea")
        self.assertEqual(res[1].retrieval_method, "keyword")


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
        self.assertIn("6f892a019e42", heads[0])

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
