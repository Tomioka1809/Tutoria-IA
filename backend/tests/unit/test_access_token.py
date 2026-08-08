"""El token de acceso real: caducidad correcta y base de tiempo con zona.

``create_access_token`` calculaba el ``exp`` con ``datetime.utcnow()``, deprecado
desde Python 3.12: devuelve un datetime **naive** que aparenta ser UTC. Es la misma
clase de dato que produjo el TypeError al comparar la expiracion de los codigos de
recuperacion contra una columna ``timestamptz``.

La funcion no tenia pruebas: la suite ejercitaba un doble que devuelve
``f"fake_token_for_{subject}"``, asi que nada cubria la caducidad de verdad. Cambiar
la base de tiempo del ``exp`` sin verificarlo es como se desloguea a todo el mundo,
o peor, como se emiten tokens que no caducan cuando deberian.
"""

import unittest
from datetime import datetime, timedelta, timezone

from jose import jwt

from app.infrastructure.config.config import settings
from app.infrastructure.security.security import create_access_token


def _decodificar(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


class TestTokenDeAcceso(unittest.TestCase):
    def test_el_sujeto_viaja_como_texto(self):
        payload = _decodificar(create_access_token(42))
        self.assertEqual(payload["sub"], "42")

    def test_caduca_segun_la_configuracion(self):
        antes = datetime.now(timezone.utc)
        payload = _decodificar(create_access_token("7"))

        expira = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        esperado = antes + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        # Margen de 60 s: cubre el tiempo de ejecucion sin dejar pasar un error de
        # zona horaria, que desplazaria la caducidad horas enteras.
        self.assertLess(abs((expira - esperado).total_seconds()), 60)

    def test_el_exp_no_esta_desplazado_por_zona_horaria(self):
        """Un utcnow() naive interpretado como local corre el exp varias horas."""
        payload = _decodificar(create_access_token("7"))
        expira = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

        self.assertGreater(
            expira,
            datetime.now(timezone.utc),
            "El token nace vencido: la base de tiempo del exp está desplazada.",
        )

    def test_respeta_un_expires_delta_explicito(self):
        antes = datetime.now(timezone.utc)
        payload = _decodificar(create_access_token("7", expires_delta=timedelta(minutes=5)))

        expira = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        self.assertLess(abs((expira - (antes + timedelta(minutes=5))).total_seconds()), 60)

    def test_un_token_ya_vencido_no_se_acepta(self):
        token = create_access_token("7", expires_delta=timedelta(minutes=-1))

        with self.assertRaises(jwt.ExpiredSignatureError):
            _decodificar(token)

    def test_un_token_firmado_con_otra_clave_no_se_acepta(self):
        ajeno = jwt.encode(
            {"sub": "7", "exp": datetime.now(timezone.utc) + timedelta(minutes=60)},
            "otra-clave-completamente-distinta",
            algorithm=settings.ALGORITHM,
        )

        with self.assertRaises(jwt.JWTError):
            _decodificar(ajeno)


if __name__ == "__main__":
    unittest.main()
