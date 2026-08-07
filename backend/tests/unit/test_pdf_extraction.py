"""Regresiones del extractor de articulado desde PDF (Fase 2)."""
import json
import os
import tempfile
import unittest

from app.application.dtos.corpus_dtos import MAX_CARACTERES_TEXTO, TipoDocumento
from scripts.audit_corpus_coverage import unidades_semanticas
from scripts.convert_corpus import tiene_articulado
from scripts.extract_pdf_corpus import (
    construir_documento,
    extraer_articulos,
    partir_articulo,
)

CFG = {
    "documento": "Reglamento de prueba UNSAAC",
    "tipo": TipoDocumento.REGLAMENTO,
    "resolucion": "Resolución Nro. CU-0001-2017-UNSAAC",
    "anio": 2017,
    "base_legal": [],
}


class TestExtraccionArticulos(unittest.TestCase):
    def test_reconoce_las_dos_notaciones_de_articulo(self):
        """El reglamento de tutoria usa 'Art. N', el resto 'Artículo N'."""
        texto = (
            "Art. 1° Naturaleza\n   Cuerpo del primer articulo con texto suficiente.\n\n"
            "Artículo 2° Alcance\n   Cuerpo del segundo articulo con texto suficiente.\n"
        )
        arts = extraer_articulos(texto)
        self.assertEqual([a["numero"] for a in arts], [1, 2])
        self.assertEqual([a["titulo"] for a in arts], ["Naturaleza", "Alcance"])

    def test_un_capitulo_no_se_anida_bajo_otro_capitulo(self):
        """Regresion: sin TITULO previo daba 'Capítulo I > Capítulo III'."""
        texto = (
            "Capítulo I\nNormas generales\n"
            "Art. 1° Uno\n   Cuerpo del articulo uno con longitud suficiente.\n\n"
            "Capítulo III\n"
            "Art. 5° Cinco\n   Cuerpo del articulo cinco con longitud suficiente.\n"
        )
        arts = extraer_articulos(texto)
        self.assertEqual(arts[0]["jerarquia"], ["Capítulo I"])
        self.assertEqual(arts[-1]["jerarquia"], ["Capítulo III"])

    def test_un_titulo_reinicia_el_capitulo(self):
        texto = (
            "TÍTULO I\nCapítulo I\n"
            "Art. 1° Uno\n   Cuerpo suficientemente largo para el articulo uno.\n\n"
            "TÍTULO II\n"
            "Art. 2° Dos\n   Cuerpo suficientemente largo para el articulo dos.\n"
        )
        arts = extraer_articulos(texto)
        self.assertEqual(arts[0]["jerarquia"], ["Título I", "Capítulo I"])
        self.assertEqual(arts[1]["jerarquia"], ["Título II"])

    def test_descarta_numeros_de_pagina_sueltos(self):
        texto = (
            "Art. 1° Uno\n   Primera parte del cuerpo del articulo.\n"
            "12\n"
            "   Segunda parte del cuerpo del articulo.\n"
        )
        arts = extraer_articulos(texto)
        self.assertNotIn("12", arts[0]["cuerpo"].split())

    def test_descarta_el_encabezado_y_el_pie_que_se_repiten_por_pagina(self):
        """Regresion: el pie del ROF 2024 quedaba dentro del cuerpo del articulo.

        El Art. 104 terminaba con "OFICINA DE PLANEAMIENTO... Pagina 54", que
        entraba al embedding como si fuera texto normativo.
        """
        paginas = []
        for n in range(1, 7):
            paginas.append(
                "REGLAMENTO DE ORGANIZACION Y FUNCIONES DE LA UNSAAC\n"
                f"Art. {n}° Titulo del articulo {n}\n"
                f"   Cuerpo del articulo {n} con longitud mas que suficiente para indexar.\n"
                f"OFICINA DE PLANEAMIENTO Y PRESUPUESTO/UNIDAD DE MODERNIZACION    Página {n}"
            )
        arts = extraer_articulos("\f".join(paginas))

        self.assertEqual([a["numero"] for a in arts], [1, 2, 3, 4, 5, 6])
        for art in arts:
            self.assertNotIn("OFICINA DE PLANEAMIENTO", art["cuerpo"])
            self.assertNotIn("Página", art["cuerpo"])
            self.assertNotIn("REGLAMENTO DE ORGANIZACION", art["cuerpo"])
            self.assertIn("Cuerpo del articulo", art["cuerpo"])

    def test_no_borra_una_linea_repetida_que_es_contenido(self):
        """El filtro mira la posicion, no solo la frecuencia.

        En texto justificado una linea corta como "Universidad." se repite
        muchas veces y es contenido: filtrar por frecuencia la borraria.
        """
        paginas = []
        for n in range(1, 7):
            paginas.append(
                "ENCABEZADO QUE SE REPITE\n"
                f"Art. {n}° Titulo del articulo {n}\n"
                f"   Apertura del articulo {n} con longitud mas que suficiente.\n"
                "   Universidad.\n"
                f"   Cierre del articulo {n} con texto adicional para no quedar corto.\n"
                f"Página {n}"
            )
        arts = extraer_articulos("\f".join(paginas))

        self.assertEqual(len(arts), 6)
        for art in arts:
            self.assertIn("Universidad.", art["cuerpo"])
            self.assertNotIn("ENCABEZADO QUE SE REPITE", art["cuerpo"])
            self.assertNotIn("Página", art["cuerpo"])

    def test_parte_un_parrafo_unico_mas_largo_que_el_limite(self):
        """Regresion: un parrafo sin saltos generaba un fragmento de 2703 chars."""
        parrafo = " ".join(f"Oracion numero {i} del parrafo largo." for i in range(120))
        piezas = partir_articulo(parrafo, 500)
        self.assertGreater(len(piezas), 1)
        for p in piezas:
            self.assertLessEqual(len(p), 500)

    def test_parte_una_fila_de_tabla_sin_un_solo_punto(self):
        """Regresion: el Art. 27 de subvenciones daba un fragmento de 3033 chars.

        Las tablas del OCR llegan como una fila unica sin puntos finales, asi
        que el corte por oraciones no tenia donde cortar y devolvia el bloque
        entero, diluyendo el embedding entre todos los conceptos de la tabla.
        """
        fila = " | ".join(f"CONCEPTO {i} de la tabla con su descripcion" for i in range(40))
        piezas = partir_articulo(fila, 500)
        self.assertGreater(len(piezas), 1)
        for p in piezas:
            self.assertLessEqual(len(p), 500)

    def test_parte_una_celda_unica_mas_larga_que_el_presupuesto(self):
        """Sin corte por palabra, una sola celda enorme seguia excediendo."""
        celda = " ".join(f"palabra{i}" for i in range(400))
        piezas = partir_articulo(celda, 300)
        self.assertGreater(len(piezas), 1)
        for p in piezas:
            self.assertLessEqual(len(p), 300)


class TestConstruccionDeFragmentos(unittest.TestCase):
    def test_asigna_el_numero_de_articulo_a_cada_fragmento(self):
        arts = [{"numero": 14, "titulo": "Asignación", "jerarquia": [], "cuerpo": "x" * 300}]
        doc = construir_documento("reg", CFG, arts)
        self.assertTrue(all(f.articulo == "Art. 14" for f in doc.fragmentos))
        self.assertEqual(doc.fragmentos_sin_articulo, [])

    def test_el_encabezado_incluye_documento_y_articulo(self):
        """Sin esto el fragmento no es citable fuera de su contexto."""
        arts = [{"numero": 9, "titulo": "Matrícula", "jerarquia": ["Título I"], "cuerpo": "y" * 300}]
        doc = construir_documento("reg", CFG, arts)
        encabezado = doc.fragmentos[0].texto.split("\n")[0]
        self.assertIn("Reglamento de prueba UNSAAC", encabezado)
        self.assertIn("Título I", encabezado)
        self.assertIn("Art. 9 - Matrícula", encabezado)

    def test_fusiona_un_articulo_demasiado_corto_con_el_siguiente(self):
        """'Art. 2 Base Legal: Ley 30220' solo no es recuperable."""
        arts = [
            {"numero": 2, "titulo": "Base Legal", "jerarquia": [], "cuerpo": "Ley 30220"},
            {"numero": 3, "titulo": "Definición", "jerarquia": [], "cuerpo": "z" * 300},
        ]
        doc = construir_documento("reg", CFG, arts)
        self.assertEqual(len(doc.fragmentos), 1)
        self.assertIn("Ley 30220", doc.fragmentos[0].texto)

    def test_los_fragmentos_divisibles_respetan_el_limite(self):
        arts = [{
            "numero": 1, "titulo": "Largo", "jerarquia": [],
            "cuerpo": "\n".join("Parrafo con contenido normativo extenso." * 8 for _ in range(9)),
        }]
        doc = construir_documento("reg", CFG, arts)
        self.assertGreater(len(doc.fragmentos), 1)
        for f in doc.fragmentos:
            self.assertLessEqual(len(f.texto), MAX_CARACTERES_TEXTO)


class TestProteccionDelArticulado(unittest.TestCase):
    def test_detecta_un_documento_ya_extraido(self):
        """Reconvertir desde el corpus heredado pisaria el articulado real."""
        with tempfile.TemporaryDirectory() as d:
            con = os.path.join(d, "con.json")
            sin = os.path.join(d, "sin.json")
            with open(con, "w", encoding="utf-8") as fh:
                json.dump({"fragmentos": [{"id": "a", "articulo": "Art. 1"}]}, fh)
            with open(sin, "w", encoding="utf-8") as fh:
                json.dump({"fragmentos": [{"id": "a", "articulo": None}]}, fh)

            self.assertTrue(tiene_articulado(con))
            self.assertFalse(tiene_articulado(sin))
            self.assertFalse(tiene_articulado(os.path.join(d, "no-existe.json")))


class TestAuditoriaSobreCorpusEstructurado(unittest.TestCase):
    def test_usa_el_fragmento_como_unidad_en_el_formato_nuevo(self):
        """En el corpus estructurado el fragmento YA es la unidad de recuperacion."""
        datos = {
            "procedencia": {"documento": "Doc"},
            "fragmentos": [
                {"id": "doc#art-1", "texto": "primero"},
                {"id": "doc#art-2", "texto": "segundo"},
            ],
        }
        unidades = unidades_semanticas(datos, "doc.json")
        self.assertEqual([u[0] for u in unidades], ["doc#art-1", "doc#art-2"])

    def test_mantiene_el_formato_heredado(self):
        datos = {"seccion_a": {"x": 1}, "seccion_b": "texto"}
        unidades = unidades_semanticas(datos, "viejo.json")
        self.assertEqual([u[0] for u in unidades], ["viejo.json#seccion_a", "viejo.json#seccion_b"])


if __name__ == "__main__":
    unittest.main()
