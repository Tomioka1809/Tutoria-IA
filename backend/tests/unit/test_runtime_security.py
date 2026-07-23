import os
import asyncio
import pytest
from app.infrastructure.config.config import (
    validate_secret_key_for_environment,
    validate_environment_name,
    validate_runtime_security,
    DEFAULT_DEV_SECRET_KEY,
)
from app.infrastructure.database.session import (
    validate_database_password_for_environment,
    validate_database_security,
)
from app.main import app, lifespan

# Sample fictitious secure strings for testing
SECURE_PROD_SECRET_KEY = "fictitious_secure_prod_key_min32chars_ok"
SECURE_PROD_DB_PASS = "db_password_segura_2026"
EXTENSIVE_SECURE_DB_PASS = "Extensive_Super_Secure_DB_Password_2026!@#"


def test_1_development_accepts_secret_key_fallback():
    validate_secret_key_for_environment("development", DEFAULT_DEV_SECRET_KEY)


def test_2_test_accepts_secret_key_fallback():
    validate_secret_key_for_environment("test", DEFAULT_DEV_SECRET_KEY)


def test_3_production_rejects_secret_key_fallback():
    with pytest.raises((ValueError, RuntimeError)) as exc:
        validate_secret_key_for_environment("production", DEFAULT_DEV_SECRET_KEY)
    assert "predeterminada de desarrollo" in str(exc.value)


def test_4_production_rejects_empty_secret_key():
    with pytest.raises((ValueError, RuntimeError)) as exc:
        validate_secret_key_for_environment("production", "")
    assert "SECRET_KEY" in str(exc.value)


def test_5_production_rejects_short_secret_key():
    with pytest.raises((ValueError, RuntimeError)) as exc:
        validate_secret_key_for_environment("production", "short_key_under_32_chars")
    assert "32 caracteres" in str(exc.value)


def test_6_production_rejects_known_placeholders():
    placeholders = ["changeme", "change_me", "secret", "your_secret_key", "tu_clave_secreta_super_segura_aqui"]
    for ph in placeholders:
        with pytest.raises((ValueError, RuntimeError)) as exc:
            validate_secret_key_for_environment("production", ph)
        assert "placeholder" in str(exc.value).lower() or "predeterminada" in str(exc.value).lower()


def test_7_production_accepts_secure_secret_key():
    validate_secret_key_for_environment("production", SECURE_PROD_SECRET_KEY)


def test_8_environment_normalized_case_insensitively():
    assert validate_environment_name("  PRODUCTION  ") == "production"
    assert validate_environment_name("Development") == "development"
    assert validate_environment_name("  tEsT ") == "test"
    validate_secret_key_for_environment("  PRODUCTION  ", SECURE_PROD_SECRET_KEY)


def test_9_unknown_environment_rejected():
    with pytest.raises((ValueError, RuntimeError)) as exc:
        validate_environment_name("staging")
    assert "APP_ENV" in str(exc.value)


def test_10_development_accepts_db_password_postgres():
    validate_database_password_for_environment("development", "postgres")


def test_11_test_accepts_db_password_postgres():
    validate_database_password_for_environment("test", "postgres")


def test_12_production_rejects_db_password_postgres():
    with pytest.raises((ValueError, RuntimeError)) as exc:
        validate_database_password_for_environment("production", "postgres")
    assert "DB_PASSWORD" in str(exc.value)


def test_13_production_rejects_empty_db_password():
    with pytest.raises((ValueError, RuntimeError)) as exc:
        validate_database_password_for_environment("production", "")
    assert "DB_PASSWORD" in str(exc.value)


def test_14_production_rejects_db_password_placeholders():
    placeholders = [
        "postgres",
        "password",
        "change-me",
        "change me",
        "your_password_here",
        "changeme",
        "change_me",
    ]
    for ph in placeholders:
        with pytest.raises((ValueError, RuntimeError)) as exc:
            validate_database_password_for_environment("production", ph)
        assert "DB_PASSWORD" in str(exc.value)


def test_15_production_accepts_secure_db_passwords():
    validate_database_password_for_environment("production", SECURE_PROD_DB_PASS)
    validate_database_password_for_environment("production", EXTENSIVE_SECURE_DB_PASS)


def test_16_exception_messages_do_not_contain_secrets():
    secret_test = "tu_clave_secreta_super_segura_aqui"
    with pytest.raises((ValueError, RuntimeError)) as exc1:
        validate_secret_key_for_environment("production", secret_test)
    assert secret_test not in str(exc1.value)

    db_pass_test = "postgres"
    with pytest.raises((ValueError, RuntimeError)) as exc2:
        validate_database_password_for_environment("production", db_pass_test)
    assert db_pass_test not in str(exc2.value)


def test_17_main_py_integrates_lifespan_validations():
    async def run_lifespan():
        async with lifespan(app):
            pass

    asyncio.run(run_lifespan())


def test_18_wrapper_functions_use_real_configuration(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    validate_runtime_security()
    validate_database_security("development")

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", DEFAULT_DEV_SECRET_KEY)
    with pytest.raises((ValueError, RuntimeError)):
        validate_runtime_security()

    monkeypatch.setenv("DB_PASSWORD", "postgres")
    with pytest.raises((ValueError, RuntimeError)):
        validate_database_security("production")
