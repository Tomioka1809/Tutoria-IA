"""Regresion: PUT /auth/profile no puede cambiar el rol ni el estado de la cuenta.

Origen: el endpoint de autoservicio recibia el mismo DTO que podria usar un
administrador, con los campos ``role`` e ``is_active`` incluidos, y el repositorio
los escribia sin preguntar quien los mandaba. Un estudiante autenticado se volvia
administrador con un solo PUT:

    PUT /api/v1/auth/profile   {"role": "admin"}

El control de acceso posterior solo compara ``current_user.role``, asi que a partir
de ahi el panel de administracion completo quedaba abierto.

La defensa es estructural y no un filtro en el endpoint: el DTO de autoservicio no
declara esos campos, de modo que no hay forma de que lleguen al repositorio. Estas
pruebas fijan las tres capas por separado porque el fallo original fue que cada una
confiaba en que otra validaba.
"""

import unittest

from fastapi.routing import APIRoute

from app.domain.entities.user import UserSelfUpdate
from app.infrastructure.api.v1.api import api_router
from app.infrastructure.database.repositories.user_repository import UserRepository


# Campos que solo un administrador puede tocar, nunca el propio usuario sobre si mismo.
CAMPOS_PRIVILEGIADOS = ("role", "is_active")


class FakeProfile:
    def __init__(self):
        self.full_name = "Nombre Viejo"
        self.student_code = "000000"
        self.phone_number = None
        self.current_semester = None
        self.academic_status = None


class FakeUser:
    def __init__(self):
        self.id = 1
        self.email = "estudiante@unsaac.edu.pe"
        self.role = "estudiante"
        self.is_active = True
        self.student_profile = FakeProfile()
        self.tutor_profile = None
        self.admin_profile = None


class FakeSession:
    def __init__(self):
        self.commits = 0

    async def commit(self):
        self.commits += 1


class RepositorioConUsuarioFijo(UserRepository):
    """Aisla ``update`` de la base de datos sin reimplementar su logica."""

    def __init__(self, db, user):
        super().__init__(db)
        self._user = user

    async def get_by_id(self, user_id: int):
        return self._user


class TestDtoDeAutoservicio(unittest.TestCase):
    def test_el_dto_no_declara_campos_privilegiados(self):
        declarados = [c for c in CAMPOS_PRIVILEGIADOS if c in UserSelfUpdate.model_fields]
        self.assertEqual(
            declarados,
            [],
            "UserSelfUpdate expone campos que solo un admin deberia poder cambiar: "
            f"{declarados}. Si hace falta editarlos, va por una ruta de admin con su "
            "propio DTO, no por /auth/profile.",
        )

    def test_los_campos_privilegiados_enviados_por_el_cliente_se_descartan(self):
        dto = UserSelfUpdate(
            **{"full_name": "Nombre Nuevo", "role": "admin", "is_active": False}
        )
        enviado = dto.model_dump(exclude_unset=True)

        self.assertEqual(enviado.get("full_name"), "Nombre Nuevo")
        for campo in CAMPOS_PRIVILEGIADOS:
            self.assertNotIn(
                campo,
                enviado,
                f"'{campo}' sobrevivio a la validacion del DTO y llegaria al repositorio.",
            )


class TestRutaDePerfil(unittest.TestCase):
    def _ruta_de_perfil(self) -> APIRoute:
        for route in api_router.routes:
            if isinstance(route, APIRoute) and route.path == "/auth/profile":
                return route
        self.fail("No se encontro la ruta /auth/profile en el router de la API.")

    def test_el_endpoint_recibe_el_dto_de_autoservicio(self):
        ruta = self._ruta_de_perfil()
        cuerpos = [p.field_info.annotation for p in ruta.dependant.body_params]
        self.assertIn(
            UserSelfUpdate,
            cuerpos,
            "PUT /auth/profile debe recibir UserSelfUpdate. Con un DTO que declare "
            f"role o is_active vuelve la escalacion de privilegios. Recibe: {cuerpos}",
        )


class TestRepositorio(unittest.IsolatedAsyncioTestCase):
    async def test_update_no_reescribe_rol_ni_estado(self):
        user = FakeUser()
        db = FakeSession()
        repo = RepositorioConUsuarioFijo(db, user)

        # Se fuerza el peor caso: un objeto que si trae los campos privilegiados,
        # para que la prueba falle si el repositorio vuelve a copiarlos a ciegas.
        class PayloadMalicioso:
            @staticmethod
            def model_dump(exclude_unset: bool = False):
                return {
                    "full_name": "Nombre Nuevo",
                    "role": "admin",
                    "is_active": False,
                }

        await repo.update(user.id, PayloadMalicioso())

        self.assertEqual(user.role, "estudiante", "El repositorio reescribio el rol.")
        self.assertTrue(user.is_active, "El repositorio reescribio is_active.")
        self.assertEqual(
            user.student_profile.full_name,
            "Nombre Nuevo",
            "El repositorio dejo de aplicar los campos que si son del usuario.",
        )


if __name__ == "__main__":
    unittest.main()
