"""Regresion: toda ruta de la API exige autenticacion salvo las declaradas publicas.

Origen: /quiz/generate quedo expuesta sin ninguna dependencia de autenticacion pese a
invocar a Gemini en cada peticion, lo que permitia agotar la cuota de la API sin token.
La lista blanca es explicita para que agregar una ruta publica sea una decision visible
en el diff y no un olvido.
"""

import unittest

from app.infrastructure.api.v1.api import api_router


AUTH_DEPENDENCIES = {
    "get_current_user",
    "get_current_active_tutor",
    "get_current_active_admin",
}

# Rutas que deben ser accesibles sin token: son las que permiten obtenerlo o recuperarlo.
PUBLIC_ROUTES = {
    ("POST", "/auth/login"),
    ("POST", "/auth/register"),
    ("POST", "/auth/forgot-password"),
    ("POST", "/auth/reset-password"),
    # Solo lectura, sin datos personales ni consumo de cuota externa.
    ("GET", "/quotes/random"),
}


def _route_dependency_names(route) -> set:
    return {dep.call.__name__ for dep in route.dependant.dependencies}


def _iter_routes():
    for route in api_router.routes:
        for method in route.methods:
            yield method, route.path, route


class TestEndpointAuthorization(unittest.TestCase):
    def test_every_route_requires_auth_unless_explicitly_public(self):
        unprotected = [
            f"{method} {path}"
            for method, path, route in _iter_routes()
            if (method, path) not in PUBLIC_ROUTES
            and not (_route_dependency_names(route) & AUTH_DEPENDENCIES)
        ]
        self.assertEqual(
            unprotected,
            [],
            "Rutas sin autenticacion que no estan en PUBLIC_ROUTES: "
            f"{unprotected}. Si la exposicion es intencional, agregarla a PUBLIC_ROUTES.",
        )

    def test_quiz_generate_requires_authentication(self):
        """Regresion directa: /quiz/generate consume cuota de Gemini por peticion."""
        matches = [
            route
            for method, path, route in _iter_routes()
            if method == "GET" and path == "/quiz/generate"
        ]
        self.assertEqual(len(matches), 1, "No se encontro GET /quiz/generate")
        self.assertTrue(
            _route_dependency_names(matches[0]) & AUTH_DEPENDENCIES,
            "GET /quiz/generate debe exigir autenticacion",
        )

    def test_public_allowlist_has_no_stale_entries(self):
        """Evita que la lista blanca conserve rutas que ya no existen."""
        declared = {(method, path) for method, path, _ in _iter_routes()}
        stale = sorted(PUBLIC_ROUTES - declared)
        self.assertEqual(stale, [], f"PUBLIC_ROUTES declara rutas inexistentes: {stale}")


if __name__ == "__main__":
    unittest.main()
