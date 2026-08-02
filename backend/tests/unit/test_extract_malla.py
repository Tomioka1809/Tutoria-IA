"""Conversion de la malla curricular transcrita a fragmentos del corpus."""
import unittest

from app.application.dtos.corpus_dtos import TipoDocumento
from scripts.extract_malla import construir, redactar_ciclo

MALLA = {
    "plan": "2017",
    "total_asignaturas": 3,
    "total_creditos": 11,
    "ciclos": [
        {"ciclo": 1, "creditos_totales": 7, "cursos": [
            {"codigo": "ME901", "nombre": "MATEMATICA I", "creditos": 4,
             "categoria": "estudios_generales", "requisitos": []},
            {"codigo": "FP901", "nombre": "FILOSOFIA Y ETICA", "creditos": 3,
             "categoria": "estudios_generales", "requisitos": []},
        ]},
        {"ciclo": 6, "creditos_totales": 4, "cursos": [
            {"codigo": "ELECTIVO-6-1", "nombre": "ASIGNATURA DE ESPECIALIDAD", "creditos": 4,
             "categoria": "estudios_especialidad", "requisitos": ["ME901"]},
        ]},
    ],
}


class TestRedaccionDeCiclo(unittest.TestCase):
    def setUp(self):
        self.nombres = {c["codigo"]: c["nombre"]
                        for ciclo in MALLA["ciclos"] for c in ciclo["cursos"]}

    def test_encabeza_con_el_ordinal_y_el_numero_de_semestre(self):
        """El estudiante dice 'sexto ciclo' o 'semestre 6' indistintamente."""
        texto = redactar_ciclo(MALLA["ciclos"][1], "2017", self.nombres)
        self.assertIn("Sexto ciclo (semestre 6)", texto)
        self.assertIn("malla curricular 2017", texto)

    def test_expresa_el_requisito_con_codigo_y_nombre(self):
        """Se pregunta por el nombre del curso, no por su clave."""
        texto = redactar_ciclo(MALLA["ciclos"][1], "2017", self.nombres)
        self.assertIn("requisito: ME901 MATEMATICA I", texto)

    def test_omite_el_codigo_ficticio_de_los_electivos(self):
        """'ELECTIVO-6-1' es un identificador interno, no un codigo real."""
        texto = redactar_ciclo(MALLA["ciclos"][1], "2017", self.nombres)
        self.assertNotIn("ELECTIVO-6-1", texto)
        self.assertIn("ASIGNATURA DE ESPECIALIDAD", texto)

    def test_traduce_la_categoria_a_texto_legible(self):
        texto = redactar_ciclo(MALLA["ciclos"][0], "2017", self.nombres)
        self.assertIn("estudios generales", texto)
        self.assertNotIn("estudios_generales", texto)

    def test_marca_los_cursos_sin_requisitos(self):
        self.assertIn("sin requisitos", redactar_ciclo(MALLA["ciclos"][0], "2017", self.nombres))


class TestDocumentoMalla(unittest.TestCase):
    def setUp(self):
        self.doc = construir(MALLA, "2017")

    def test_un_fragmento_por_ciclo_mas_el_resumen(self):
        self.assertEqual(len(self.doc.fragmentos), 3)
        self.assertTrue(self.doc.fragmentos[-1].id.endswith("#resumen"))

    def test_los_ids_usan_el_numero_de_ciclo_real_y_no_la_posicion(self):
        self.assertEqual(self.doc.fragmentos[1].id, "malla_2017#ciclo-6")

    def test_el_resumen_desglosa_creditos_por_categoria(self):
        texto = self.doc.fragmentos[-1].texto
        self.assertIn("11 créditos", texto)
        self.assertIn("Estudios generales: 7 créditos", texto)
        self.assertIn("Estudios de especialidad: 4 créditos", texto)

    def test_una_malla_no_requiere_articulado(self):
        self.assertEqual(self.doc.procedencia.tipo, TipoDocumento.MALLA)
        self.assertEqual(self.doc.fragmentos_sin_articulo, [])


if __name__ == "__main__":
    unittest.main()
