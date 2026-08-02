"""Ingesta incremental del corpus a pgvector (Fase 3)."""
import unittest
from unittest.mock import AsyncMock

from app.infrastructure.adapters.gemini_adapter import GeminiAdapter
from app.domain.exceptions import LLMAuthenticationError
from scripts.ingest_corpus import (
    TASK_TYPE_INDEXACION,
    clasificar,
    hash_contenido,
)


def _frag(fid: str, texto: str) -> dict:
    return {
        "fragment_id": fid,
        "texto": texto,
        "hash": hash_contenido(texto),
        "documento": "Doc",
        "articulo": None,
        "source": "doc",
    }


class TestHash(unittest.TestCase):
    def test_es_estable_para_el_mismo_texto(self):
        self.assertEqual(hash_contenido("texto normativo"), hash_contenido("texto normativo"))

    def test_cambia_ante_cualquier_edicion(self):
        self.assertNotEqual(hash_contenido("veinticinco (25)"), hash_contenido("veintiseis (26)"))


class TestClasificacion(unittest.TestCase):
    def setUp(self):
        self.fragmentos = [_frag("a#1", "uno"), _frag("a#2", "dos"), _frag("b#1", "tres")]

    def test_todo_es_nuevo_contra_un_indice_vacio(self):
        nuevos, modificados, obsoletos = clasificar(self.fragmentos, {})
        self.assertEqual(len(nuevos), 3)
        self.assertEqual(modificados, [])
        self.assertEqual(obsoletos, [])

    def test_no_reembebe_lo_que_no_cambio(self):
        """El ahorro central: agregar un documento no debe recostar el corpus entero."""
        existentes = {f["fragment_id"]: f["hash"] for f in self.fragmentos[:2]}
        nuevos, modificados, _ = clasificar(self.fragmentos, existentes)

        self.assertEqual([f["fragment_id"] for f in nuevos], ["b#1"])
        self.assertEqual(modificados, [])

    def test_detecta_un_fragmento_editado_por_su_hash(self):
        existentes = {f["fragment_id"]: f["hash"] for f in self.fragmentos}
        existentes["a#2"] = "hash-viejo"

        nuevos, modificados, _ = clasificar(self.fragmentos, existentes)
        self.assertEqual(nuevos, [])
        self.assertEqual([f["fragment_id"] for f in modificados], ["a#2"])

    def test_marca_como_obsoleto_lo_que_ya_no_esta_en_el_corpus(self):
        """Al reemplazar malla_curricular_2017 por malla_2017 hay que borrar los viejos."""
        existentes = {"a#1": self.fragmentos[0]["hash"], "viejo#9": "h"}
        _, _, obsoletos = clasificar(self.fragmentos, existentes)
        self.assertEqual(obsoletos, ["viejo#9"])

    def test_forzar_reembebe_todo(self):
        existentes = {f["fragment_id"]: f["hash"] for f in self.fragmentos}
        nuevos, modificados, _ = clasificar(self.fragmentos, existentes, forzar=True)
        self.assertEqual(len(nuevos), 3)
        self.assertEqual(modificados, [])


class TestEmbeddingAsimetrico(unittest.IsolatedAsyncioTestCase):
    async def test_la_indexacion_usa_retrieval_document(self):
        """La busqueda es asimetrica: documento y consulta no se embeben igual."""
        adapter = GeminiAdapter(api_key="clave")
        adapter.client = AsyncMock()
        adapter.client.aio.models.embed_content.return_value = type(
            "R", (), {"embeddings": [type("E", (), {"values": [0.1] * 768})()]}
        )()

        await adapter.compute_embedding("texto", task_type=TASK_TYPE_INDEXACION)

        config = adapter.client.aio.models.embed_content.call_args.kwargs["config"]
        self.assertEqual(config.task_type, "RETRIEVAL_DOCUMENT")
        self.assertEqual(config.output_dimensionality, 768)

    async def test_la_consulta_usa_retrieval_query_por_defecto(self):
        adapter = GeminiAdapter(api_key="clave")
        adapter.client = AsyncMock()
        adapter.client.aio.models.embed_content.return_value = type(
            "R", (), {"embeddings": [type("E", (), {"values": [0.1] * 768})()]}
        )()

        await adapter.compute_embedding("cuando me matriculo")

        config = adapter.client.aio.models.embed_content.call_args.kwargs["config"]
        self.assertEqual(config.task_type, "RETRIEVAL_QUERY")


class TestModoEstricto(unittest.IsolatedAsyncioTestCase):
    async def test_sin_clave_falla_en_vez_de_devolver_el_pseudo_embedding(self):
        """Un vector basura almacenado degrada la busqueda sin dejar rastro.

        Es preferible una siembra incompleta y visible a un corpus envenenado.
        """
        adapter = GeminiAdapter(api_key="", allow_embedding_fallback=False)
        with self.assertRaises(LLMAuthenticationError):
            await adapter.compute_embedding("texto", task_type=TASK_TYPE_INDEXACION)

    async def test_el_fallback_sigue_disponible_cuando_se_permite(self):
        adapter = GeminiAdapter(api_key="", allow_embedding_fallback=True)
        vector = await adapter.compute_embedding("texto")
        self.assertEqual(len(vector), 768)



class TestOrdenDeIngesta(unittest.TestCase):
    def test_intercala_documentos_en_vez_de_recorrerlos_en_serie(self):
        """Regresion de un fallo observado en una ingesta real.

        En orden alfabetico la cuota se agoto dentro de reglamento_academico y
        dejo reglamento_tutoria con cero fragmentos indexados. Como ese
        reglamento es la fuente de la mitad del golden set, la evaluacion
        parecia un fallo de recuperacion cuando en realidad el documento nunca
        habia llegado al indice.
        """
        from scripts.ingest_corpus import intercalar

        orden = intercalar({
            "a": [_frag("a#1", "1"), _frag("a#2", "2"), _frag("a#3", "3")],
            "z": [_frag("z#1", "1"), _frag("z#2", "2")],
        })

        fuentes = [f["fragment_id"].split("#")[0] for f in orden]
        self.assertEqual(fuentes, ["a", "z", "a", "z", "a"])

    def test_una_ingesta_parcial_cubre_todos_los_documentos(self):
        from scripts.ingest_corpus import intercalar

        por_doc = {f"doc{i}": [_frag(f"doc{i}#{j}", str(j)) for j in range(10)] for i in range(5)}
        orden = intercalar(por_doc)

        # Cortando en el primer 10% ya hay un fragmento de cada documento.
        primeros = {f["fragment_id"].split("#")[0] for f in orden[:5]}
        self.assertEqual(len(primeros), 5)

    def test_no_pierde_ni_duplica_fragmentos(self):
        from scripts.ingest_corpus import intercalar

        por_doc = {"a": [_frag("a#1", "1")], "b": [_frag(f"b#{j}", str(j)) for j in range(4)]}
        orden = intercalar(por_doc)

        self.assertEqual(len(orden), 5)
        self.assertEqual(len({f["fragment_id"] for f in orden}), 5)

if __name__ == "__main__":
    unittest.main()


class TestGuardaDeModelo(unittest.TestCase):
    """Cambiar la API key es inocuo; cambiar el modelo no.

    Los vectores no llevan marca de la cuenta, asi que rotar credenciales no
    afecta nada. Pero dos modelos producen espacios vectoriales distintos: una
    distancia entre un fragmento viejo y una consulta nueva deja de significar
    algo y la busqueda empeora sin que nada falle.
    """

    def test_un_indice_homogeneo_no_reporta_nada(self):
        from app.infrastructure.adapters.gemini_adapter import IDENTIDAD_EMBEDDING
        from scripts.ingest_corpus import verificar_modelo

        self.assertEqual(verificar_modelo({IDENTIDAD_EMBEDDING}), [])

    def test_detecta_un_modelo_ajeno(self):
        from app.infrastructure.adapters.gemini_adapter import IDENTIDAD_EMBEDDING
        from scripts.ingest_corpus import verificar_modelo

        ajenos = verificar_modelo({IDENTIDAD_EMBEDDING, "text-embedding-004@768"})
        self.assertEqual(ajenos, ["text-embedding-004@768"])

    def test_ignora_los_chunks_sin_modelo_declarado(self):
        """Los sembrados antes de la columna quedan en nulo; la migracion los rellena."""
        from app.infrastructure.adapters.gemini_adapter import IDENTIDAD_EMBEDDING
        from scripts.ingest_corpus import verificar_modelo

        self.assertEqual(verificar_modelo({IDENTIDAD_EMBEDDING, None}), [])

    def test_la_identidad_incluye_las_dimensiones(self):
        """El mismo modelo a otra dimensionalidad tampoco es comparable."""
        from app.infrastructure.adapters.gemini_adapter import (
            DIMENSIONES_EMBEDDING,
            IDENTIDAD_EMBEDDING,
            MODELO_EMBEDDING,
        )

        self.assertEqual(IDENTIDAD_EMBEDDING, f"{MODELO_EMBEDDING}@{DIMENSIONES_EMBEDDING}")
        self.assertEqual(DIMENSIONES_EMBEDDING, 768)
