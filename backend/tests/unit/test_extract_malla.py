"""Conversion de la malla curricular transcrita a fragmentos del corpus."""
import json
import os
import unittest

from app.application.dtos.corpus_dtos import TipoDocumento
from scripts.extract_malla import construir, redactar_ciclo
from scripts.validate_malla import (
    CREDITOS_POR_CICLO_2017,
    TOTAL_ASIGNATURAS_2017,
    TOTAL_CREDITOS_2017,
    validar,
)

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

    def test_abre_con_la_forma_en_que_llega_la_consulta(self):
        """El chat antepone 'malla curricular Plan <anio>' a la pregunta. Medido,
        esa consulta devolvia seis fragmentos del plan 2025 y ninguno del 2017,
        porque solo las FAQ del 2025 estaban redactadas con esa forma."""
        texto = redactar_ciclo(MALLA["ciclos"][1], "2017", self.nombres)
        self.assertIn("¿Qué cursos se llevan en el sexto semestre bajo la malla curricular 2017?", texto)
        self.assertIn("¿Qué cursos llevo en el sexto ciclo del plan 2017?", texto)

    def test_entrega_el_codigo_con_el_que_se_matricula(self):
        """La imagen de la malla trae cinco codigos que el catalogo no reconoce.
        Responder solo con el de la imagen le da al estudiante una clave
        inservible para matricularse."""
        ciclo = {
            "ciclo": 3, "creditos_totales": 4, "cursos": [
                {"codigo": "IF351", "codigo_catalogo": "ME351", "nombre": "ALGEBRA LINEAL",
                 "creditos": 4, "categoria": "estudios_especificos", "requisitos": []},
            ],
        }
        texto = redactar_ciclo(ciclo, "2017", {})
        self.assertIn("IF351", texto)
        self.assertIn("ME351", texto)
        self.assertIn("con el que se matricula", texto)

    def test_no_aclara_nada_cuando_los_codigos_coinciden(self):
        """La aclaracion solo aparece donde hay discrepancia, no como muletilla."""
        self.assertNotIn(
            "con el que se matricula", redactar_ciclo(MALLA["ciclos"][0], "2017", self.nombres)
        )


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

    def test_declara_la_imagen_de_la_que_sale(self):
        """Sin URL, una respuesta sobre la malla no se puede contrastar."""
        con_url = construir({**MALLA, "url_fuente": "http://ejemplo/malla.jpg"}, "2017")
        self.assertEqual("http://ejemplo/malla.jpg", con_url.procedencia.url)

    def test_el_ciclo_con_casilleros_sin_nombre_remite_al_catalogo(self):
        """La imagen rotula 'ASIGNATURA DE ESPECIALIDAD' y no dice cual es.
        Recuperado aislado, ese ciclo dejaba al lector sin respuesta."""
        con_electivo = self.doc.fragmentos[1].texto
        self.assertIn("catálogo de asignaturas del Plan Curricular 2017", con_electivo)

    def test_el_ciclo_sin_casilleros_vacios_no_lleva_la_remision(self):
        """La nota solo aparece donde hace falta, no como muletilla."""
        self.assertNotIn("catálogo de asignaturas", self.doc.fragmentos[0].texto)


class TestTranscripcionVersionada(unittest.TestCase):
    """La transcripcion vivia fuera del repositorio y malla_2017.json no se
    podia regenerar. Ahora esta versionada y cuadra con la imagen oficial."""

    @classmethod
    def setUpClass(cls):
        backend = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        with open(os.path.join(backend, "corpus_fuentes", "malla_2017_transcrita.json"),
                  encoding="utf-8") as fh:
            cls.transcrita = json.load(fh)

    def test_cuadra_con_las_invariantes_que_declara_la_imagen(self):
        errores = validar(
            self.transcrita, CREDITOS_POR_CICLO_2017, TOTAL_ASIGNATURAS_2017, TOTAL_CREDITOS_2017
        )
        self.assertEqual([], errores)

    def test_declara_la_url_de_la_imagen_oficial(self):
        self.assertIn("malla-curricular-ing-informatica-2017", self.transcrita["url_fuente"])

    def test_regenera_el_documento_que_se_indexa(self):
        doc = construir(self.transcrita, "2017")
        self.assertEqual(11, len(doc.fragmentos))
        self.assertEqual(219, self.transcrita["total_creditos"])
        self.assertEqual(62, self.transcrita["total_asignaturas"])


if __name__ == "__main__":
    unittest.main()
