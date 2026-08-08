"""Extraccion del plan de estudios tabular (Fase 2).

El plan no tiene articulado: es una tabla por semestre. El extractor de
articulado no aplica, y una fila cruda ("IFI02 | 4 | 3 | 2") no se parece a la
consulta real del estudiante, asi que el fragmento se redacta en prosa.
"""
import unittest

from scripts.extract_plan_estudios import construir, parsear, redactar

MD = """- II.3. Plan de estudios semestralizado

PRIMER SEMESTRE

| COD   | ASIGNATURA                    |   CR |   HT |   HP | REQ1   | REQ2   |
|-------|-------------------------------|------|------|------|--------|--------|
| QUG01 | QUÍMICA GENERAL               |    4 |    3 |    2 |        |        |
| MEG02 | CÁLCULO I                     |    4 |    3 |    2 |        |        |

Total Cr.  8

TERCER SEMESTRE

| COD   | ASIGNATURA                          |   CR |   HT |   HP | REQ1   | REQ2   |
|-------|-------------------------------------|------|------|------|--------|--------|
| IFI02 | ALGORITMOS Y ESTRUCTURAS DE DATOS I |    4 |    3 |    2 | IFI01  | IFG01  |
| IFI03 | PROGRAMACIÓN I                      |    2 |    0 |    4 | IFI01  |        |

Total Cr. 6
"""


class TestParseoDelPlan(unittest.TestCase):
    def setUp(self):
        self.semestres = parsear(MD)

    def test_reconoce_los_semestres_por_ordinal(self):
        self.assertEqual([s["numero"] for s in self.semestres], [1, 3])

    def test_lee_creditos_horas_y_requisitos(self):
        curso = self.semestres[1]["cursos"][0]
        self.assertEqual(curso["codigo"], "IFI02")
        self.assertEqual(curso["creditos"], "4")
        self.assertEqual(curso["horas_practicas"], "2")
        self.assertEqual(curso["requisitos"], ["IFI01", "IFG01"])

    def test_un_curso_sin_requisitos_queda_con_lista_vacia(self):
        self.assertEqual(self.semestres[0]["cursos"][0]["requisitos"], [])

    def test_captura_el_total_de_creditos(self):
        self.assertEqual([s["total_creditos"] for s in self.semestres], [8, 6])

    def test_ignora_la_fila_separadora_de_la_tabla(self):
        for s in self.semestres:
            self.assertTrue(all(c["codigo"] and "-" not in c["codigo"] for c in s["cursos"]))


class TestRedaccion(unittest.TestCase):
    def test_redacta_en_prosa_y_no_como_tabla(self):
        """El estudiante pregunta en lenguaje natural, no en filas."""
        texto = redactar(parsear(MD)[1], "2025")
        self.assertIn("Tercer semestre del Plan de Estudios 2025", texto)
        self.assertIn("2 asignaturas", texto)
        self.assertIn("6 créditos en total", texto)
        self.assertNotIn("|", texto)

    def test_expresa_los_requisitos_de_forma_legible(self):
        texto = redactar(parsear(MD)[1], "2025")
        self.assertIn("requisitos: IFI01, IFG01", texto)
        self.assertIn("sin requisitos", redactar(parsear(MD)[0], "2025"))


class TestDocumentoResultante(unittest.TestCase):
    def setUp(self):
        self.doc = construir(parsear(MD), "2025")

    def test_un_fragmento_por_semestre_mas_el_resumen(self):
        self.assertEqual(len(self.doc.fragmentos), 3)
        self.assertTrue(self.doc.fragmentos[-1].id.endswith("#resumen"))

    def test_el_resumen_suma_cursos_y_creditos(self):
        texto = self.doc.fragmentos[-1].texto
        self.assertIn("4 asignaturas", texto)
        self.assertIn("14 créditos", texto)

    def test_no_exige_articulo_por_no_ser_un_reglamento(self):
        """Una malla no tiene articulado; reclamarselo seria un error permanente."""
        self.assertEqual(self.doc.fragmentos_sin_articulo, [])

    def test_ids_estables_por_semestre(self):
        self.assertEqual(self.doc.fragmentos[0].id, "plan_estudios_2025#semestre-1")
        self.assertEqual(self.doc.fragmentos[1].id, "plan_estudios_2025#semestre-3")


if __name__ == "__main__":
    unittest.main()
