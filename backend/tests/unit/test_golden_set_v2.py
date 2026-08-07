"""Integridad del golden set ampliado (v2).

El v1 quedo congelado por verify_evaluation_integrity.py, que fija sus hashes y
sus 15 ids. El v2 es un archivo aparte y necesita sus propias garantias.
"""
import json
import os
import unittest

from scripts.audit_corpus_coverage import DATASET_DIR, cargar_casos

RUTA_V2 = os.path.join(DATASET_DIR, "golden_set_v2.json")

# El Reglamento de Tutoria (CU-0220-2017) llega hasta el Art. 16 seguido de
# disposiciones finales. El v1 citaba Art. 18, 22, 23, 25 y 30, que no existen.
MAX_ARTICULO_REGLAMENTO_TUTORIA = 16


class TestGoldenSetV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(RUTA_V2, encoding="utf-8") as fh:
            cls.doc = json.load(fh)
        cls.casos = cargar_casos("v2")

    def test_carga_los_casos_y_no_las_notas_de_cambios(self):
        """El archivo tiene otras listas de nivel superior antes de 'casos'."""
        self.assertGreater(len(self.casos), 20)
        self.assertTrue(all(isinstance(c, dict) and "pregunta" in c for c in self.casos))

    def test_ids_unicos(self):
        ids = [c["id"] for c in self.casos]
        self.assertEqual(len(ids), len(set(ids)))

    def test_no_colisiona_con_los_ids_del_v1(self):
        """Los ids del v1 van del 1 al 32; el v2 arranca en 101 para no solaparse."""
        self.assertTrue(all(c["id"] >= 100 for c in self.casos))

    def test_todos_declaran_dominio_y_estado(self):
        for c in self.casos:
            self.assertIn("dominio", c, f"caso {c['id']} sin dominio")
            self.assertIn(c.get("estado"), ("verificado", "pendiente_documento"), f"caso {c['id']}")

    def test_los_verificados_declaran_fuente_salvo_fuera_de_alcance(self):
        for c in self.casos:
            if c.get("estado") != "verificado" or c["dominio"] == "fuera_de_alcance":
                continue
            self.assertIsNotNone(c.get("fuente"), f"caso {c['id']} verificado sin fuente")

    def test_no_cita_articulos_inexistentes_del_reglamento_de_tutoria(self):
        """Regresion del defecto encontrado en el v1.

        Citar un articulo que no existe vuelve la metrica de cobertura imposible
        de satisfacer y da una falsa sensacion de fallo de recuperacion.
        """
        import re

        for c in self.casos:
            for cita in c.get("articulos_referencia", []):
                if "Tutoría" not in cita and "Tutoria" not in cita:
                    continue
                m = re.search(r"Art\.\s*(\d+)", cita)
                if m:
                    self.assertLessEqual(
                        int(m.group(1)),
                        MAX_ARTICULO_REGLAMENTO_TUTORIA,
                        f"caso {c['id']} cita {cita}, fuera del articulado real",
                    )

    def test_cubre_todos_los_dominios_del_alcance(self):
        esperados = {
            "tutoria",
            "trayectoria_academica",
            "apoyos",
            "movilidad",
            "tramites",
            "calendario",
            "enrutamiento",
            "fuera_de_alcance",
            # Identidad de la carrera: mision, vision, autoridades, aniversario,
            # circulos de estudio y eventos. El corpus solo cubria la norma
            # universitaria, no la escuela concreta a la que pertenece quien pregunta.
            "escuela",
        }
        self.assertEqual(esperados, {c["dominio"] for c in self.casos})

    def test_incluye_casos_fuera_de_alcance(self):
        fuera = [c for c in self.casos if c["dominio"] == "fuera_de_alcance"]
        self.assertGreaterEqual(len(fuera), 3)
        for c in fuera:
            self.assertEqual(c["articulos_referencia"], ["NO_APLICA"])


if __name__ == "__main__":
    unittest.main()
