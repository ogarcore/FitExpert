"""
test_database_pdf.py
====================
Persistencia (database.py) y exportación (pdf_exporter.py):

  - round-trip save_profile → get_user_history / get_last_session
  - db_stats expone ambos nombres de clave (gui/ui y main/doc)
  - base corrupta → backup .bak y arranque vacío (nunca excepción)
  - escalado de historial y progreso (delta de peso/calorías)
  - export_pdf genera un archivo PDF real completo con contenido esperado
"""

import json

import pytest

import database
import pdf_exporter
from user_profile import UserProfile
from inference_engine import InferenceEngine
from nutrition import generate_nutrition_plan
from training import generate_training_plan
from conftest import make_profile


def _run_full(profile: UserProfile):
    """Ejecuta motor + planes para alimentar el perfil antes de persistir."""
    InferenceEngine().run(profile)
    profile.nutrition_plan = generate_nutrition_plan(profile)
    profile.training_plan = generate_training_plan(profile)
    return profile


def test_round_trip_save_and_history(data_db):
    p = _run_full(make_profile())
    database.save_profile(p)
    history = database.get_user_history(p.user_id)
    assert len(history) == 1
    entry = history[0]
    assert entry["user_id"] == p.user_id
    assert entry["name"] == "Test"
    assert entry["age"] == 30
    assert entry["saved_at"]
    assert entry["objective"] == "mantenimiento"
    assert entry["sex"] == "masculino"
    assert entry["conclusions"]
    assert entry["explanations"]


def test_save_two_sessions_and_last(data_db):
    p1 = _run_full(make_profile())
    p2 = _run_full(make_profile(weight=80, objective="perdida_grasa"))
    database.save_profile(p1)
    database.save_profile(p2)
    history = database.get_user_history(p1.user_id)
    assert len(history) == 2
    last = database.get_last_session(p1.user_id)
    assert last["objective"] == "perdida_grasa"
    # Sin cruces entre usuarios distintos
    other = database.get_user_history("otro_usuario")
    assert other == []


def test_db_stats_dual_keys(data_db):
    database.save_profile(_run_full(make_profile(user_id="u1")))
    database.save_profile(_run_full(make_profile(user_id="u2",
                                                 objective="perdida_grasa")))
    stats = database.db_stats()
    # Dos usuarios distintos = 2 sesiones
    assert stats["total_sesiones"] == 2
    assert stats["total_consultas"] == 2
    assert stats["total_usuarios"] == 2
    assert stats["usuarios_unicos"] == 2
    assert stats["por_objetivo"]["mantenimiento"] == 1
    assert stats["por_objetivo"]["perdida_grasa"] == 1
    # Compatibilidad gui.py / ui.py
    for key in ("total_usuarios", "por_objetivo", "total_consultas"):
        assert key in stats


def test_progress_summary(data_db):
    p1 = _run_full(make_profile(weight=75, objective="perdida_grasa"))
    p2 = _run_full(make_profile(weight=72, objective="perdida_grasa"))
    database.save_profile(p1)
    database.save_profile(p2)
    summary = database.get_progress_summary(p1.user_id)
    assert summary["sesiones"] == 2
    assert summary["progreso_disponible"] is True
    assert summary["delta_peso_kg"] == -3.0
    assert summary["objetivo_inicial"] == "perdida_grasa"
    assert summary["objetivo_actual"] == "perdida_grasa"


def test_progress_empty(data_db):
    summary = database.get_progress_summary("nadie")
    assert summary["sesiones"] == 0
    assert summary["progreso_disponible"] is False


def test_corrupt_db_is_backed_up(data_db):
    data_db.write_text("{esto no es json", encoding="utf-8")
    # no debe lanzar
    assert database.list_users() == []
    bak = [x for x in data_db.parent.iterdir() if x.suffix == ".bak"]
    assert bak, "la base corrupta debe respaldarse como .bak (nunca perderse)"
    assert data_db.read_text(encoding="utf-8") == "{esto no es json"


def test_legacy_list_shape_migrated(data_db):
    """Bases antiguas con forma de lista se migran a {sessions:[...]}."""
    data_db.write_text('[{"user_id": "u1", "name": "Ana"}]', encoding="utf-8")
    hist = database.get_user_history("u1")
    assert hist and hist[0]["name"] == "Ana"
    assert database.list_users()[0]["name"] == "Ana"


def test_legacy_dict_values_shape_migrated(data_db):
    data_db.write_text('{"u1": {"user_id": "u1", "name": "Ana"}}', encoding="utf-8")
    assert database.get_user_history("u1")[0]["name"] == "Ana"


def test_save_creates_parent_dir(tmp_path):
    target = tmp_path / "deep" / "nested" / "usuarios.json"
    import database as db
    import auth
    import pytest
    # Necesitamos monkeypatch del módulo: usamos fixture data_db equivalente manual
    origin = db.DB_PATH
    try:
        db.DB_PATH = target
        p = make_profile()
        InferenceEngine().run(p)
        db.save_profile(p)
        assert target.exists()
        hist = db.get_user_history(p.user_id)
        assert hist
    finally:
        db.DB_PATH = origin


def test_export_pdf_creates_file(data_db, tmp_path):
    p = _run_full(make_profile())
    out = tmp_path / "informe.pdf"
    path = pdf_exporter.export_pdf(p, p.nutrition_plan, p.training_plan, str(out))
    assert path == str(out)
    assert out.exists() and out.stat().st_size > 0
    head = out.read_bytes()[:5]
    assert head == b"%PDF-", "debe ser un PDF real, no HTML ni vacío"


def test_export_pdf_with_suspended_plan(tmp_path):
    """El PDF debe generarse incluso con plan suspendido (sin sesiones)."""
    p = make_profile(red_flags=["mareo_desmayo"])
    InferenceEngine().run(p)
    p.training_plan = generate_training_plan(p)
    out = tmp_path / "suspendido.pdf"
    pdf_exporter.export_pdf(p, make_profile_nutrition_plan(), p.training_plan, str(out))
    assert out.exists() and out.stat().st_size > 0


def make_profile_nutrition_plan():
    from conftest import make_profile as _mp
    return generate_nutrition_plan(_mp())