"""Preparacion de datos de los graficos de evaluacion.

Se prueba el calculo y no el dibujo: lo que puede estar mal es el numero que
sostiene la barra. El unico caso que toca matplotlib es la prueba de humo, que
solo comprueba que los archivos se escriben.
"""
import json
import os
import tempfile
import unittest

from scripts.graficar_evaluacion import (
    acierto_por_dominio,
    curva_recall,
    curva_umbral,
    graficar,
    metricas_resumen,
    posiciones_primer_acierto,
    serie_peso_autoridad,
)


def caso(id_, dominio, art=None, doc=True, fuera=False, **extra):
    base = {
        "id": id_,
        "dominio": dominio,
        "fuera_de_alcance": fuera,
        "acierto_articulo": art,
        "acierto_documento": doc,
        "chunks_recuperados": 0 if fuera else 6,
    }
    base.update(extra)
    return base


DETALLE = [
    caso(1, "tutoria", art=True, recall_por_k={"1": 1.0, "2": 1.0}, posicion_primer_acierto=1),
    caso(2, "tutoria", art=False, recall_por_k={"1": 0.0, "2": 0.5}, posicion_primer_acierto=2),
    caso(3, "escuela", art=None, recall_por_k={"1": 1.0, "2": 1.0}, posicion_primer_acierto=1),
    caso(4, "fuera", fuera=True),
]


class TestAciertoPorDominio(unittest.TestCase):
    def setUp(self):
        self.filas = {f["dominio"]: f for f in acierto_por_dominio(DETALLE)}

    def test_excluye_los_casos_fuera_de_alcance(self):
        self.assertNotIn("fuera", self.filas)

    def test_cuenta_articulo_solo_sobre_los_evaluables(self):
        """Un dominio sin casos que citen articulado no tiene 0 aciertos: no
        tiene ninguno que evaluar, y la barra debe marcarse como n/a."""
        self.assertEqual(2, self.filas["tutoria"]["articulo_evaluables"])
        self.assertEqual(1, self.filas["tutoria"]["articulo_aciertos"])
        self.assertEqual(0, self.filas["escuela"]["articulo_evaluables"])

    def test_documento_se_evalua_en_todos(self):
        self.assertEqual(1, self.filas["escuela"]["documento_evaluables"])
        self.assertEqual(1, self.filas["escuela"]["documento_aciertos"])


class TestCurvaRecall(unittest.TestCase):
    def test_promedia_sobre_los_casos_en_alcance(self):
        ks, medias = curva_recall(DETALLE)
        self.assertEqual(1, ks[0])
        # k=1: (1.0 + 0.0 + 1.0) / 3
        self.assertAlmostEqual(2 / 3, medias[0], places=3)

    def test_arrastra_el_ultimo_valor_cuando_faltan_ks(self):
        """Regresion: el runner excluia esos casos y el graficador los
        arrastraba, asi que informe y grafico discrepaban para el mismo k."""
        ks, medias = curva_recall(DETALLE)
        # A partir de k=3 ningun caso tiene dato: se mantiene el de k=2.
        self.assertEqual(medias[1], medias[-1])

    def test_sin_datos_devuelve_listas_vacias(self):
        self.assertEqual(([], []), curva_recall([caso(9, "x", fuera=True)]))


class TestPosicionesYResumen(unittest.TestCase):
    def test_recoge_las_posiciones_del_primer_acierto(self):
        self.assertEqual([1, 2, 1], posiciones_primer_acierto(DETALLE))

    def test_el_resumen_omite_las_metricas_ausentes(self):
        pares = metricas_resumen({"acierto_documento": 1.0, "mrr": None})
        self.assertEqual([("Acierto de documento", 1.0)], pares)

    def test_el_resumen_respeta_el_orden_de_lectura(self):
        nombres = [n for n, _ in metricas_resumen({
            "acierto_documento": 1.0, "precision_at_k": 0.4, "mrr": 0.8,
        })]
        self.assertEqual(["Acierto de documento", "MRR", "Precision@k"], nombres)


class TestCurvasDeCalibracion(unittest.TestCase):
    def test_umbral_cuenta_recall_y_falsos_positivos(self):
        cal = {
            "en_alcance": [[1, 0.25], [2, 0.33]],
            "fuera_de_alcance": [[3, 0.29], [4, 0.45]],
        }
        umbrales, recalls, falsos = curva_umbral(cal)
        i30 = umbrales.index(0.30)
        self.assertEqual(0.5, recalls[i30])   # solo el de 0.25 entra
        self.assertEqual(1, falsos[i30])      # el de 0.29 se cuela

    def test_umbral_sin_datos_no_revienta(self):
        self.assertEqual(([], [], []), curva_umbral({"en_alcance": [], "fuera_de_alcance": []}))

    def test_serie_del_peso_de_autoridad(self):
        cal = {"mediciones": [{"peso": 0.0, "acierto_articulo": 0.7},
                              {"peso": 0.2, "acierto_articulo": 0.9}]}
        self.assertEqual(([0.0, 0.2], [0.7, 0.9]), serie_peso_autoridad(cal))


class TestHumo(unittest.TestCase):
    """Que los PNG se escriban de verdad: un grafico que no se genera no avisa."""

    def test_genera_archivos_png(self):
        informe = {
            "detalle": DETALLE,
            "politica": {"limit": 6, "max_cosine_distance": 0.34},
            "resumen": {
                "acierto_documento": 1.0,
                "acierto_articulo": 0.84,
                "mrr": 0.81,
                "precision_at_k": 0.42,
                "techo_precision_at_k": 0.53,
                "abstencion": {"tp": 3, "fn": 0, "fp": 0, "tn": 32,
                               "precision": 1.0, "recall": 1.0, "f1": 1.0,
                               "accuracy": 1.0, "n": 35},
            },
        }
        with tempfile.TemporaryDirectory() as destino:
            generados = graficar(informe, destino)
            self.assertGreaterEqual(len(generados), 3)
            for ruta in generados:
                self.assertTrue(os.path.exists(ruta), ruta)
                self.assertGreater(os.path.getsize(ruta), 1000, f"{ruta} quedo vacio")


class TestInformeReal(unittest.TestCase):
    """El informe que se versiona en el repositorio, no un caso de laboratorio."""

    RUTA = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "tests", "resultados", "fase5_eval_v2_corpus_completo.json",
    )

    @unittest.skipUnless(os.path.exists(RUTA), "sin informe generado")
    def test_las_metricas_estan_en_su_rango(self):
        with open(self.RUTA, encoding="utf-8") as fh:
            resumen = json.load(fh)["resumen"]

        for clave in ("mrr", "ndcg_at_k", "precision_at_k", "recall_at_k", "f1_at_k"):
            valor = resumen.get(clave)
            if valor is not None:
                self.assertGreaterEqual(valor, 0.0, clave)
                self.assertLessEqual(valor, 1.0, f"{clave}={valor} fuera de rango")

    @unittest.skipUnless(os.path.exists(RUTA), "sin informe generado")
    def test_la_precision_no_supera_su_techo(self):
        """Regresion: el techo se calculaba con la cantidad de citas esperadas y
        daba 0.182 contra una precision medida de 0.417, que es imposible."""
        with open(self.RUTA, encoding="utf-8") as fh:
            resumen = json.load(fh)["resumen"]
        techo = resumen.get("techo_precision_at_k")
        precision = resumen.get("precision_at_k")
        if techo is not None and precision is not None:
            self.assertLessEqual(precision, techo + 1e-9)


if __name__ == "__main__":
    unittest.main()
