"""Regresiones de la conversion del corpus y de la auditoria de cobertura."""
import unittest

from app.application.dtos.corpus_dtos import MAX_CARACTERES_TEXTO, TipoDocumento
from scripts.audit_corpus_coverage import auditar_caso, normalizar
from scripts.convert_corpus import convertir, etiqueta_de_item, render


class TestConversionCorpus(unittest.TestCase):
    def test_descompone_los_dict_grandes_en_lugar_de_aplanarlos(self):
        """El defecto original: un dict entero colapsaba en UN fragmento.

        En el corpus real, 'tutoria_universitaria' agrupaba nueve subclaves en un
        solo chunk de 3729 caracteres, de modo que el dato buscado quedaba diluido
        en un embedding que promediaba nueve temas distintos.
        """
        datos = {
            "documento": "Reglamento de prueba",
            "tema_grande": {
                f"subclave_{i}": "y ".join(["contenido normativo extenso"] * 12)
                for i in range(9)
            },
        }
        doc = convertir("reglamento_tutoria.json", datos)

        self.assertGreater(len(doc.fragmentos), 1, "el dict grande no se descompuso")
        secciones = {tuple(f.seccion) for f in doc.fragmentos}
        self.assertIn(("tema_grande", "subclave_0"), secciones)

    def test_ningun_fragmento_divisible_supera_el_limite(self):
        datos = {
            "documento": "Documento de prueba",
            "raiz": {f"hijo_{i}": "contenido normativo " * 15 for i in range(6)},
        }
        doc = convertir("reglamento_tutoria.json", datos)

        self.assertEqual(len(doc.fragmentos), 6, "no descendio hasta los hijos")
        for f in doc.fragmentos:
            self.assertLessEqual(
                len(f.texto), MAX_CARACTERES_TEXTO,
                f"{f.id} supera el limite y era divisible",
            )

    def test_una_hoja_indivisible_puede_superar_el_limite(self):
        """Comportamiento aceptado y explicito.

        Un string unico mas largo que el limite no se parte, porque cortarlo por
        caracteres romperia la unidad semantica. El validador lo reporta como
        aviso, no como error.
        """
        datos = {"documento": "Documento de prueba", "articulo_unico": "palabra " * 300}
        doc = convertir("reglamento_tutoria.json", datos)

        self.assertEqual(len(doc.fragmentos), 1)
        self.assertGreater(len(doc.fragmentos[0].texto), MAX_CARACTERES_TEXTO)

    def test_el_texto_incluye_la_ruta_como_encabezado(self):
        """Un fragmento aislado debe ser autocontenido.

        Sin la ruta delante, '25 estudiantes' no se puede recuperar ni citar.
        """
        datos = {
            "documento": "Reglamento de prueba",
            "tutoria": {"maximo": "No supera los 25 estudiantes."},
        }
        doc = convertir("reglamento_tutoria.json", datos)
        fragmento = doc.fragmentos[0]

        self.assertTrue(fragmento.texto.startswith("Tutoria"))
        self.assertIn("25 estudiantes", fragmento.texto)

    def test_un_dict_que_entra_en_el_limite_no_se_descompone(self):
        """Contrapeso de la descomposicion: evita generar micro-fragmentos.

        El corpus heredado tenia chunks de 57 caracteres sin contexto util. Si un
        dict completo cabe en el limite, se conserva entero.
        """
        datos = {
            "documento": "Reglamento de prueba",
            "tutoria": {"maximo": "No supera los 25 estudiantes.", "duracion": "Un semestre."},
        }
        doc = convertir("reglamento_tutoria.json", datos)

        self.assertEqual(len(doc.fragmentos), 1)
        self.assertEqual(doc.fragmentos[0].seccion, ["tutoria"])
        self.assertIn("25 estudiantes", doc.fragmentos[0].texto)
        self.assertIn("Un semestre", doc.fragmentos[0].texto)

    def test_las_etiquetas_de_lista_usan_texto_legible_no_slug(self):
        """La etiqueta termina embebida en el vector; un slug truncado lo degrada."""
        item = {"pregunta": "¿Qué cursos electivos hay?", "respuesta": "Varios."}
        self.assertEqual(etiqueta_de_item(item, 0), "¿Qué cursos electivos hay?")
        self.assertEqual(etiqueta_de_item({"termino": "Tutorado"}, 0), "Tutorado")
        self.assertEqual(etiqueta_de_item("sin dict", 3), "3")

    def test_las_claves_de_metadato_no_generan_fragmentos(self):
        datos = {
            "universidad": "UNSAAC",
            "documento": "Glosario de prueba",
            "base_legal": ["Ley 30220"],
            "contenido": "Texto real del glosario.",
        }
        doc = convertir("glosario.json", datos)
        self.assertEqual([f.seccion for f in doc.fragmentos], [["contenido"]])
        self.assertEqual(doc.procedencia.base_legal, ["Ley 30220"])

    def test_asigna_el_tipo_segun_el_archivo(self):
        datos = {"documento": "Documento de prueba", "contenido": "Texto del documento."}
        self.assertEqual(convertir("glosario.json", datos).procedencia.tipo, TipoDocumento.GLOSARIO)
        self.assertEqual(
            convertir("reglamento_tutoria.json", datos).procedencia.tipo,
            TipoDocumento.REGLAMENTO,
        )
        self.assertEqual(
            convertir("cronograma_academico.json", datos).procedencia.tipo,
            TipoDocumento.CRONOGRAMA,
        )

    def test_render_no_deja_sintaxis_json_en_el_texto(self):
        salida = render({"clave_uno": ["a", "b"], "clave_dos": "valor"})
        for simbolo in ("{", "}", "[", "]", '"'):
            self.assertNotIn(simbolo, salida)


class TestAuditoriaCobertura(unittest.TestCase):
    UNIDADES = [
        ("doc#a", normalizar("El maximo de tutorados por profesor es 25 estudiantes")),
        ("doc#b", normalizar("En el segundo ciclo se llevan 6 cursos, total de 22 creditos")),
        ("doc#c", normalizar("El semestre academico ordinario se organiza por ciclos")),
    ]

    def _caso(self, **kwargs):
        base = {
            "id": 1,
            "categoria": "facil",
            "pregunta": "?",
            "articulos_referencia": ["Art. 1 - Reglamento"],
            "palabras_clave_esperadas": [],
        }
        base.update(kwargs)
        return base

    def test_penaliza_las_palabras_dispersas_entre_secciones(self):
        """Regresion del falso positivo detectado en la auditoria.

        '22 creditos', 'maximo' y 'semestre' existen en el corpus, pero en
        secciones sin relacion: hablan de la carga de un ciclo, no del maximo
        matriculable. Contarlo como cubierto inflaba el techo del RAG.
        """
        corpus = " ".join(t for _, t in self.UNIDADES)
        caso = self._caso(palabras_clave_esperadas=["22 creditos", "maximo", "semestre"])

        resultado = auditar_caso(caso, corpus, self.UNIDADES, {})

        self.assertEqual(resultado.ratio_corpus, 1.0, "las tres aparecen en el corpus")
        self.assertLess(resultado.ratio, 1.0, "pero no co-ocurren en una sola seccion")
        self.assertNotEqual(resultado.veredicto, "CUBIERTO")

    def test_marca_cubierto_cuando_co_ocurren_en_una_unidad(self):
        caso = self._caso(palabras_clave_esperadas=["maximo", "25 estudiantes"])
        resultado = auditar_caso(caso, " ".join(t for _, t in self.UNIDADES), self.UNIDADES, {})
        self.assertEqual(resultado.veredicto, "CUBIERTO")
        self.assertEqual(resultado.mejor_unidad, "doc#a")

    def test_excluye_los_casos_fuera_de_alcance(self):
        """Sus palabras clave vienen del mensaje de rechazo, no del corpus.

        Medirlos por cobertura los daba como 'contaminados' porque frases como
        'base de datos' aparecen en cualquier corpus.
        """
        caso = self._caso(
            articulos_referencia=["NO_APLICA"],
            palabras_clave_esperadas=["base de datos"],
        )
        resultado = auditar_caso(caso, "una base de datos", self.UNIDADES, {})
        self.assertEqual(resultado.veredicto, "FUERA_DE_ALCANCE")

    def test_separa_los_pendientes_por_falta_de_documento(self):
        """Una brecha de adquisicion documental no es un fallo de recuperacion.

        Mezclarlas oculta cual de los dos problemas hay que resolver: conseguir el
        documento o mejorar la busqueda.
        """
        caso = self._caso(estado="pendiente_documento", palabras_clave_esperadas=["maximo"])
        resultado = auditar_caso(caso, "el maximo es 25", self.UNIDADES, {})
        self.assertEqual(resultado.veredicto, "PENDIENTE_DOCUMENTO")

    def test_propaga_el_dominio(self):
        caso = self._caso(dominio="movilidad", palabras_clave_esperadas=["maximo"])
        self.assertEqual(auditar_caso(caso, "", self.UNIDADES, {}).dominio, "movilidad")
        # Los sets v1 no declaran dominio y deben seguir funcionando.
        self.assertEqual(auditar_caso(self._caso(), "", self.UNIDADES, {}).dominio, "general")

    def test_reporta_los_documentos_citados_ausentes(self):
        caso = self._caso(articulos_referencia=["Art. 5 - Reglamento Academico UNSAAC"])
        resultado = auditar_caso(caso, "", self.UNIDADES, {"glosario.json": "Glosario General"})
        self.assertEqual(resultado.documentos_ausentes, ["Art. 5 - Reglamento Academico UNSAAC"])
        self.assertEqual(resultado.articulos_citados, ["Art. 5 - Reglamento Academico UNSAAC"])


if __name__ == "__main__":
    unittest.main()
