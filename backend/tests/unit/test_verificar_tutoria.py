"""Pruebas del resumen de `docker compose ps` del verificador.

El detalle de F6-001 se guarda en reporte_verificacion.json, que esta
versionado. Antes se guardaba la tabla de texto completa, con el uptime de cada
contenedor, asi que el archivo cambiaba en cada corrida aunque el estado de los
servicios fuera identico. Estas pruebas fijan que el resumen dependa solo del
estado y sea estable.
"""
import json

from tests.verificar_tutoria import Verifier


UNA_LINEA_BACKEND = {
    "Service": "backend",
    "State": "running",
    "Health": "",
    "Status": "Up About an hour",
    "RunningFor": "4 days ago",
    "ID": "51195b96f5f9",
}

UNA_LINEA_DB = {
    "Service": "db",
    "State": "running",
    "Health": "healthy",
    "Status": "Up About an hour (healthy)",
    "RunningFor": "4 days ago",
    "ID": "f7f5e679d2f3",
}


def _json_lines(*registros: dict) -> str:
    return "\n".join(json.dumps(registro) for registro in registros)


def test_resume_json_lines():
    """Compose v5 emite un objeto por linea."""
    salida = _json_lines(UNA_LINEA_BACKEND, UNA_LINEA_DB)

    assert Verifier.parse_compose_ps(salida) == [
        "backend: running",
        "db: running (healthy)",
    ]


def test_resume_array_json():
    """Otras versiones emiten un unico array."""
    salida = json.dumps([UNA_LINEA_BACKEND, UNA_LINEA_DB])

    assert Verifier.parse_compose_ps(salida) == [
        "backend: running",
        "db: running (healthy)",
    ]


def test_resume_objeto_suelto():
    """Con un solo servicio, algunas versiones no envuelven en array."""
    assert Verifier.parse_compose_ps(json.dumps(UNA_LINEA_BACKEND)) == [
        "backend: running",
    ]


def test_descarta_los_campos_que_cambian_en_cada_corrida():
    """Ni uptime ni ids: son los que ensuciaban el diff del reporte."""
    resumen = Verifier.parse_compose_ps(_json_lines(UNA_LINEA_BACKEND, UNA_LINEA_DB))
    plano = " ".join(resumen)

    assert "Up About an hour" not in plano
    assert "4 days ago" not in plano
    assert "51195b96f5f9" not in plano


def test_el_orden_no_depende_del_de_compose():
    """Compose no garantiza el orden y el reporte se versiona."""
    directo = Verifier.parse_compose_ps(_json_lines(UNA_LINEA_BACKEND, UNA_LINEA_DB))
    invertido = Verifier.parse_compose_ps(_json_lines(UNA_LINEA_DB, UNA_LINEA_BACKEND))

    assert directo == invertido


def test_dos_corridas_del_mismo_estado_dan_el_mismo_resumen():
    """La razon de ser del cambio: mismo estado -> mismo texto."""
    primera = dict(UNA_LINEA_DB, Status="Up 53 minutes (healthy)")
    segunda = dict(UNA_LINEA_DB, Status="Up 59 minutes (healthy)")

    assert Verifier.parse_compose_ps(json.dumps(primera)) == Verifier.parse_compose_ps(
        json.dumps(segunda)
    )


def test_sin_servicios_devuelve_lista_vacia():
    """Vacio no es lo mismo que ilegible: quien llama responde WARN, no FAIL."""
    assert Verifier.parse_compose_ps("") == []
    assert Verifier.parse_compose_ps("   \n  ") == []


def test_salida_ilegible_devuelve_none():
    """None hace que quien llama caiga a la tabla de texto.

    Es la diferencia entre "no se pudo leer" y "no hay servicios": dar por
    caidos unos contenedores que estan arriba seria peor que el ruido.
    """
    assert Verifier.parse_compose_ps("no soy json") is None
    assert Verifier.parse_compose_ps('{"Service": "db"}\nbasura') is None


def test_registro_sin_nombre_devuelve_none():
    """Sin Service ni Name no hay resumen posible; se prefiere el fallback."""
    assert Verifier.parse_compose_ps(json.dumps({"State": "running"})) is None


def test_usa_name_si_falta_service():
    """Versiones viejas de compose no traen el campo Service."""
    assert Verifier.parse_compose_ps(
        json.dumps({"Name": "tutoria_db", "State": "running"})
    ) == ["tutoria_db: running"]


def test_estado_ausente_no_rompe():
    assert Verifier.parse_compose_ps(json.dumps({"Service": "db"})) == [
        "db: desconocido",
    ]


def test_lista_de_valores_no_dict_devuelve_none():
    assert Verifier.parse_compose_ps(json.dumps(["backend", "db"])) is None
