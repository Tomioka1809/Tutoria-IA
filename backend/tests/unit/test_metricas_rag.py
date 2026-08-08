"""Metricas de recuperacion y de abstencion.

Varias pruebas son regresiones de defectos reales de la medicion anterior:
el articulo suelto que daba por acertada una cita de otro reglamento, y la
precision reportada sin su techo, que hacia parecer mala una recuperacion
perfecta.
"""
import unittest

from scripts.metricas_rag import (
    cita_cubierta,
    citas_cubiertas,
    confusion_abstencion,
    documento_coincide,
    f1,
    media,
    ndcg_at_k,
    partir_cita,
    percentil,
    posicion_primer_acierto,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    relevancias,
    techo_precision_at_k,
)


class ChunkFalso:
    def __init__(self, articulo=None, documento=None):
        self.articulo = articulo
        self.documento = documento


TUTORIA = "Reglamento de Tutoría Académica UNSAAC"
ESTATUTO = "Estatuto Universitario UNSAAC"


class TestPartirCita(unittest.TestCase):
    def test_separa_articulo_y_documento(self):
        self.assertEqual(("Art. 14", TUTORIA), partir_cita(f"Art. 14 - {TUTORIA}"))

    def test_ignora_el_numeral_dentro_del_articulo(self):
        art, _ = partir_cita(f"Art. 14 num. 2 - {TUTORIA}")
        self.assertEqual("Art. 14", art)

    def test_una_cita_sin_articulo_deja_el_articulo_nulo(self):
        self.assertEqual((None, "TUPA UNSAAC"), partir_cita("TUPA UNSAAC"))


class TestCoincidenciaDeDocumento(unittest.TestCase):
    def test_tolera_redacciones_distintas(self):
        self.assertTrue(documento_coincide(TUTORIA, "Reglamento de Tutoría Académica de la UNSAAC"))

    def test_distingue_documentos_diferentes(self):
        self.assertFalse(documento_coincide(TUTORIA, ESTATUTO))

    def test_un_documento_ausente_no_coincide(self):
        self.assertFalse(documento_coincide(TUTORIA, None))


class TestRelevanciaEstricta(unittest.TestCase):
    """Regresion: la medicion anterior comparaba el articulo contra el conjunto
    de articulos recuperados, sin mirar el documento. Como "Art. 14" existe en
    casi todos los reglamentos, bastaba recuperar el Art. 14 de cualquier norma
    para dar por acertada la cita del Reglamento de Tutoria."""

    def test_exige_articulo_y_documento(self):
        self.assertTrue(cita_cubierta(f"Art. 14 - {TUTORIA}", "Art. 14", TUTORIA))

    def test_el_articulo_correcto_en_otro_documento_no_cuenta(self):
        self.assertFalse(cita_cubierta(f"Art. 14 - {TUTORIA}", "Art. 14", ESTATUTO))

    def test_el_documento_correcto_con_otro_articulo_no_cuenta(self):
        self.assertFalse(cita_cubierta(f"Art. 14 - {TUTORIA}", "Art. 9", TUTORIA))

    def test_una_cita_sin_articulo_solo_exige_el_documento(self):
        self.assertTrue(cita_cubierta("TUPA UNSAAC", None, "TUPA UNSAAC"))
        self.assertTrue(cita_cubierta("TUPA UNSAAC", "Art. 3", "TUPA UNSAAC"))

    def test_marca_la_relevancia_en_el_orden_recuperado(self):
        chunks = [
            ChunkFalso("Art. 9", TUTORIA),
            ChunkFalso("Art. 14", TUTORIA),
            ChunkFalso("Art. 14", ESTATUTO),
        ]
        self.assertEqual([False, True, False], relevancias(chunks, [f"Art. 14 - {TUTORIA}"]))


class TestPrecisionYRecall(unittest.TestCase):
    def setUp(self):
        self.chunks = [
            ChunkFalso("Art. 9", TUTORIA),
            ChunkFalso("Art. 14", TUTORIA),
            ChunkFalso("Art. 246", ESTATUTO),
            ChunkFalso("Art. 3", TUTORIA),
        ]
        self.citas = [f"Art. 14 - {TUTORIA}", f"Art. 246 - {ESTATUTO}"]

    def test_precision_cuenta_relevantes_sobre_k(self):
        rels = relevancias(self.chunks, self.citas)
        self.assertEqual(0.5, precision_at_k(rels, 4))
        self.assertEqual(0.0, precision_at_k(rels, 1))

    def test_el_techo_de_precision_explica_un_valor_bajo(self):
        """Con una sola cita esperada y seis huecos, 1/6 ya es lo maximo."""
        self.assertAlmostEqual(1 / 6, techo_precision_at_k(1, 6))
        self.assertEqual(1.0, techo_precision_at_k(6, 6))

    def test_recall_mide_las_citas_esperadas_encontradas(self):
        self.assertEqual(1.0, recall_at_k(self.chunks, self.citas, 4))
        self.assertEqual(0.5, recall_at_k(self.chunks, self.citas, 2))
        self.assertEqual(0.0, recall_at_k(self.chunks, self.citas, 1))

    def test_recall_no_pasa_de_uno_con_varios_fragmentos_de_la_misma_cita(self):
        """Un articulo largo se parte en varios fragmentos: si los tres entran,
        la cita esta cubierta una vez, no tres."""
        repetidos = [ChunkFalso("Art. 14", TUTORIA) for _ in range(3)]
        self.assertEqual(1.0, recall_at_k(repetidos, [f"Art. 14 - {TUTORIA}"], 3))

    def test_citas_cubiertas_devuelve_cuales(self):
        self.assertEqual([f"Art. 14 - {TUTORIA}"], citas_cubiertas(self.chunks, self.citas, 2))

    def test_f1_equilibra_ambas(self):
        self.assertEqual(0.0, f1(0.0, 1.0))
        self.assertAlmostEqual(0.5, f1(0.5, 0.5))


class TestRanking(unittest.TestCase):
    def test_reciprocal_rank_usa_el_primer_acierto(self):
        self.assertEqual(1.0, reciprocal_rank([True, False]))
        self.assertEqual(0.5, reciprocal_rank([False, True]))
        self.assertAlmostEqual(1 / 3, reciprocal_rank([False, False, True]))

    def test_sin_aciertos_el_reciprocal_rank_es_cero(self):
        self.assertEqual(0.0, reciprocal_rank([False, False]))

    def test_posicion_del_primer_acierto(self):
        self.assertEqual(2, posicion_primer_acierto([False, True, True]))
        self.assertIsNone(posicion_primer_acierto([False, False]))

    def test_ndcg_premia_el_acierto_arriba(self):
        arriba = ndcg_at_k([True, False, False], total_relevantes=1, k=3)
        abajo = ndcg_at_k([False, False, True], total_relevantes=1, k=3)
        self.assertEqual(1.0, arriba)
        self.assertLess(abajo, arriba)

    def test_ndcg_es_cero_sin_aciertos(self):
        self.assertEqual(0.0, ndcg_at_k([False, False], total_relevantes=1, k=2))

    def test_ndcg_llega_a_uno_con_el_orden_ideal(self):
        self.assertEqual(1.0, ndcg_at_k([True, True, False], total_relevantes=2, k=3))

    def test_ndcg_nunca_pasa_de_uno(self):
        """Regresion: el ideal se calculaba con la cantidad de citas esperadas y
        no de fragmentos relevantes. Como un articulo se parte en varios
        fragmentos y todos cubren la misma cita, el DCG real superaba al ideal y
        la metrica devolvia 1.585."""
        tres_fragmentos_de_una_cita = [True, True, True]
        self.assertLessEqual(ndcg_at_k(tres_fragmentos_de_una_cita, total_relevantes=3, k=3), 1.0)

    def test_el_techo_de_precision_cuenta_fragmentos_no_citas(self):
        """Misma causa: con tres fragmentos relevantes en seis huecos el techo
        es 3/6, no 1/6 por haber esperado una sola cita."""
        self.assertAlmostEqual(0.5, techo_precision_at_k(3, 6))


class TestAbstencion(unittest.TestCase):
    """Positivo = el sistema se abstiene, la convencion de AbstentionBench."""

    def test_cuenta_los_cuatro_cuadrantes(self):
        casos = [
            {"fuera_de_alcance": True, "se_abstuvo": True},    # TP
            {"fuera_de_alcance": True, "se_abstuvo": False},   # FN: alucina
            {"fuera_de_alcance": False, "se_abstuvo": True},   # FP: se calla de mas
            {"fuera_de_alcance": False, "se_abstuvo": False},  # TN
        ]
        m = confusion_abstencion(casos)
        self.assertEqual((1, 1, 1, 1), (m["tp"], m["fn"], m["fp"], m["tn"]))
        self.assertEqual(0.5, m["precision"])
        self.assertEqual(0.5, m["recall"])
        self.assertEqual(0.5, m["accuracy"])

    def test_callarse_de_mas_baja_la_precision_no_el_recall(self):
        casos = [
            {"fuera_de_alcance": True, "se_abstuvo": True},
            {"fuera_de_alcance": False, "se_abstuvo": True},
        ]
        m = confusion_abstencion(casos)
        self.assertEqual(1.0, m["recall"])
        self.assertEqual(0.5, m["precision"])

    def test_no_divide_por_cero_sin_casos(self):
        m = confusion_abstencion([])
        self.assertEqual(0.0, m["f1"])
        self.assertEqual(0, m["n"])


class TestEstadisticos(unittest.TestCase):
    def test_percentil_interpola(self):
        self.assertEqual(3, percentil([1, 2, 3, 4, 5], 50))
        self.assertEqual(1, percentil([1], 95))

    def test_percentil_de_lista_vacia_es_nulo(self):
        self.assertIsNone(percentil([], 50))

    def test_media(self):
        self.assertEqual(2, media([1, 2, 3]))
        self.assertIsNone(media([]))


if __name__ == "__main__":
    unittest.main()
