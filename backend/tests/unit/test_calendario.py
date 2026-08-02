"""Extraccion del calendario academico desde el Markdown con OCR (Fase 2)."""
import unittest

from app.application.dtos.corpus_dtos import MAX_CARACTERES_TEXTO, TipoDocumento
from scripts.extract_calendario import construir, parsear

MD = """## Calendario

| SEMESTRE ACADÉMICO 2026 1 | SEMESTRE ACADÉMICO 2026 1                  | FECHAS                      |
|---------------------------|--------------------------------------------|-----------------------------|
| 2                         | Matrícula de reinicio de estudios           | 20 al 27 de febrero de 2026 |
| 3                         | Matrícula de   estudiantes  regulares       | 02 al 06 de marzo de 2026   |
|                           | NOTA: No se aceptará matrícula extemporánea | NOTA: No se aceptará        |
| 6                         | Inicio de actividades lectivas              | 30 de marzo 2026            |
| 7                         | Sin fecha asociada                          |                             |
"""


class TestParseoCalendario(unittest.TestCase):
    def setUp(self):
        self.filas = parsear(MD)

    def test_extrae_actividad_y_fecha(self):
        self.assertEqual(self.filas[1]["actividad"], "Matrícula de estudiantes regulares")
        self.assertEqual(self.filas[1]["fechas"], "02 al 06 de marzo de 2026")

    def test_normaliza_los_espacios_multiples_del_ocr(self):
        """El OCR deja espacios irregulares dentro de las celdas."""
        self.assertNotIn("  ", self.filas[1]["actividad"])

    def test_descarta_filas_sin_fecha(self):
        self.assertTrue(all(f["fechas"] for f in self.filas))
        self.assertNotIn("Sin fecha asociada", [f["actividad"] for f in self.filas])

    def test_descarta_las_notas_al_pie(self):
        self.assertFalse(any(f["actividad"].upper().startswith("NOTA") for f in self.filas))

    def test_no_duplica_cuando_docling_repite_columnas(self):
        """Con celdas combinadas docling emite la misma columna dos veces."""
        claves = [(f["actividad"], f["fechas"]) for f in self.filas]
        self.assertEqual(len(claves), len(set(claves)))


class TestDocumentoCalendario(unittest.TestCase):
    def setUp(self):
        self.doc = construir(parsear(MD), 2026, "Resolución Nro. CU-014-2026-UNSAAC")

    def test_declara_procedencia_y_tipo(self):
        self.assertEqual(self.doc.procedencia.tipo, TipoDocumento.CRONOGRAMA)
        self.assertEqual(self.doc.procedencia.anio, 2026)
        self.assertIn("CU-014-2026", self.doc.procedencia.resolucion)

    def test_cada_fragmento_repite_el_encabezado_para_ser_autocontenido(self):
        for f in self.doc.fragmentos:
            self.assertIn("Calendario Académico 2026", f.texto)

    def test_respeta_el_limite_de_tamano(self):
        muchas = [{"actividad": f"Actividad numero {i}", "fechas": f"{i} de marzo de 2026"}
                  for i in range(200)]
        doc = construir(muchas, 2026, "Resolución Nro. CU-014-2026-UNSAAC")
        self.assertGreater(len(doc.fragmentos), 1)
        for f in doc.fragmentos:
            self.assertLessEqual(len(f.texto), MAX_CARACTERES_TEXTO)

    def test_un_cronograma_no_requiere_articulado(self):
        self.assertEqual(self.doc.fragmentos_sin_articulo, [])


if __name__ == "__main__":
    unittest.main()
