"""Guia de becas y comedor.

El riesgo de este documento es el que ya hundio a `servicios_bienestar`: una
parafrasis sin fuente que suena verosimil y compite con el articulado. Estas
pruebas fijan las dos defensas: cada entrada nombra la norma de la que sale, y
ningun fragmento se presenta como citable por articulo.
"""
import json
import os
import unittest

from app.application.dtos.corpus_dtos import MAX_CARACTERES_TEXTO, TipoDocumento
from scripts.extract_becas_comedor import construir

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FUENTE = os.path.join(BACKEND_DIR, "corpus_fuentes", "becas_y_comedor.json")


class TestBecasYComedor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(FUENTE, encoding="utf-8") as fh:
            cls.datos = json.load(fh)
        cls.doc = construir(cls.datos)
        cls.por_id = {f.id: f for f in cls.doc.fragmentos}

    def frag(self, sufijo):
        return self.por_id[f"becas_y_comedor#{sufijo}"]

    def test_toda_beca_declara_su_fundamento(self):
        """Sin la norma citada, esto es la parafrasis que ya fallo una vez."""
        for beca in self.datos["becas"]:
            self.assertTrue(beca["fundamento"], f"{beca['nombre']} no declara fundamento")

    def test_el_fundamento_llega_al_texto_del_fragmento(self):
        """De nada sirve en el archivo fuente si no viaja al chunk indexado."""
        for beca in self.datos["becas"]:
            fragmento = next(
                f for f in self.doc.fragmentos if f.titulo == beca["nombre"]
            )
            self.assertIn("Fundamento:", fragmento.texto)
            self.assertIn(beca["fundamento"][0], fragmento.texto)

    def test_separa_las_becas_propias_de_las_del_estado(self):
        """Decir que la UNSAAC 'otorga' Beca 18 seria falso: la concursa
        PRONABEC y la universidad solo asesora."""
        propias = self.frag("que-becas-existen").texto
        externas = self.frag("becas-externas").texto
        self.assertIn("Comedor universitario", propias)
        self.assertIn("PRONABEC", externas)
        self.assertIn("no otorga la Universidad", externas)

        # El indice de becas propias solo puede nombrar a PRONABEC para remitir,
        # nunca para atribuirse sus becas.
        listadas = propias.split("recursos propios:")[1].split("Aparte de estas")[0]
        self.assertNotIn("PRONABEC", listadas)
        self.assertIn("la Universidad no otorga", propias)

    def test_la_beca_externa_lo_dice_en_su_propio_fragmento(self):
        permanencia = next(
            f for f in self.doc.fragmentos if "Beca Permanencia" in f.titulo
        )
        self.assertIn("No la otorga la UNSAAC", permanencia.texto)

    def test_el_indice_nombra_las_becas_de_idiomas(self):
        """Eran las unicas becas de estudio articuladas y no estaban en el corpus."""
        texto = self.frag("que-becas-existen").texto
        self.assertIn("Instituto de Idiomas", texto)

    def test_el_comedor_explica_como_se_reserva_el_cupo(self):
        """La respuesta anterior se quedaba en 'hay evaluacion socioeconomica'
        y omitia lo unico que el estudiante tiene que hacer."""
        texto = self.frag("comedor-como-reservar-cupo").texto
        self.assertIn("bienestar.unsaac.edu.pe", texto)
        self.assertIn("código de estudiante", texto)
        self.assertIn("voucher de pago de matrícula", texto)

    def test_el_comedor_cita_la_norma_que_lo_hace_gratuito(self):
        texto = self.frag("comedor-quien-accede").texto
        self.assertIn("libre y gratuito", texto)
        self.assertIn("Art. 252", texto)

    def test_las_cifras_del_semestre_advierten_que_caducan(self):
        """El corpus no tiene ventana de vigencia: la advertencia va en el texto."""
        self.assertIn("cambian cada semestre", self.frag("comedor-cobertura").texto)

    def test_ningun_fragmento_lleva_articulo(self):
        """Es un indice, no una fuente: el Estatuto y el ROF deben ganarle."""
        self.assertTrue(all(f.articulo is None for f in self.doc.fragmentos))

    def test_procedencia_declara_la_base_legal(self):
        self.assertEqual(TipoDocumento.SERVICIO, self.doc.procedencia.tipo)
        self.assertTrue(self.doc.procedencia.base_legal)

    def test_los_fragmentos_son_autocontenidos(self):
        for f in self.doc.fragmentos:
            self.assertTrue(f.texto.startswith("Guía de becas"), f"{f.id} sin jerarquía")

    def test_ningun_fragmento_desborda_por_mucho(self):
        excedidos = [
            (len(f.texto), f.id)
            for f in self.doc.fragmentos
            if len(f.texto) > MAX_CARACTERES_TEXTO + 200
        ]
        self.assertEqual([], excedidos)
