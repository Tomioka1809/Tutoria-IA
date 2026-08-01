"""Regresion: el sorteo respeta max_capacity y no consulta dentro del bucle.

Origen: la sesion se construye con autoflush=False, por lo que los db.add() del bucle
quedaban pendientes y el SELECT COUNT de cada iteracion devolvia siempre la carga previa
al sorteo. El limite max_capacity se superaba en silencio. Ademas ese COUNT se ejecutaba
una vez por cada intento estudiante x tutor (N+1).

FakeSession reproduce ese autoflush=False de forma deliberada: no expone los objetos
agregados a consultas posteriores, y falla si aparece cualquier consulta extra despues
de las tres iniciales (estudiantes, tutores, cargas).
"""

import unittest

import app.infrastructure.database.base  # noqa: F401  - registra los mappers ORM
from app.infrastructure.api.v1.endpoints.admin import execute_sorteo


class FakeProfile:
    def __init__(self, max_capacity: int):
        self.max_capacity = max_capacity


class FakeUser:
    def __init__(self, id: int, tutor_profile=None):
        self.id = id
        self.tutor_profile = tutor_profile


class ScalarResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return self

    def all(self):
        return list(self._items)


class RowResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return list(self._rows)


class FakeSession:
    """Sesion con autoflush=False: los add() pendientes no afectan consultas posteriores."""

    def __init__(self, students, tutors, loads):
        self._queued = [ScalarResult(students), ScalarResult(tutors), RowResult(loads)]
        self.added = []
        self.committed = False
        self.extra_queries = 0

    async def execute(self, statement):
        if self._queued:
            return self._queued.pop(0)
        self.extra_queries += 1
        raise AssertionError(
            "Consulta emitida dentro del bucle de asignacion: reintroduce el N+1 "
            "y vuelve a leer cargas obsoletas."
        )

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed = True


def loads_per_tutor(session):
    counts = {}
    for assignment in session.added:
        counts[assignment.tutor_id] = counts.get(assignment.tutor_id, 0) + 1
    return counts


class TestSorteoCapacity(unittest.IsolatedAsyncioTestCase):
    async def test_does_not_exceed_max_capacity_with_stale_counts(self):
        """3 tutores en 14/15 y 30 estudiantes: solo caben 3 asignaciones."""
        tutors = [FakeUser(i, FakeProfile(15)) for i in (1, 2, 3)]
        students = [FakeUser(100 + i) for i in range(30)]
        session = FakeSession(students, tutors, loads=[(1, 14), (2, 14), (3, 14)])

        result = await execute_sorteo(period="2026-I", db=session, _=FakeUser(999))

        final_loads = {t.id: 14 + loads_per_tutor(session).get(t.id, 0) for t in tutors}
        over_capacity = {tid: n for tid, n in final_loads.items() if n > 15}

        self.assertEqual(over_capacity, {}, f"Tutores por encima de max_capacity: {final_loads}")
        self.assertEqual(result["assigned"], 3)
        self.assertEqual(result["unassigned"], 27)

    async def test_reports_students_left_without_tutor(self):
        tutors = [FakeUser(1, FakeProfile(2))]
        students = [FakeUser(100 + i) for i in range(5)]
        session = FakeSession(students, tutors, loads=[])

        result = await execute_sorteo(period="2026-I", db=session, _=FakeUser(999))

        self.assertEqual(result["assigned"], 2)
        self.assertEqual(result["unassigned"], 3)
        self.assertIn("sin asignar", result["message"])

    async def test_no_queries_inside_assignment_loop(self):
        """Las cargas se leen una sola vez; FakeSession falla ante cualquier consulta extra."""
        tutors = [FakeUser(i, FakeProfile(15)) for i in (1, 2, 3)]
        students = [FakeUser(100 + i) for i in range(20)]
        session = FakeSession(students, tutors, loads=[])

        await execute_sorteo(period="2026-I", db=session, _=FakeUser(999))

        self.assertEqual(session.extra_queries, 0)

    async def test_distributes_round_robin_across_tutors(self):
        tutors = [FakeUser(i, FakeProfile(15)) for i in (1, 2, 3)]
        students = [FakeUser(100 + i) for i in range(9)]
        session = FakeSession(students, tutors, loads=[])

        result = await execute_sorteo(period="2026-I", db=session, _=FakeUser(999))

        self.assertEqual(result["assigned"], 9)
        self.assertEqual(loads_per_tutor(session), {1: 3, 2: 3, 3: 3})

    async def test_tutor_without_profile_uses_default_capacity(self):
        tutors = [FakeUser(1, tutor_profile=None)]
        students = [FakeUser(100 + i) for i in range(20)]
        session = FakeSession(students, tutors, loads=[])

        result = await execute_sorteo(period="2026-I", db=session, _=FakeUser(999))

        self.assertEqual(result["assigned"], 15, "El default documentado es 15")
        self.assertEqual(result["unassigned"], 5)

    async def test_commits_once_at_the_end(self):
        tutors = [FakeUser(1, FakeProfile(15))]
        students = [FakeUser(100)]
        session = FakeSession(students, tutors, loads=[])

        await execute_sorteo(period="2026-I", db=session, _=FakeUser(999))

        self.assertTrue(session.committed)


if __name__ == "__main__":
    unittest.main()
