import unittest
import os
import ast
import inspect
from datetime import datetime, timedelta

from app.application.use_cases.auth_use_cases import AuthUseCase, reset_tokens_cache
from app.application.ports.repository_ports import UserRepositoryPort
from app.application.ports.security_port import (
    PasswordHasherPort,
    TokenServicePort,
    PasswordResetNotifierPort,
)
from app.domain.entities.user import UserCreate, UserUpdate, PasswordChange
from app.domain.entities.auth import LoginRequest
from app.domain.exceptions import (
    UserAlreadyExistsError,
    InvalidCredentialsError,
    AccountInactiveError,
    UserNotFoundError,
    PasswordMismatchError,
    InvalidTokenError,
    PasswordValidationError,
    PasswordUpdateError,
)


class FakeDbUser:
    def __init__(self, id: int, email: str, password_hash: str, role: str = "estudiante", is_active: bool = True, full_name: str = "Test User"):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.is_active = is_active
        self.full_name = full_name
        self.student_code = "123456"
        self.tutor_code = None
        self.phone_number = "999999999"
        self.expertise_areas = None
        self.office_location = None
        self.current_semester = 5
        self.academic_status = "Regular"


class FakeUserRepository(UserRepositoryPort):
    def __init__(self):
        self.users_by_email = {}
        self.users_by_id = {}
        self.counter = 1
        self.should_fail_update_password = False

    async def get_by_email(self, email: str):
        return self.users_by_email.get(email.lower())

    async def get_by_id(self, user_id: int):
        return self.users_by_id.get(user_id)

    async def create(self, user_in: UserCreate, hashed_password: str, is_active: bool = True):
        user = FakeDbUser(
            id=self.counter,
            email=user_in.email,
            password_hash=hashed_password,
            role=user_in.role,
            is_active=is_active,
            full_name=user_in.full_name,
        )
        self.counter += 1
        self.users_by_email[user_in.email.lower()] = user
        self.users_by_id[user.id] = user
        return user

    async def update(self, user_id: int, user_in: UserUpdate):
        user = self.users_by_id.get(user_id)
        if not user:
            return None
        if user_in.full_name is not None:
            user.full_name = user_in.full_name
        if user_in.email is not None:
            user.email = user_in.email
        return user

    async def update_password(self, user_id: int, new_password_hash: str) -> bool:
        if self.should_fail_update_password:
            return False
        user = self.users_by_id.get(user_id)
        if not user:
            return False
        user.password_hash = new_password_hash
        return True


class FakePasswordHasher(PasswordHasherPort):
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return f"hashed_{plain_password}" == hashed_password

    def get_password_hash(self, password: str) -> str:
        return f"hashed_{password}"


class FakeTokenService(TokenServicePort):
    def __init__(self):
        self.created_tokens = []

    def create_access_token(self, subject: str) -> str:
        token = f"fake_token_for_{subject}"
        self.created_tokens.append(token)
        return token


class FakePasswordResetNotifier(PasswordResetNotifierPort):
    def __init__(self):
        self.sent_notifications = []

    def send_reset_code(self, email: str, code: str, expires_at: datetime) -> None:
        self.sent_notifications.append({
            "email": email,
            "code": code,
            "expires_at": expires_at
        })


class TestAuthApplication(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        reset_tokens_cache.clear()
        self.user_repo = FakeUserRepository()
        self.password_hasher = FakePasswordHasher()
        self.token_service = FakeTokenService()
        self.notifier = FakePasswordResetNotifier()
        self.auth_use_case = AuthUseCase(
            user_repo=self.user_repo,
            password_hasher=self.password_hasher,
            token_service=self.token_service,
            notifier=self.notifier,
        )

    def tearDown(self):
        reset_tokens_cache.clear()

    async def test_register_user_success(self):
        user_in = UserCreate(
            email="estudiante@unsaac.edu.pe",
            password="secretpassword",
            full_name="Juan Perez",
            role="estudiante"
        )
        user_out = await self.auth_use_case.register_user(user_in, is_active=True)
        self.assertEqual(user_out.email, "estudiante@unsaac.edu.pe")
        self.assertEqual(user_out.full_name, "Juan Perez")
        self.assertTrue(user_out.is_active)

    async def test_register_user_already_exists(self):
        user_in = UserCreate(
            email="duplicado@unsaac.edu.pe",
            password="secretpassword",
            full_name="Juan Perez",
            role="estudiante"
        )
        await self.auth_use_case.register_user(user_in)

        with self.assertRaises(UserAlreadyExistsError):
            await self.auth_use_case.register_user(user_in)

    async def test_authenticate_user_success(self):
        user_in = UserCreate(
            email="login@unsaac.edu.pe",
            password="mypassword",
            full_name="Maria Gomez",
            role="estudiante"
        )
        await self.auth_use_case.register_user(user_in, is_active=True)

        login_in = LoginRequest(username="login@unsaac.edu.pe", password="mypassword")
        token_out = await self.auth_use_case.authenticate_user(login_in)
        self.assertEqual(token_out.token_type, "bearer")
        self.assertEqual(token_out.access_token, "fake_token_for_1")

    async def test_authenticate_user_wrong_password(self):
        user_in = UserCreate(
            email="login_fail@unsaac.edu.pe",
            password="correctpassword",
            full_name="Maria Gomez",
            role="estudiante"
        )
        await self.auth_use_case.register_user(user_in, is_active=True)

        login_in = LoginRequest(username="login_fail@unsaac.edu.pe", password="wrongpassword")
        with self.assertRaises(InvalidCredentialsError):
            await self.auth_use_case.authenticate_user(login_in)

    async def test_authenticate_user_not_found(self):
        login_in = LoginRequest(username="inexistente@unsaac.edu.pe", password="password")
        with self.assertRaises(InvalidCredentialsError):
            await self.auth_use_case.authenticate_user(login_in)

    async def test_authenticate_user_inactive_account(self):
        user_in = UserCreate(
            email="tutor@unsaac.edu.pe",
            password="tutorpassword",
            full_name="Ing. Carlos",
            role="tutor"
        )
        await self.auth_use_case.register_user(user_in, is_active=False)

        login_in = LoginRequest(username="tutor@unsaac.edu.pe", password="tutorpassword")
        with self.assertRaises(AccountInactiveError):
            await self.auth_use_case.authenticate_user(login_in)

    async def test_update_profile_success(self):
        user_in = UserCreate(
            email="perfil@unsaac.edu.pe",
            password="password",
            full_name="Nombre Viejo",
            role="estudiante"
        )
        created = await self.auth_use_case.register_user(user_in)

        update_in = UserUpdate(full_name="Nombre Nuevo")
        updated = await self.auth_use_case.update_profile(created.id, update_in)
        self.assertEqual(updated.full_name, "Nombre Nuevo")

    async def test_update_profile_user_not_found(self):
        update_in = UserUpdate(full_name="Nombre Nuevo")
        with self.assertRaises(UserNotFoundError):
            await self.auth_use_case.update_profile(999, update_in)

    async def test_change_password_success(self):
        user_in = UserCreate(
            email="pass@unsaac.edu.pe",
            password="oldpassword",
            full_name="Usuario Pass",
            role="estudiante"
        )
        created = await self.auth_use_case.register_user(user_in)

        change_in = PasswordChange(current_password="oldpassword", new_password="newpassword123")
        res = await self.auth_use_case.change_password(created.id, change_in)
        self.assertTrue(res)

        login_in = LoginRequest(username="pass@unsaac.edu.pe", password="newpassword123")
        token_out = await self.auth_use_case.authenticate_user(login_in)
        self.assertIsNotNone(token_out.access_token)

    async def test_change_password_wrong_current(self):
        user_in = UserCreate(
            email="pass_wrong@unsaac.edu.pe",
            password="oldpassword",
            full_name="Usuario Pass",
            role="estudiante"
        )
        created = await self.auth_use_case.register_user(user_in)

        change_in = PasswordChange(current_password="wrongpassword", new_password="newpassword123")
        with self.assertRaises(PasswordMismatchError):
            await self.auth_use_case.change_password(created.id, change_in)

    async def test_change_password_repository_failure(self):
        user_in = UserCreate(
            email="pass_repo_fail@unsaac.edu.pe",
            password="oldpassword",
            full_name="Usuario Pass",
            role="estudiante"
        )
        created = await self.auth_use_case.register_user(user_in)
        self.user_repo.should_fail_update_password = True

        change_in = PasswordChange(current_password="oldpassword", new_password="newpassword123")
        with self.assertRaises(PasswordUpdateError):
            await self.auth_use_case.change_password(created.id, change_in)

    async def test_generate_reset_token_calls_notifier_and_6_digits(self):
        user_in = UserCreate(
            email="reset@unsaac.edu.pe",
            password="password",
            full_name="Usuario Reset",
            role="estudiante"
        )
        await self.auth_use_case.register_user(user_in)

        await self.auth_use_case.generate_reset_token("reset@unsaac.edu.pe")

        self.assertEqual(len(self.notifier.sent_notifications), 1)
        notification = self.notifier.sent_notifications[0]
        self.assertEqual(notification["email"], "reset@unsaac.edu.pe")
        code = notification["code"]
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())

    async def test_generate_reset_token_user_not_found(self):
        with self.assertRaises(UserNotFoundError):
            await self.auth_use_case.generate_reset_token("nonexistent@unsaac.edu.pe")

    async def test_reset_password_unrequested_code(self):
        with self.assertRaises(InvalidTokenError):
            await self.auth_use_case.reset_password_with_token("unrequested@unsaac.edu.pe", "123456", "newpass123")

    async def test_reset_password_incorrect_code(self):
        user_in = UserCreate(
            email="wrong_token@unsaac.edu.pe",
            password="password",
            full_name="Usuario Token",
            role="estudiante"
        )
        await self.auth_use_case.register_user(user_in)
        await self.auth_use_case.generate_reset_token("wrong_token@unsaac.edu.pe")

        with self.assertRaises(InvalidTokenError):
            await self.auth_use_case.reset_password_with_token("wrong_token@unsaac.edu.pe", "000000", "newpass123")

    async def test_reset_password_expired_code(self):
        user_in = UserCreate(
            email="expired@unsaac.edu.pe",
            password="password",
            full_name="Usuario Expired",
            role="estudiante"
        )
        await self.auth_use_case.register_user(user_in)
        await self.auth_use_case.generate_reset_token("expired@unsaac.edu.pe")

        # Manually expire the token in cache
        reset_tokens_cache["expired@unsaac.edu.pe"]["expires"] = datetime.now() - timedelta(minutes=1)

        with self.assertRaises(InvalidTokenError):
            await self.auth_use_case.reset_password_with_token("expired@unsaac.edu.pe", self.notifier.sent_notifications[0]["code"], "newpass123")

    async def test_reset_password_short_new_password(self):
        user_in = UserCreate(
            email="shortpass@unsaac.edu.pe",
            password="password",
            full_name="Usuario Short",
            role="estudiante"
        )
        await self.auth_use_case.register_user(user_in)
        await self.auth_use_case.generate_reset_token("shortpass@unsaac.edu.pe")
        code = self.notifier.sent_notifications[0]["code"]

        with self.assertRaises(PasswordValidationError):
            await self.auth_use_case.reset_password_with_token("shortpass@unsaac.edu.pe", code, "12345")

        # Verify token is still retained in cache after password validation error
        self.assertIn("shortpass@unsaac.edu.pe", reset_tokens_cache)

    async def test_reset_password_success_updates_hash_and_removes_token(self):
        user_in = UserCreate(
            email="reset_success@unsaac.edu.pe",
            password="oldpassword",
            full_name="Usuario Reset OK",
            role="estudiante"
        )
        await self.auth_use_case.register_user(user_in)
        await self.auth_use_case.generate_reset_token("reset_success@unsaac.edu.pe")
        code = self.notifier.sent_notifications[0]["code"]

        res = await self.auth_use_case.reset_password_with_token("reset_success@unsaac.edu.pe", code, "newsecurepass")
        self.assertTrue(res)
        self.assertNotIn("reset_success@unsaac.edu.pe", reset_tokens_cache)

        # Login with new password
        login_in = LoginRequest(username="reset_success@unsaac.edu.pe", password="newsecurepass")
        token_out = await self.auth_use_case.authenticate_user(login_in)
        self.assertIsNotNone(token_out.access_token)

    async def test_reset_password_repository_failure_retains_token(self):
        user_in = UserCreate(
            email="reset_fail_repo@unsaac.edu.pe",
            password="oldpassword",
            full_name="Usuario Reset Fail",
            role="estudiante"
        )
        await self.auth_use_case.register_user(user_in)
        await self.auth_use_case.generate_reset_token("reset_fail_repo@unsaac.edu.pe")
        code = self.notifier.sent_notifications[0]["code"]

        self.user_repo.should_fail_update_password = True

        with self.assertRaises(PasswordUpdateError):
            await self.auth_use_case.reset_password_with_token("reset_fail_repo@unsaac.edu.pe", code, "newsecurepass")

        # Verify token was NOT deleted from cache upon repository update failure
        self.assertIn("reset_fail_repo@unsaac.edu.pe", reset_tokens_cache)

    def test_architectural_decoupling_and_legacy_removal(self):
        use_case_path = os.path.join(
            os.path.dirname(__file__),
            "../../app/application/use_cases/auth_use_cases.py"
        )
        with open(use_case_path, "r", encoding="utf-8") as f:
            code_text = f.read()

        # AST Inspection to ensure clean imports in auth_use_cases.py
        parsed = ast.parse(code_text)
        imported_modules = []
        for node in ast.walk(parsed):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_modules.append(node.module)

        forbidden_prefixes = ["fastapi", "sqlalchemy", "app.infrastructure", "random"]
        for mod in imported_modules:
            for prefix in forbidden_prefixes:
                self.assertFalse(
                    mod.startswith(prefix),
                    f"Forbidden import '{mod}' found in auth_use_cases.py"
                )

        # Check no print() in auth_use_cases.py
        self.assertNotIn("print(", code_text, "AuthUseCase must not contain print() statements")

        # Verify legacy auth_service.py does NOT exist
        legacy_path = os.path.join(
            os.path.dirname(__file__),
            "../../app/application/use_cases/auth_service.py"
        )
        self.assertFalse(
            os.path.exists(legacy_path),
            "Legacy auth_service.py file must be removed and not re-introduced"
        )


if __name__ == "__main__":
    unittest.main()
