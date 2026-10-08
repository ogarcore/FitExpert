"""
test_exercise_info.py
=====================
Catálogo de ejercicios (exercise_info.py):

  - Todos los ejercicios de training.EXERCISE_LIBRARY tienen ficha.
  - Los slugs son estables, únicos y sin colisiones.
  - resolve_exercise_image devuelve None (sin fallar) si no hay imagen
    y la ruta correcta cuando el archivo existe.
  - get_ficha nunca lanza excepción y siempre devuelve una estructura.
"""

import exercise_info as EI
from training import EXERCISE_LIBRARY

REQUIRED_KEYS = (
    "nombre", "categoria", "grupo_muscular", "secundarios", "descripcion",
    "pasos", "errores", "consejos", "respiracion", "tempo",
    "regresion", "progresion", "lesiones", "equipamiento", "imagen",
)


def test_todos_los_ejercicios_tienen_ficha():
    for entry in EXERCISE_LIBRARY.values():
        slug = EI.slugify(entry["nombre"])
        assert slug in EI.CATALOG, f"Falta ficha para {entry['nombre']}"
        ficha = EI.CATALOG[slug]
        for key in REQUIRED_KEYS:
            assert key in ficha, f"{slug}: falta la clave {key}"
        assert ficha["nombre"] == entry["nombre"]


def test_slugs_estables_y_sin_colisiones():
    slugs = [EI.slugify(e["nombre"]) for e in EXERCISE_LIBRARY.values()]
    assert len(slugs) == len(set(slugs)), "Colisión de slugs entre ejercicios"
    # Estabilidad: mismos inputs → mismo slug
    for e in EXERCISE_LIBRARY.values():
        assert EI.slugify(e["nombre"]) == EI.slugify(e["nombre"])
        assert EI.slugify(e["nombre"]) == EI.slugify(e["nombre"].strip())


def test_slugify_normaliza():
    assert EI.slugify("Sentadilla Búlgara") == "sentadilla_bulgara"
    assert EI.slugify("Press de banca con barra") == "press_de_banca_con_barra"
    assert EI.slugify("Nordic curl (curl nórdico)") == "nordic_curl_curl_nordico"


def test_resolve_exercise_image_none_sin_archivo(tmp_path, monkeypatch):
    monkeypatch.setattr(EI, "ASSETS_DIR", tmp_path)
    assert EI.resolve_exercise_image("dead_bug") is None


def test_resolve_exercise_image_devuelve_ruta(tmp_path, monkeypatch):
    monkeypatch.setattr(EI, "ASSETS_DIR", tmp_path)
    img = tmp_path / "dead_bug.png"
    img.write_bytes(b"\x89PNG fake")
    assert EI.resolve_exercise_image("dead_bug") == img


def test_resolve_exercise_image_extensiones(tmp_path, monkeypatch):
    monkeypatch.setattr(EI, "ASSETS_DIR", tmp_path)
    img = tmp_path / "plancha.webp"
    img.write_bytes(b"fake")
    assert EI.resolve_exercise_image("plancha") == img


def test_get_ficha_desconocido_no_falla():
    ficha = EI.get_ficha("ejercicio_que_no_existe")
    assert ficha["nombre"] == "ejercicio_que_no_existe"
    assert ficha["pasos"] == []
    assert ficha["lesiones"] == []


def test_get_ficha_por_nombre_y_slug():
    entry = next(iter(EXERCISE_LIBRARY.values()))
    a = EI.get_ficha(entry["nombre"])
    b = EI.get_ficha(EI.slugify(entry["nombre"]))
    assert a is b
