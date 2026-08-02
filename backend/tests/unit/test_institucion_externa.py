"""Guardado por institucion (Fase 3).

La calibracion del umbral dejo un caso sin resolver: preguntar por la matricula
de otra universidad peruana queda a distancia 0.291 del corpus, mas cerca que
varias preguntas legitimas. Es coherente, porque semanticamente SI es una
consulta sobre matricula universitaria; lo que difiere es la institucion. Ningun
umbral de distancia separa eso.
"""
import unittest

from app.application.use_cases.chat_use_cases import detectar_institucion_externa


class TestDeteccionDeInstitucionExterna(unittest.TestCase):
    def test_detecta_el_caso_que_el_umbral_no_podia_separar(self):
        institucion = detectar_institucion_externa(
            "¿Cuánto cuesta la matrícula en la Universidad Nacional de San Agustín de Arequipa?"
        )
        self.assertEqual(institucion, "Universidad Nacional de San Agustín de Arequipa")

    def test_detecta_por_sigla(self):
        self.assertIsNotNone(detectar_institucion_externa("cuanto cuesta estudiar en la UNSA"))
        self.assertIsNotNone(detectar_institucion_externa("requisitos de la PUCP"))
        self.assertIsNotNone(detectar_institucion_externa("horarios en San Marcos"))

    def test_no_confunde_unsa_dentro_de_unsaac(self):
        """'unsa' es prefijo de 'unsaac': sin limite de palabra bloquearia todo."""
        self.assertIsNone(detectar_institucion_externa("cuanto cuesta la matricula en la UNSAAC"))
        self.assertIsNone(detectar_institucion_externa("tramites en la unsaac"))

    def test_no_se_activa_si_la_consulta_nombra_a_la_unsaac(self):
        self.assertIsNone(
            detectar_institucion_externa("vengo de la UNSA y quiero estudiar en la UNSAAC")
        )
        self.assertIsNone(detectar_institucion_externa("soy de Cusco, estudie antes en San Marcos"))

    def test_no_bloquea_las_consultas_de_movilidad(self):
        """Convenios e intercambio son uno de los dominios del alcance.

        Un guardado que las bloqueara romperia justamente el dominio que se
        acaba de incorporar al golden set.
        """
        self.assertIsNone(detectar_institucion_externa("¿hay convenio con la PUCP?"))
        self.assertIsNone(
            detectar_institucion_externa("quiero postular a un intercambio con San Marcos")
        )
        self.assertIsNone(detectar_institucion_externa("movilidad estudiantil hacia la UNSA"))
        self.assertIsNone(detectar_institucion_externa("traslado externo desde la UNSA"))

    def test_no_se_activa_con_consultas_normales(self):
        for consulta in [
            "cuantos creditos puedo llevar por semestre",
            "quien es mi tutor",
            "cuando empieza la uni",  # 'uni' coloquial, no la UNI
            "",
        ]:
            self.assertIsNone(detectar_institucion_externa(consulta), consulta)

    def test_tolera_tildes_y_mayusculas(self):
        self.assertIsNotNone(detectar_institucion_externa("Católica del Perú"))
        self.assertIsNotNone(detectar_institucion_externa("CAYETANO HEREDIA"))


if __name__ == "__main__":
    unittest.main()
