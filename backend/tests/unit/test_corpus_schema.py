"""Contrato del esquema unico del corpus (Fase 1)."""
import unittest

from pydantic import ValidationError

from app.application.dtos.corpus_dtos import (
    DocumentoCorpus,
    Fragmento,
    Procedencia,
    TipoDocumento,
)


def _fragmento(fid: str = "doc#a", **kwargs) -> Fragmento:
    base = {
        "id": fid,
        "titulo": "Titulo de prueba",
        "texto": "Texto normativo suficientemente largo para la prueba.",
        "seccion": ["seccion"],
    }
    base.update(kwargs)
    return Fragmento(**base)


class TestFragmento(unittest.TestCase):
    def test_id_no_admite_espacios(self):
        # Los ids se usan como identificador estable del chunk; un espacio los
        # vuelve fragiles al serializarse en logs y en la tabla de corpus.
        with self.assertRaises(ValidationError):
            _fragmento("doc# con espacio")

    def test_detecta_seccion_conversacional(self):
        self.assertTrue(_fragmento(seccion=["saludos_y_despedidas"]).es_conversacional)
        self.assertTrue(_fragmento(seccion=["reglamento", "despedidas"]).es_conversacional)
        self.assertFalse(_fragmento(seccion=["tutoria_universitaria"]).es_conversacional)


class TestDocumentoCorpus(unittest.TestCase):
    def _doc(self, tipo: TipoDocumento, fragmentos: list[Fragmento]) -> DocumentoCorpus:
        return DocumentoCorpus(
            procedencia=Procedencia(documento="Documento de prueba", tipo=tipo),
            fragmentos=fragmentos,
        )

    def test_rechaza_ids_duplicados(self):
        with self.assertRaises(ValidationError):
            self._doc(TipoDocumento.REGLAMENTO, [_fragmento("doc#x"), _fragmento("doc#x")])

    def test_solo_los_reglamentos_exigen_articulo(self):
        sin_art = [_fragmento("doc#1"), _fragmento("doc#2")]

        self.assertEqual(len(self._doc(TipoDocumento.REGLAMENTO, sin_art).fragmentos_sin_articulo), 2)
        # Un glosario o un cronograma no tienen articulado; exigirselo produciria
        # errores permanentes que nunca podrian cerrarse.
        self.assertEqual(len(self._doc(TipoDocumento.GLOSARIO, sin_art).fragmentos_sin_articulo), 0)
        self.assertEqual(len(self._doc(TipoDocumento.CRONOGRAMA, sin_art).fragmentos_sin_articulo), 0)

    def test_el_articulo_declarado_cierra_el_pendiente(self):
        doc = self._doc(
            TipoDocumento.REGLAMENTO,
            [_fragmento("doc#1", articulo="Art. 15"), _fragmento("doc#2")],
        )
        pendientes = doc.fragmentos_sin_articulo
        self.assertEqual([f.id for f in pendientes], ["doc#2"])

    def test_los_conversacionales_no_cuentan_como_pendientes(self):
        # Un saludo no es un articulo: reclamarle numeracion mantendria el corpus
        # en error para siempre.
        doc = self._doc(
            TipoDocumento.REGLAMENTO,
            [_fragmento("doc#s", seccion=["saludos"]), _fragmento("doc#n")],
        )
        self.assertEqual([f.id for f in doc.fragmentos_sin_articulo], ["doc#n"])


if __name__ == "__main__":
    unittest.main()
