"""Conversion del catalogo oficial del plan 2017 a fragmentos del corpus.

Varias pruebas son regresiones de defectos reales del corpus anterior: los
quince casilleros sin nombre, el fragmento de 3614 caracteres que metia treinta
y siete asignaturas en un mismo embedding, y los cinco codigos que la imagen de
la malla contradice.
"""
import json
import os
import unittest

from app.application.dtos.corpus_dtos import MAX_CARACTERES_TEXTO, TipoDocumento
from scripts.extract_catalogo_2017 import (
    construir,
    redactar_requisito,
    redactar_semestre,
    verificar,
)

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FUENTE = os.path.join(BACKEND_DIR, "corpus", "fuentes", "catalogo_2017.json")

CATALOGO_MINIMO = {
    "fuente": {"url": "http://ejemplo/catalogo"},
    "categorias": {
        "EG": "estudios generales",
        "EGT": "estudios generales del área técnica",
        "OEES": "estudios específicos",
        "EEEP": "estudios de especialidad",
        "AEX": "actividades extracurriculares",
        "PPP": "prácticas pre profesionales",
    },
    "totales_por_categoria": {"EG": 4, "EGT": 0, "OEES": 4, "EEEP": 4, "AEX": 2, "PPP": 9},
    "total_creditos": 23,
    "condicion_egresante": {
        "creditos_minimos_articulo_8": 180,
        "nota_articulo_8": "Créditos mínimos para el Artículo 8",
        "creditos_para_egresar": 23,
    },
    "discrepancias_con_la_malla": [
        {"asignatura": "ECUACIONES DIFERENCIALES", "codigo_catalogo": "ME356",
         "codigo_en_la_imagen": "ME359", "nota": "ME359 es ESTADÍSTICA APLICADA."},
    ],
    "semestres": [
        {"numero": 1, "cursos": [
            {"codigo": "ME901", "nombre": "MATEMÁTICA I", "creditos": 4,
             "categoria": "EG", "requisito": None},
        ]},
        {"numero": 6, "cursos": [
            {"codigo": "IF458", "nombre": "COMPUTACIÓN GRÁFICA I", "creditos": 4,
             "categoria": "EEEP", "requisito": "IF452*ME901"},
            {"codigo": "IF452", "nombre": "ALGORITMOS Y ESTRUCTURAS DE DATOS", "creditos": 4,
             "categoria": "OEES", "requisito": None},
            {"codigo": "IF060", "nombre": "MÚSICA", "creditos": 2,
             "categoria": "AEX", "requisito": "60 créditos"},
        ]},
    ],
    "electivos_y_complementarios": [
        {"codigo": "IF020", "nombre": "PRÁCTICAS PRE-PROFESIONALES", "creditos": 9,
         "categoria": "PPP", "requisito": "200 créditos"},
    ],
}


class TestRedaccion(unittest.TestCase):
    def setUp(self):
        self.nombres = {"ME901": "MATEMÁTICA I", "IF452": "ALGORITMOS Y ESTRUCTURAS DE DATOS"}

    def test_expande_el_requisito_a_codigo_y_nombre(self):
        """Se pregunta por el nombre del curso, no por su clave."""
        texto = redactar_requisito("IF452*ME901", self.nombres)
        self.assertIn("IF452 ALGORITMOS Y ESTRUCTURAS DE DATOS", texto)
        self.assertIn("ME901 MATEMÁTICA I", texto)

    def test_conserva_el_requisito_expresado_en_creditos(self):
        """'200 créditos' no es un codigo: se copia tal cual."""
        self.assertIn("200 créditos", redactar_requisito("200 créditos", self.nombres))

    def test_marca_las_asignaturas_sin_requisito(self):
        self.assertEqual("sin requisitos", redactar_requisito(None, self.nombres))

    def test_el_semestre_declara_ordinal_y_numero(self):
        """El estudiante dice 'sexto semestre' o 'semestre 6' indistintamente."""
        texto = redactar_semestre(
            CATALOGO_MINIMO["semestres"][1], CATALOGO_MINIMO["categorias"], self.nombres
        )
        self.assertIn("Sexto semestre", texto)
        self.assertIn("10 créditos", texto)


class TestVerificacion(unittest.TestCase):
    """Una transcripcion con un credito mal leido es peor que no tenerla."""

    def test_acepta_un_catalogo_que_cuadra(self):
        self.assertEqual([], verificar(CATALOGO_MINIMO))

    def test_rechaza_un_credito_que_no_suma(self):
        roto = json.loads(json.dumps(CATALOGO_MINIMO))
        roto["semestres"][0]["cursos"][0]["creditos"] = 3
        self.assertTrue(any("EG" in e for e in verificar(roto)))

    def test_rechaza_codigos_duplicados(self):
        roto = json.loads(json.dumps(CATALOGO_MINIMO))
        roto["electivos_y_complementarios"][0]["codigo"] = "ME901"
        self.assertTrue(any("duplicado" in e for e in verificar(roto)))

    def test_no_suma_especialidad_contra_el_total(self):
        """El catalogo oferta mas creditos EEEP de los 45 exigidos: el
        estudiante elige, asi que esa categoria no se puede cuadrar."""
        holgado = json.loads(json.dumps(CATALOGO_MINIMO))
        holgado["semestres"][1]["cursos"][0]["creditos"] = 99
        self.assertEqual([], verificar(holgado))


class TestConstruccion(unittest.TestCase):
    def setUp(self):
        self.doc = construir(CATALOGO_MINIMO)
        self.ids = {f.id for f in self.doc.fragmentos}

    def test_declara_procedencia_citable(self):
        self.assertEqual(TipoDocumento.MALLA, self.doc.procedencia.tipo)
        self.assertEqual(2017, self.doc.procedencia.anio)
        self.assertEqual("http://ejemplo/catalogo", self.doc.procedencia.url)

    def test_nombra_las_asignaturas_de_especialidad(self):
        """El defecto que motivo este documento: la imagen de la malla deja
        quince casilleros rotulados 'ASIGNATURA DE ESPECIALIDAD' sin nombre."""
        self.assertIn("plan_estudios_2017#especialidad-if458", self.ids)
        indice = next(f for f in self.doc.fragmentos if f.id.endswith("#especialidad-indice"))
        self.assertIn("COMPUTACIÓN GRÁFICA I", indice.texto)

    def test_cada_especialidad_dice_donde_la_ubica_el_catalogo(self):
        en_semestre = next(f for f in self.doc.fragmentos if f.id.endswith("#especialidad-if458"))
        self.assertIn("semestre 6", en_semestre.texto)

    def test_nombra_las_actividades_extracurriculares(self):
        frag = next(f for f in self.doc.fragmentos if f.id.endswith("#actividades-extracurriculares"))
        self.assertIn("IF060 MÚSICA", frag.texto)

    def test_da_codigo_a_la_practica_pre_profesional(self):
        """La imagen de la malla la muestra con el codigo incompleto 'IF'."""
        frag = next(f for f in self.doc.fragmentos if f.id.endswith("#practicas-pre-profesionales"))
        self.assertIn("IF020", frag.texto)

    def test_registra_las_discrepancias_de_codigo(self):
        """Quien mira la malla colgada lee ME359 y debe poder entender por que
        el catalogo dice ME356, en vez de recibir una contradiccion muda."""
        frag = next(f for f in self.doc.fragmentos if f.id.endswith("#discrepancias-de-codigo"))
        self.assertIn("ME356", frag.texto)
        self.assertIn("ME359", frag.texto)

    def test_declara_los_creditos_para_egresar(self):
        frag = next(f for f in self.doc.fragmentos if f.id.endswith("#creditos-y-egreso"))
        self.assertIn("180", frag.texto)
        self.assertIn("23 créditos para egresar", frag.texto)

    def test_ningun_fragmento_lleva_articulo(self):
        """Un catalogo no es articulado: no puede citarse como norma."""
        self.assertTrue(all(f.articulo is None for f in self.doc.fragmentos))


class TestCatalogoReal(unittest.TestCase):
    """El archivo que realmente se indexa, no un caso de laboratorio."""

    @classmethod
    def setUpClass(cls):
        with open(FUENTE, encoding="utf-8") as fh:
            cls.datos = json.load(fh)
        cls.doc = construir(cls.datos)

    def test_el_catalogo_versionado_cuadra_con_sus_totales(self):
        self.assertEqual([], verificar(self.datos))

    def test_declara_los_219_creditos_del_plan(self):
        self.assertEqual(219, self.datos["total_creditos"])

    def test_cubre_los_diez_semestres(self):
        self.assertEqual(
            list(range(1, 11)), [s["numero"] for s in self.datos["semestres"]]
        )

    def test_ningun_fragmento_desborda_por_mucho(self):
        """Un fragmento largo diluye su embedding entre varios temas. Se tolera
        un margen sobre el maximo para las listas homogeneas de asignaturas."""
        excedidos = [
            (len(f.texto), f.id)
            for f in self.doc.fragmentos
            if len(f.texto) > MAX_CARACTERES_TEXTO + 200
        ]
        self.assertEqual([], excedidos)
