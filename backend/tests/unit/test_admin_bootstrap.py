"""El admin inicial existe al levantar el proyecto, y no se filtra a produccion.

``ensure_admin`` dependia de que el .env declarara ADMIN_EMAIL y ADMIN_PASSWORD, pero
``.env.example`` los traia vacios. Un clon recien levantado quedaba con el roster de
tutores y estudiantes sembrado y **sin ningun usuario que pudiera entrar al panel de
administracion**: el bootstrap imprimia un aviso y seguia de largo.

La contrapartida es que la contraseña por defecto vive en el repositorio, o sea que es
publica. Estas pruebas fijan las dos mitades: que exista sin configurar nada fuera de
produccion, y que produccion se niegue a arrancar con ella.
"""

import os
import unittest
from unittest.mock import patch

from app.infrastructure.config.config import (
    DEFAULT_ADMIN_EMAIL,
    DEFAULT_ADMIN_NAME,
    DEFAULT_ADMIN_PASSWORD,
    resolve_admin_bootstrap,
    validate_admin_password_for_environment,
    validate_runtime_security,
)


def _sin_variables_admin(**extra):
    """Entorno limpio: ninguna ADMIN_* heredada del .env de quien corre las pruebas."""
    entorno = {k: v for k, v in os.environ.items() if not k.startswith("ADMIN_")}
    entorno.update(extra)
    return patch.dict(os.environ, entorno, clear=True)


class TestAdminPorDefectoEnDesarrollo(unittest.TestCase):
    def test_sin_configurar_nada_hay_credenciales(self):
        """Regresion: el caso del clon recien hecho, con .env.example sin tocar."""
        for env in ("development", "test"):
            with self.subTest(env=env), _sin_variables_admin():
                credenciales = resolve_admin_bootstrap(env)

                self.assertIsNotNone(
                    credenciales,
                    "Sin admin no queda nadie que pueda entrar al panel.",
                )
                email, password, nombre = credenciales
                self.assertEqual(email, DEFAULT_ADMIN_EMAIL)
                self.assertEqual(password, DEFAULT_ADMIN_PASSWORD)
                self.assertEqual(nombre, DEFAULT_ADMIN_NAME)

    def test_el_correo_pedido_es_el_que_se_usa(self):
        self.assertEqual(DEFAULT_ADMIN_EMAIL, "admin@unsaac.edu.pe")
        self.assertEqual(DEFAULT_ADMIN_PASSWORD, "admin123")

    def test_el_env_gana_sobre_el_valor_por_defecto(self):
        with _sin_variables_admin(
            ADMIN_EMAIL="otro@unsaac.edu.pe",
            ADMIN_PASSWORD="una-clave-propia",
            ADMIN_NAME="Coordinación",
        ):
            self.assertEqual(
                resolve_admin_bootstrap("development"),
                ("otro@unsaac.edu.pe", "una-clave-propia", "Coordinación"),
            )

    def test_una_variable_vacia_cae_al_valor_por_defecto(self):
        with _sin_variables_admin(ADMIN_EMAIL="", ADMIN_PASSWORD="   "):
            email, password, _ = resolve_admin_bootstrap("development")

            self.assertEqual(email, DEFAULT_ADMIN_EMAIL)
            self.assertEqual(password, DEFAULT_ADMIN_PASSWORD)


class TestProduccionNoHeredaLaClavePublica(unittest.TestCase):
    def test_sin_variables_produccion_no_crea_admin_automatico(self):
        """Nada de valores por defecto alli: se crea a mano con create_superuser."""
        with _sin_variables_admin(APP_ENV="production"):
            self.assertIsNone(resolve_admin_bootstrap("production"))

    def test_la_clave_del_repositorio_es_rechazada_en_produccion(self):
        with self.assertRaises(ValueError) as ctx:
            validate_admin_password_for_environment("production", DEFAULT_ADMIN_PASSWORD)

        self.assertIn("repositorio", str(ctx.exception).lower())

    def test_otras_claves_conocidas_tambien_se_rechazan(self):
        for debil in ("admin", "password", "123456", "changeme", "ADMIN123"):
            with self.subTest(clave=debil), self.assertRaises(ValueError):
                validate_admin_password_for_environment("production", debil)

    def test_se_exige_una_longitud_minima_en_produccion(self):
        with self.assertRaises(ValueError):
            validate_admin_password_for_environment("production", "corta12345")

    def test_una_clave_fuerte_pasa(self):
        validate_admin_password_for_environment("production", "8Kd!wq2Zx#mL4vTn")

    def test_sin_clave_no_falla(self):
        """Sin ADMIN_PASSWORD no se crea ningun admin: es seguro, no un error."""
        validate_admin_password_for_environment("production", None)
        validate_admin_password_for_environment("production", "   ")

    def test_fuera_de_produccion_no_se_valida_nada(self):
        for env in ("development", "test"):
            validate_admin_password_for_environment(env, DEFAULT_ADMIN_PASSWORD)

    def test_resolve_falla_si_produccion_declara_la_clave_debil(self):
        with _sin_variables_admin(
            ADMIN_EMAIL="admin@unsaac.edu.pe", ADMIN_PASSWORD=DEFAULT_ADMIN_PASSWORD
        ):
            with self.assertRaises(ValueError):
                resolve_admin_bootstrap("production")

    def test_el_arranque_falla_en_produccion_con_la_clave_debil(self):
        """Igual que SECRET_KEY y CORS: el error salta al desplegar.

        Se comprueba el mensaje, no solo el tipo: ``validate_runtime_security``
        encadena varias validaciones y la del notificador se evalua antes, asi que
        un ``assertRaises(ValueError)`` a secas pasaria aunque la comprobacion del
        admin no existiera.
        """
        with _sin_variables_admin(
            APP_ENV="production",
            SECRET_KEY="una-clave-de-firma-suficientemente-larga-para-produccion",
            DB_PASSWORD="una-db-password-fuerte",
            CORS_ALLOWED_ORIGINS="https://tutoria.unsaac.edu.pe",
            ADMIN_PASSWORD=DEFAULT_ADMIN_PASSWORD,
        ):
            # Se neutraliza la validacion previa para aislar la que se esta probando.
            with patch(
                "app.infrastructure.config.config.validate_password_reset_notifier",
                return_value=None,
            ):
                with self.assertRaises(ValueError) as ctx:
                    validate_runtime_security()

        self.assertIn("ADMIN_PASSWORD", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
