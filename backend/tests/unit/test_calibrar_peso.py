"""Seleccion del peso de autoridad a partir del barrido (Fase 4).

El peso se fijo en 0.5 porque funcionaba en la consulta con la que se
diagnostico el problema, el mismo error que tenia el umbral de distancia en
0.45. Lo que se prueba aca es el criterio de eleccion, que es donde esta el
juicio: mejorar el acierto de articulo sin degradar el de documento.
"""
import io
import unittest
from contextlib import redirect_stdout

from scripts.calibrar_peso_autoridad import informar


def _medicion(peso, art, doc, evaluables=10, casos=12, fallos=None):
    return {
        "peso": peso,
        "acierto_articulo": round(art / evaluables, 4),
        "aciertos_articulo": art,
        "evaluables_articulo": evaluables,
        "acierto_documento": round(doc / casos, 4),
        "aciertos_documento": doc,
        "casos": casos,
        "fallos_articulo": fallos or [],
    }


def _elegir(mediciones) -> float:
    with redirect_stdout(io.StringIO()):
        return informar(mediciones)


class TestSeleccionDelPeso(unittest.TestCase):
    def test_elige_el_peso_que_maximiza_el_acierto_de_articulo(self):
        elegido = _elegir([
            _medicion(0.0, art=6, doc=12),
            _medicion(0.5, art=9, doc=12),
            _medicion(1.0, art=8, doc=12),
        ])
        self.assertEqual(elegido, 0.5)

    def test_ante_empate_prefiere_el_peso_mas_bajo(self):
        """Menos intervencion sobre el ranking original ante igual resultado."""
        elegido = _elegir([
            _medicion(0.0, art=6, doc=12),
            _medicion(0.3, art=9, doc=12),
            _medicion(1.0, art=9, doc=12),
        ])
        self.assertEqual(elegido, 0.3)

    def test_descarta_un_peso_que_degrada_el_acierto_de_documento(self):
        """Un articulo muy autorizado de otro documento puede desplazar al correcto.

        Ganar articulo perdiendo documento no es una mejora: significa que la
        respuesta cita una norma que no corresponde a la consulta.
        """
        elegido = _elegir([
            _medicion(0.0, art=6, doc=12),
            _medicion(2.0, art=10, doc=9),   # mejor articulo, peor documento
            _medicion(0.5, art=8, doc=12),
        ])
        self.assertEqual(elegido, 0.5)

    def test_si_todo_peso_degrada_documento_recomienda_desactivarlo(self):
        elegido = _elegir([
            _medicion(0.0, art=6, doc=12),
            _medicion(0.5, art=9, doc=10),
            _medicion(1.0, art=10, doc=8),
        ])
        self.assertEqual(elegido, 0.0)

    def test_advierte_cuando_el_reordenamiento_no_aporta(self):
        salida = io.StringIO()
        with redirect_stdout(salida):
            informar([
                _medicion(0.0, art=9, doc=12),
                _medicion(0.5, art=9, doc=12),
            ])
        self.assertIn("no mejora el acierto", salida.getvalue())

    def test_no_advierte_cuando_si_aporta(self):
        salida = io.StringIO()
        with redirect_stdout(salida):
            informar([
                _medicion(0.0, art=6, doc=12),
                _medicion(0.5, art=9, doc=12),
            ])
        self.assertNotIn("no mejora el acierto", salida.getvalue())


if __name__ == "__main__":
    unittest.main()
