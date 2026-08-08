"""Regresion: los cuatro fallos del flujo de recuperacion de contraseña.

1. **Enumeracion de cuentas.** ``/auth/forgot-password`` es publico y devolvia 404
   para un correo desconocido y 200 para uno registrado. Alcanzaba con probar
   correos para saber quien tiene cuenta.

2. **Intentos ilimitados.** El codigo es de seis digitos y vivia 15 minutos sin
   contador de fallos: se recorria el espacio entero dentro de la ventana.

3. **Codigos en el log.** El unico notificador escribe el codigo en el log del
   backend y se instanciaba sin mirar ``APP_ENV``.

4. **Tokens en memoria del proceso.** Vivian en un diccionario a nivel de modulo:
   se perdian al reiniciar, no se compartian entre workers, y sobre eso no se puede
   construir un limite de intentos que signifique algo.

Los cuatro se arreglan juntos porque comparten el mismo flujo: el limite de intentos
(2) necesita el almacen persistente (4), y la respuesta uniforme (1) solo sirve si el
codigo tampoco se filtra por otro lado (3).
"""

import logging
import unittest
from datetime import datetime, timedelta, timezone

from app.main import configure_logging

from app.application.ports.repository_ports import PasswordResetTokenRepositoryPort
from app.application.ports.security_port import (
    PasswordHasherPort,
    PasswordResetNotifierPort,
    TokenServicePort,
)
from app.application.use_cases.auth_use_cases import (
    AuthUseCase,
    MAX_RESET_ATTEMPTS,
    RESET_REQUEST_ACK,
)
from app.domain.entities.user import UserCreate
from app.domain.exceptions import InvalidTokenError
from app.infrastructure.config.config import validate_password_reset_notifier
from app.infrastructure.security.security_adapter import DevelopmentPasswordResetNotifier


class FakeDbUser:
    def __init__(self, id, email, password_hash):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.role = "estudiante"
        self.is_active = True
        self.full_name = "Usuario"
        self.student_code = "1"
        self.tutor_code = None
        self.phone_number = None
        self.expertise_areas = None
        self.office_location = None
        self.current_semester = None
        self.academic_status = None


class FakeUserRepository:
    def __init__(self):
        self.users = {}
        self.counter = 1

    async def get_by_email(self, email):
        return self.users.get(email.lower())

    async def get_by_id(self, user_id):
        return next((u for u in self.users.values() if u.id == user_id), None)

    async def create(self, user_in, hashed_password, is_active=True):
        user = FakeDbUser(self.counter, user_in.email, hashed_password)
        self.counter += 1
        self.users[user_in.email.lower()] = user
        return user

    async def update(self, user_id, user_in):
        return None

    async def update_password(self, user_id, new_password_hash):
        user = await self.get_by_id(user_id)
        user.password_hash = new_password_hash
        return True


class FakeRecord:
    def __init__(self, id, email, code_hash, expires_at):
        self.id = id
        self.email = email
        self.code_hash = code_hash
        self.expires_at = expires_at
        self.attempts = 0
        self.is_active = True


class FakeResetRepo(PasswordResetTokenRepositoryPort):
    def __init__(self):
        self.tokens = {}
        self.counter = 1

    async def replace_for_email(self, email, code_hash, expires_at):
        # El adaptador real guarda en una columna timestamptz y devuelve datetimes con
        # tzinfo. Si el doble aceptara naive seria mas permisivo que produccion, que es
        # justo como se colo un TypeError que las pruebas no vieron.
        assert expires_at.tzinfo is not None, "expires_at debe llevar zona horaria"
        for t in self.tokens.values():
            if t.email == email:
                t.is_active = False
        token = FakeRecord(self.counter, email, code_hash, expires_at)
        self.tokens[self.counter] = token
        self.counter += 1
        return token

    async def get_active(self, email):
        activos = [t for t in self.tokens.values() if t.email == email and t.is_active]
        return activos[-1] if activos else None

    async def register_failed_attempt(self, token_id):
        self.tokens[token_id].attempts += 1
        return self.tokens[token_id].attempts

    async def invalidate(self, token_id):
        self.tokens[token_id].is_active = False


class FakeHasher(PasswordHasherPort):
    def verify_password(self, plain, hashed):
        return f"hashed_{plain}" == hashed

    def get_password_hash(self, password):
        return f"hashed_{password}"


class FakeTokenService(TokenServicePort):
    def create_access_token(self, subject):
        return f"token_{subject}"


class FakeNotifier(PasswordResetNotifierPort):
    def __init__(self):
        self.sent = []

    def send_reset_code(self, email, code, expires_at):
        self.sent.append({"email": email, "code": code, "expires_at": expires_at})


class BaseResetTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.user_repo = FakeUserRepository()
        self.reset_repo = FakeResetRepo()
        self.notifier = FakeNotifier()
        self.use_case = AuthUseCase(
            user_repo=self.user_repo,
            password_hasher=FakeHasher(),
            token_service=FakeTokenService(),
            notifier=self.notifier,
            reset_token_repo=self.reset_repo,
        )

    async def _crear_usuario(self, email="alumno@unsaac.edu.pe"):
        await self.use_case.register_user(
            UserCreate(
                email=email, password="password", full_name="Alumno", role="estudiante"
            )
        )
        return email


class TestEnumeracionDeCuentas(BaseResetTest):
    async def test_pedir_codigo_para_cuenta_inexistente_no_lanza(self):
        """Antes lanzaba UserNotFoundError, que el handler convertia en 404."""
        await self.use_case.generate_reset_token("fantasma@unsaac.edu.pe")
        self.assertEqual(self.notifier.sent, [])

    async def test_la_cuenta_inexistente_no_deja_rastro_consultable(self):
        await self.use_case.generate_reset_token("fantasma@unsaac.edu.pe")
        self.assertIsNone(await self.reset_repo.get_active("fantasma@unsaac.edu.pe"))

    async def test_existente_e_inexistente_terminan_igual(self):
        """Ninguna de las dos ramas levanta excepcion: el endpoint responde lo mismo."""
        email = await self._crear_usuario()
        await self.use_case.generate_reset_token(email)
        await self.use_case.generate_reset_token("fantasma@unsaac.edu.pe")
        self.assertEqual(len(self.notifier.sent), 1)

    async def test_el_acuse_no_afirma_que_la_cuenta_existe(self):
        self.assertIn("si el correo corresponde", RESET_REQUEST_ACK.lower())

    async def test_codigo_inexistente_y_expirado_dan_el_mismo_mensaje(self):
        """Diferenciarlos volveria a decir si la cuenta pidio un reset."""
        email = await self._crear_usuario()

        with self.assertRaises(InvalidTokenError) as sin_pedido:
            await self.use_case.reset_password_with_token(
                "otro@unsaac.edu.pe", "123456", "clavenueva"
            )

        await self.use_case.generate_reset_token(email)
        registro = await self.reset_repo.get_active(email)
        registro.is_active = False

        with self.assertRaises(InvalidTokenError) as anulado:
            await self.use_case.reset_password_with_token(email, "123456", "clavenueva")

        self.assertEqual(str(sin_pedido.exception), str(anulado.exception))


class TestLimiteDeIntentos(BaseResetTest):
    async def test_el_codigo_se_anula_al_agotar_los_intentos(self):
        email = await self._crear_usuario()
        await self.use_case.generate_reset_token(email)
        codigo = self.notifier.sent[0]["code"]

        for _ in range(MAX_RESET_ATTEMPTS):
            with self.assertRaises(InvalidTokenError):
                await self.use_case.reset_password_with_token(
                    email, "000000", "clavenueva"
                )

        self.assertIsNone(
            await self.reset_repo.get_active(email),
            "Tras agotar los intentos el codigo debe quedar inservible.",
        )

    async def test_el_codigo_correcto_deja_de_servir_tras_agotar_intentos(self):
        """El limite no sirve de nada si el codigo bueno sigue entrando despues."""
        email = await self._crear_usuario()
        await self.use_case.generate_reset_token(email)
        codigo = self.notifier.sent[0]["code"]

        for _ in range(MAX_RESET_ATTEMPTS):
            with self.assertRaises(InvalidTokenError):
                await self.use_case.reset_password_with_token(
                    email, "000000", "clavenueva"
                )

        with self.assertRaises(InvalidTokenError):
            await self.use_case.reset_password_with_token(email, codigo, "clavenueva")

    async def test_un_fallo_aislado_no_invalida_el_codigo(self):
        """Equivocarse una vez no puede costar el codigo entero."""
        email = await self._crear_usuario()
        await self.use_case.generate_reset_token(email)
        codigo = self.notifier.sent[0]["code"]

        with self.assertRaises(InvalidTokenError):
            await self.use_case.reset_password_with_token(email, "000000", "clavenueva")

        self.assertTrue(
            await self.use_case.reset_password_with_token(email, codigo, "clavenueva")
        )

    async def test_pedir_un_codigo_nuevo_anula_el_anterior(self):
        """Si convivieran, cada pedido sumaria otra tanda de intentos sobre la cuenta."""
        email = await self._crear_usuario()
        await self.use_case.generate_reset_token(email)
        primero = self.notifier.sent[0]["code"]

        await self.use_case.generate_reset_token(email)

        with self.assertRaises(InvalidTokenError):
            await self.use_case.reset_password_with_token(email, primero, "clavenueva")


class TestAlmacenamientoDelCodigo(BaseResetTest):
    async def test_el_codigo_se_guarda_hasheado(self):
        email = await self._crear_usuario()
        await self.use_case.generate_reset_token(email)

        codigo = self.notifier.sent[0]["code"]
        registro = await self.reset_repo.get_active(email)
        self.assertNotEqual(
            registro.code_hash,
            codigo,
            "El codigo quedo guardado en claro: seis digitos se revierten al instante.",
        )

    async def test_el_estado_no_vive_en_el_modulo(self):
        """Regresion directa: habia un dict global que no sobrevivia al reinicio."""
        import app.application.use_cases.auth_use_cases as modulo

        self.assertFalse(
            hasattr(modulo, "reset_tokens_cache"),
            "Volvio el almacen en memoria del proceso: no se comparte entre workers.",
        )

    async def test_el_codigo_expirado_se_rechaza_y_se_anula(self):
        email = await self._crear_usuario()
        await self.use_case.generate_reset_token(email)
        codigo = self.notifier.sent[0]["code"]

        registro = await self.reset_repo.get_active(email)
        registro.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)

        with self.assertRaises(InvalidTokenError):
            await self.use_case.reset_password_with_token(email, codigo, "clavenueva")

        self.assertIsNone(await self.reset_repo.get_active(email))


class TestVisibilidadDelCodigoEnDesarrollo(unittest.TestCase):
    """El notificador de desarrollo solo sirve si su linea llega a la consola.

    Uvicorn deja el logger root sin handlers, asi que el arbol 'app.*' quedaba en
    WARNING y el logger.info con el codigo se descartaba: el codigo se generaba, se
    guardaba y no lo veia nadie, mientras el README y la pantalla del frontend decian
    "revise la consola del backend".
    """

    def setUp(self):
        self.app_logger = logging.getLogger("app")
        self.nivel_previo = self.app_logger.level
        self.handlers_previos = list(self.app_logger.handlers)

    def tearDown(self):
        self.app_logger.setLevel(self.nivel_previo)
        self.app_logger.handlers = self.handlers_previos

    def test_en_desarrollo_el_codigo_llega_al_log(self):
        configure_logging("development")

        notifier = DevelopmentPasswordResetNotifier(app_env="development")
        with self.assertLogs("app.infrastructure.security.security_adapter", level="INFO") as capturado:
            notifier.send_reset_code(
                email="alumno@unsaac.edu.pe",
                code="123456",
                expires_at=datetime.now(timezone.utc),
            )

        self.assertIn("123456", "\n".join(capturado.output))

    def test_en_desarrollo_los_info_de_la_app_estan_habilitados(self):
        configure_logging("development")
        self.assertTrue(logging.getLogger("app.cualquier.modulo").isEnabledFor(logging.INFO))

    def test_en_produccion_los_info_quedan_apagados(self):
        configure_logging("production")
        self.assertFalse(logging.getLogger("app.cualquier.modulo").isEnabledFor(logging.INFO))


class TestNotificadorEnProduccion(unittest.TestCase):
    def test_el_notificador_de_log_se_niega_a_construirse_en_produccion(self):
        with self.assertRaises(ValueError):
            DevelopmentPasswordResetNotifier(app_env="production")

    def test_el_notificador_de_log_sirve_en_desarrollo_y_pruebas(self):
        for env in ("development", "test"):
            self.assertIsNotNone(DevelopmentPasswordResetNotifier(app_env=env))

    def test_el_arranque_falla_en_produccion(self):
        """Igual que SECRET_KEY y CORS: el error salta al desplegar, no en el primer reset."""
        with self.assertRaises(ValueError):
            validate_password_reset_notifier("production")

    def test_el_arranque_no_falla_fuera_de_produccion(self):
        for env in ("development", "test"):
            validate_password_reset_notifier(env)


if __name__ == "__main__":
    unittest.main()
