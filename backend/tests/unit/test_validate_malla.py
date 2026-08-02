"""Validacion de una malla curricular transcrita desde imagen."""
import unittest

from scripts.validate_malla import validar

# Malla de juguete: 2 ciclos, 10 y 12 creditos, 4 asignaturas, 22 en total.
ESPERADO = {1: 10, 2: 12}
TOTAL_ASIG = 4
TOTAL_CRED = 22


def _curso(codigo, creditos, requisitos=None, categoria="estudios_generales"):
    return {
        "codigo": codigo,
        "nombre": f"Curso {codigo}",
        "creditos": creditos,
        "categoria": categoria,
        "requisitos": requisitos or [],
    }


def _malla(**overrides):
    datos = {
        "plan": "2017",
        "ciclos": [
            {"ciclo": 1, "creditos_totales": 10, "cursos": [_curso("A1", 6), _curso("A2", 4)]},
            {"ciclo": 2, "creditos_totales": 12,
             "cursos": [_curso("B1", 6, ["A1"]), _curso("B2", 6)]},
        ],
    }
    datos.update(overrides)
    return datos


class TestMallaValida(unittest.TestCase):
    def test_una_transcripcion_correcta_no_reporta_errores(self):
        self.assertEqual(validar(_malla(), ESPERADO, TOTAL_ASIG, TOTAL_CRED), [])


class TestDeteccionDeErrores(unittest.TestCase):
    def _errores(self, malla):
        return validar(malla, ESPERADO, TOTAL_ASIG, TOTAL_CRED)

    def test_detecta_creditos_que_no_suman_lo_declarado(self):
        """El caso que motiva el validador: un digito mal leido de la imagen."""
        m = _malla()
        m["ciclos"][0]["cursos"][0]["creditos"] = 3
        errores = self._errores(m)
        self.assertTrue(any("suman 7" in e for e in errores))

    def test_detecta_desvio_contra_los_totales_de_la_imagen(self):
        m = _malla()
        m["ciclos"][1]["cursos"].append(_curso("B3", 0))
        self.assertTrue(any("creditos invalidos" in e for e in self._errores(m)))

    def test_detecta_codigos_duplicados(self):
        m = _malla()
        m["ciclos"][1]["cursos"][0]["codigo"] = "A1"
        self.assertTrue(any("duplicado" in e for e in self._errores(m)))

    def test_detecta_categoria_invalida(self):
        m = _malla()
        m["ciclos"][0]["cursos"][0]["categoria"] = "color_amarillo"
        self.assertTrue(any("categoria desconocida" in e for e in self._errores(m)))

    def test_detecta_requisito_hacia_un_curso_inexistente(self):
        """Suele indicar que se leyo mal el codigo al seguir una flecha."""
        m = _malla()
        m["ciclos"][1]["cursos"][0]["requisitos"] = ["ZZ99"]
        self.assertTrue(any("ZZ99" in e for e in self._errores(m)))

    def test_detecta_ciclos_faltantes(self):
        m = _malla()
        m["ciclos"] = m["ciclos"][:1]
        self.assertTrue(any("Faltan ciclos" in e for e in self._errores(m)))

    def test_rechaza_un_json_sin_ciclos(self):
        self.assertTrue(self._errores({"plan": "2017"}))


if __name__ == "__main__":
    unittest.main()
