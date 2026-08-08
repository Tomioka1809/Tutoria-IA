"""Regresion: la politica de CORS depende del entorno y nunca combina '*' con credenciales.

Origen: main.py registraba CORSMiddleware con allow_origins=["*"] y allow_credentials=True.
Esa combinacion es invalida por especificacion y habilita peticiones autenticadas desde
cualquier origen. En produccion la lista de origenes pasa a ser explicita y obligatoria.
"""

import unittest

from app.infrastructure.config.config import (
    parse_cors_origins,
    resolve_cors_origins,
)


class TestCorsOriginParsing(unittest.TestCase):
    def test_splits_trims_and_strips_trailing_slash(self):
        self.assertEqual(
            parse_cors_origins(" https://a.pe , https://b.pe/ "),
            ["https://a.pe", "https://b.pe"],
        )

    def test_ignores_empty_entries_and_deduplicates(self):
        self.assertEqual(
            parse_cors_origins("https://a.pe,,https://a.pe/,"),
            ["https://a.pe"],
        )

    def test_none_and_blank_yield_empty_list(self):
        self.assertEqual(parse_cors_origins(None), [])
        self.assertEqual(parse_cors_origins("   "), [])


class TestCorsOriginResolution(unittest.TestCase):
    def test_development_without_config_falls_back_to_wildcard(self):
        self.assertEqual(resolve_cors_origins("development", ""), ["*"])
        self.assertEqual(resolve_cors_origins("test", None), ["*"])

    def test_development_honours_explicit_origins(self):
        self.assertEqual(
            resolve_cors_origins("development", "http://localhost:8081"),
            ["http://localhost:8081"],
        )

    def test_production_requires_explicit_origins(self):
        for raw in ("", None, "   "):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    resolve_cors_origins("production", raw)

    def test_production_rejects_wildcard(self):
        with self.assertRaises(ValueError):
            resolve_cors_origins("production", "*")
        with self.assertRaises(ValueError):
            resolve_cors_origins("production", "https://tutoria.unsaac.edu.pe,*")

    def test_production_accepts_explicit_list(self):
        self.assertEqual(
            resolve_cors_origins("production", "https://tutoria.unsaac.edu.pe"),
            ["https://tutoria.unsaac.edu.pe"],
        )


class TestCredentialsNeverPairWithWildcard(unittest.TestCase):
    """Replica la regla aplicada en main.py: allow_credentials = '*' not in origins."""

    def _allow_credentials(self, app_env, raw_origins):
        origins = resolve_cors_origins(app_env, raw_origins)
        return origins, "*" not in origins

    def test_wildcard_disables_credentials(self):
        origins, credentials = self._allow_credentials("development", "")
        self.assertEqual(origins, ["*"])
        self.assertFalse(
            credentials,
            "'*' con allow_credentials=True es la combinacion que se estaba corrigiendo",
        )

    def test_explicit_origins_enable_credentials(self):
        origins, credentials = self._allow_credentials(
            "production", "https://tutoria.unsaac.edu.pe"
        )
        self.assertEqual(origins, ["https://tutoria.unsaac.edu.pe"])
        self.assertTrue(credentials)


class TestRuntimeSecurityIncludesCors(unittest.TestCase):
    def test_production_without_cors_fails_at_startup(self):
        """validate_runtime_security debe abortar el arranque, no servir con comodin."""
        import os
        from unittest.mock import patch
        from app.infrastructure.config.config import validate_runtime_security

        env = {
            "APP_ENV": "production",
            "SECRET_KEY": "x" * 48,
            "CORS_ALLOWED_ORIGINS": "",
        }
        with patch.dict(os.environ, env, clear=False):
            with self.assertRaises(ValueError):
                validate_runtime_security()


if __name__ == "__main__":
    unittest.main()
