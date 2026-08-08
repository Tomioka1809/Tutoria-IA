"""Regresion: listados de administracion acotados y asignacion validada.

- ``GET /admin/users`` devolvia el padron completo (~577 filas) y hacia **una consulta
  por tutor** dentro de un bucle de Python. ``GET /admin/corpus`` devolvia los ~1370
  fragmentos con su texto entero. Ambos, en cada carga de pantalla de una app movil.

- ``POST /admin/assignments`` insertaba sin comprobar nada: ids inexistentes, un
  "tutor" que era estudiante o admin, y por encima de ``max_capacity``, que
  ``bulk_transfer`` y ``execute_sorteo`` si respetan. Era la unica de las tres vias
  de asignacion sin control de cupo.
"""

import ast
import inspect
import unittest

from fastapi.routing import APIRoute

from app.infrastructure.api.v1 import api as api_module
from app.infrastructure.api.v1.endpoints import admin


def _ruta(path: str, metodo: str) -> APIRoute:
    for route in api_module.api_router.routes:
        if isinstance(route, APIRoute) and route.path == path and metodo in route.methods:
            return route
    raise AssertionError(f"No se encontro {metodo} {path}")


class TestPaginacionDeListados(unittest.TestCase):
    def _params(self, path: str) -> dict:
        ruta = _ruta(path, "GET")
        return {p.name: p for p in ruta.dependant.query_params}

    def test_users_acepta_limit_y_offset(self):
        params = self._params("/admin/users")
        self.assertIn("limit", params)
        self.assertIn("offset", params)

    def test_corpus_acepta_limit_y_offset(self):
        params = self._params("/admin/corpus")
        self.assertIn("limit", params)
        self.assertIn("offset", params)

    def test_el_tamano_de_pagina_tiene_tope(self):
        """Sin tope superior, ?limit=999999 reproduce la consulta sin acotar."""
        self.assertLessEqual(admin.DEFAULT_PAGE_SIZE, admin.MAX_PAGE_SIZE)
        self.assertLessEqual(admin.MAX_PAGE_SIZE, 1000)

        for path in ("/admin/users", "/admin/corpus"):
            # Las restricciones viven en field_info.metadata como objetos de
            # annotated-types: [Ge(ge=1), Le(le=500)].
            restricciones = {
                type(m).__name__.lower(): getattr(m, type(m).__name__.lower())
                for m in self._params(path)["limit"].field_info.metadata
            }
            self.assertEqual(
                restricciones.get("le"),
                admin.MAX_PAGE_SIZE,
                f"{path} no aplica el tope maximo de pagina",
            )
            self.assertEqual(restricciones.get("ge"), 1)


class TestConsultaAgrupadaDeCargas(unittest.TestCase):
    def test_get_all_users_no_consulta_dentro_de_un_bucle(self):
        """Regresion del N+1: una consulta por tutor dentro del for."""
        arbol = ast.parse(inspect.getsource(admin.get_all_users))

        for nodo in ast.walk(arbol):
            if not isinstance(nodo, (ast.For, ast.AsyncFor)):
                continue
            for interno in ast.walk(nodo):
                if isinstance(interno, ast.Await):
                    self.fail(
                        "get_all_users volvio a ejecutar una consulta dentro del bucle: "
                        "usar una sola agrupada, como hace execute_sorteo."
                    )

    def test_get_all_users_agrupa_las_cargas(self):
        fuente = inspect.getsource(admin.get_all_users)
        self.assertIn("group_by", fuente)


class TestValidacionDeAsignacion(unittest.TestCase):
    """La validacion se comprueba sobre la fuente porque el endpoint necesita una

    sesion real de base de datos; el comportamiento se verifico contra la API viva.
    """

    def setUp(self):
        self.fuente = inspect.getsource(admin.create_assignment)

    def test_valida_que_el_estudiante_exista_y_sea_estudiante(self):
        self.assertIn('role != "estudiante"', self.fuente)

    def test_valida_que_el_tutor_exista_y_sea_tutor(self):
        self.assertIn('role != "tutor"', self.fuente)

    def test_respeta_la_capacidad_maxima(self):
        self.assertIn("max_capacity", self.fuente)
        self.assertIn(
            "func.count",
            self.fuente,
            "Sin contar la carga actual no se puede respetar el cupo.",
        )

    def test_las_tres_vias_de_asignacion_miran_la_capacidad(self):
        """create_assignment era la unica de las tres que no lo hacia."""
        for fn in (admin.create_assignment, admin.bulk_transfer, admin.execute_sorteo):
            self.assertIn(
                "max_capacity",
                inspect.getsource(fn),
                f"{fn.__name__} no comprueba max_capacity",
            )


if __name__ == "__main__":
    unittest.main()
