"""Conversion del portal de la Escuela Profesional a fragmentos del corpus.

Cubre las cinco consultas que no tenian de donde salir: mision, vision,
autoridades, aniversario y circulos de estudio y eventos de la carrera.
"""
import json
import os
import unittest

from app.application.dtos.corpus_dtos import MAX_CARACTERES_TEXTO, TipoDocumento
from scripts.extract_escuela import construir, slug

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FUENTE = os.path.join(BACKEND_DIR, "corpus", "fuentes", "escuela_informatica.json")


class TestEscuelaInformatica(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(FUENTE, encoding="utf-8") as fh:
            cls.datos = json.load(fh)
        cls.doc = construir(cls.datos)
        cls.por_id = {f.id: f for f in cls.doc.fragmentos}

    def frag(self, sufijo):
        return self.por_id[f"escuela_informatica#{sufijo}"]

    def test_procedencia_declara_el_portal_de_origen(self):
        self.assertEqual(TipoDocumento.SERVICIO, self.doc.procedencia.tipo)
        self.assertEqual("https://in.unsaac.edu.pe/", self.doc.procedencia.url)

    def test_mision_y_vision_son_de_la_carrera_no_de_la_universidad(self):
        """La UNSAAC publica su propia mision; la pregunta es por la carrera."""
        self.assertIn("Ingeniería Informática y de Sistemas", self.frag("mision").texto)
        self.assertIn("soluciones tecnológicas innovadoras", self.frag("mision").texto)
        self.assertIn("transformación digital", self.frag("vision").texto)

    def test_las_autoridades_traen_cargo_y_correo(self):
        texto = self.frag("autoridades").texto
        self.assertIn("Yeshica Isela Ormeño Ayala", texto)
        self.assertIn("yeshica.ormeno@unsaac.edu.pe", texto)
        self.assertIn("Decano", texto)
        self.assertIn("Director del Departamento Académico", texto)

    def test_el_aniversario_no_afirma_una_fecha_que_no_consta(self):
        """Las celebraciones se cuentan desde 1993 y la creacion es de 1971:
        la contradiccion se declara en vez de resolverse a ojo."""
        texto = self.frag("aniversario").texto
        self.assertIn("diciembre", texto)
        self.assertIn("13 de diciembre de 1971", texto)
        self.assertIn("No se ubicó una resolución", texto)

    def test_cada_hito_historico_cita_su_resolucion(self):
        texto = self.frag("resena-historica").texto
        self.assertIn("CG-110-71", texto)
        self.assertIn("CU-009-93", texto)

    def test_el_circulo_de_estudios_cita_la_resolucion_que_lo_crea(self):
        texto = self.frag("circulo-acm-unsaac-student-chapter").texto
        self.assertIn("D-2161-2025-FIEEIM-UNSAAC", texto)
        self.assertIn("ACM", texto)

    def test_hay_un_fragmento_por_evento_ademas_del_indice(self):
        """Juntos daban 2126 caracteres y mezclaban un concurso de programacion
        con un seminario de infraestructura, que no se parecen entre si."""
        indice = self.frag("eventos")
        self.assertIn("CUSCONTEST", indice.texto)
        self.assertIn("escuela_informatica#evento-cuscontest", self.por_id)
        self.assertIn("escuela_informatica#evento-neurokup", self.por_id)

    def test_los_eventos_advierten_que_las_fechas_caducan(self):
        self.assertIn("cambian en cada convocatoria", self.frag("eventos").texto)

    def test_el_equipo_docente_se_parte_por_la_categoria_del_portal(self):
        for grupo in self.datos["equipo_docente"]:
            self.assertIn(f"escuela_informatica#docentes-{slug(grupo['categoria'])}", self.por_id)

    def test_los_ids_son_ascii_y_estables(self):
        """El id viaja a la base como `fragment_id` y es la clave de la ingesta
        incremental: una tilde o un parentesis lo vuelven fragil."""
        for f in self.doc.fragmentos:
            sufijo = f.id.split("#", 1)[1]
            self.assertRegex(sufijo, r"^[a-z0-9-]+$", f"{f.id} no es un slug ASCII")

    def test_declara_el_ambito_de_cada_circulo(self):
        """Uno es de la escuela y otro de la facultad: decir que ambos son 'de
        la carrera' seria afirmar mas de lo que dice la fuente."""
        acm = self.frag("circulo-acm-unsaac-student-chapter")
        self.assertIn("cuenta con el círculo de estudios", acm.texto)
        ceit = next(f for f in self.doc.fragmentos if f.id.endswith("tecnologica-ceit"))
        self.assertIn("círculo de estudios de su facultad", ceit.texto)

    def test_ningun_fragmento_lleva_articulo(self):
        """El portal es fuente oficial de la escuela, pero no es articulado:
        no debe competir con un reglamento en el reordenamiento por autoridad."""
        self.assertTrue(all(f.articulo is None for f in self.doc.fragmentos))

    def test_los_fragmentos_son_autocontenidos(self):
        """Aislado, un fragmento tiene que decir de que escuela habla."""
        for f in self.doc.fragmentos:
            self.assertTrue(
                f.texto.startswith("Escuela Profesional de Ingeniería Informática"),
                f"{f.id} no antepone su jerarquía",
            )

    def test_ningun_fragmento_desborda_por_mucho(self):
        excedidos = [
            (len(f.texto), f.id)
            for f in self.doc.fragmentos
            if len(f.texto) > MAX_CARACTERES_TEXTO + 200
        ]
        self.assertEqual([], excedidos)

    def test_los_ids_no_se_repiten(self):
        ids = [f.id for f in self.doc.fragmentos]
        self.assertEqual(len(ids), len(set(ids)))
