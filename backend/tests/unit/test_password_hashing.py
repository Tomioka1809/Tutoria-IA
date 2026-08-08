"""Regresion: el hash de contraseñas funciona en cualquier version de Python soportada.

Origen: ``requirements.txt`` declaraba ``passlib`` pero no ``bcrypt``, su unica
dependencia real para el esquema configurado. El proyecto funcionaba igual porque
passlib caia en silencio al backend ``os_crypt``, que usa el modulo ``crypt`` de la
biblioteca estandar. Ese modulo fue eliminado en Python 3.13 (PEP 594), asi que el
registro y el login se rompian con::

    passlib.exc.MissingBackendError: bcrypt: no backends available

Solo se sostenia porque el Dockerfile fija python:3.12-slim. Fuera de Docker ya
fallaba. Al eliminar passlib desaparece la seleccion automatica de backend: si falta
la dependencia el import falla de entrada, en vez de degradarse a algo que caduca.

Los hashes de LEGADO_* los genero el stack anterior (passlib 1.7.4 + os_crypt sobre
Python 3.12). Estan fijados aqui para probar que las contraseñas ya guardadas en la
base siguen validando: el cambio no necesita migracion.
"""

import unittest

from app.infrastructure.security.security import get_password_hash, verify_password


LEGADO_CLAVE = "clave-legado-123"
LEGADO_HASH = "$2b$12$8XJ4CVGQzygL75JTHdg0DudfoiSwCjauX79VvIzY0QD5s6uW.4SdO"

# bcrypt solo considera los primeros 72 bytes. El stack viejo truncaba en silencio,
# asi que este hash corresponde a 100 caracteres guardados como si fueran 72.
LEGADO_CLAVE_LARGA = "x" * 100
LEGADO_HASH_LARGO = "$2b$12$NcbCHLKIZEFr3YBIGGlaCuGs2fvjhEqBt0SWnTmbm/mowficg4mYO"


class TestHashDeContrasenas(unittest.TestCase):
    def test_produce_un_hash_bcrypt(self):
        hashed = get_password_hash("una-clave-cualquiera")
        self.assertTrue(
            hashed.startswith("$2b$"),
            f"Se esperaba un hash bcrypt moderno ($2b$), se obtuvo: {hashed[:8]!r}",
        )

    def test_la_clave_correcta_valida_y_la_incorrecta_no(self):
        hashed = get_password_hash("clave-correcta")
        self.assertTrue(verify_password("clave-correcta", hashed))
        self.assertFalse(verify_password("clave-incorrecta", hashed))

    def test_dos_hashes_de_la_misma_clave_son_distintos(self):
        """Cada hash lleva su propia sal; si coinciden, la sal no se esta generando."""
        self.assertNotEqual(
            get_password_hash("misma-clave"),
            get_password_hash("misma-clave"),
        )

    def test_valida_los_hashes_guardados_por_el_stack_anterior(self):
        self.assertTrue(
            verify_password(LEGADO_CLAVE, LEGADO_HASH),
            "Un hash creado por passlib/os_crypt dejo de validar: las cuentas "
            "existentes no podrian iniciar sesion sin migrar la base.",
        )
        self.assertFalse(verify_password("clave-equivocada", LEGADO_HASH))

    def test_las_claves_de_mas_de_72_bytes_no_revientan(self):
        """bcrypt rechaza mas de 72 bytes; el stack viejo truncaba sin avisar.

        Se conserva ese truncado para que las cuentas creadas con claves largas
        sigan entrando. Sin esto, ``bcrypt`` lanza ValueError y el login devuelve 500.
        """
        hashed = get_password_hash(LEGADO_CLAVE_LARGA)
        self.assertTrue(verify_password(LEGADO_CLAVE_LARGA, hashed))
        self.assertTrue(
            verify_password(LEGADO_CLAVE_LARGA, LEGADO_HASH_LARGO),
            "Cambio el criterio de truncado: las claves largas ya guardadas "
            "dejarian de validar.",
        )

    def test_soporta_claves_con_caracteres_no_ascii(self):
        clave = "contraseña-ñandú-€-🎓"
        self.assertTrue(verify_password(clave, get_password_hash(clave)))

    def test_un_hash_invalido_no_propaga_la_excepcion(self):
        """Un registro corrupto en la base debe ser un login fallido, no un 500."""
        self.assertFalse(verify_password("cualquiera", "no-es-un-hash-bcrypt"))
        self.assertFalse(verify_password("cualquiera", ""))


if __name__ == "__main__":
    unittest.main()
