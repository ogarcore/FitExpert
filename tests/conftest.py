"""
conftest.py
===========
Fixture compartidas para la suite de pruebas de FitExpert.

Aislamiento: cada test usa bases de datos temporales (auth y usuarios)
para nunca tocar los datos reales del proyecto.
"""
import sys
from pathlib import Path

import pytest

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

import auth
import database
from user_profile import (
    UserProfile, OBJECTIVES, OBJECTIVE_LABELS, ACTIVITY_LEVELS,
    ACTIVITY_LABELS, EXPERIENCE_LEVELS, TRAINING_PLACES, SEX_OPTIONS,
)
from inference_engine import InferenceEngine


@pytest.fixture()
def auth_db(tmp_path, monkeypatch):
    """Base de autenticación temporal aislada."""
    db_dir = tmp_path / "auth"
    db_dir.mkdir(exist_ok=True)
    target = db_dir / "auth_db.json"
    monkeypatch.setattr(auth, "AUTH_DB_PATH", target, raising=True)
    # Garantiza que no exista de una ejecución previa del mismo test
    if target.exists():
        target.unlink()
    return target


@pytest.fixture()
def data_db(tmp_path, monkeypatch):
    """Base de sesiones/usuarios temporal aislada."""
    db_dir = tmp_path / "data"
    db_dir.mkdir(exist_ok=True)
    target = db_dir / "usuarios.json"
    monkeypatch.setattr(database, "DB_PATH", target, raising=True)
    if target.exists():
        target.unlink()
    return target


def make_profile(**overrides) -> UserProfile:
    """Perfil sano por defecto (usuario adulto típico) con overrides."""
    base = dict(
        name="Test",
        age=30,
        sex="masculino",
        weight=75.0,
        height=175.0,
        activity_level="moderado",
        objective="mantenimiento",
        experience="intermedio",
        training_place="gimnasio",
        diet_type="omnivoro",
        meal_frequency=3,
    )
    base.update(overrides)
    return UserProfile(**base)


def run_profile(profile: UserProfile) -> InferenceEngine:
    """Ejecuta el motor completo y retorna el motor (perfil ya queda armado)."""
    engine = InferenceEngine()
    engine.run(profile)
    return engine


def conclusion_ids(profile: UserProfile) -> list[str]:
    return [c["id"] for c in profile.conclusions]


@pytest.fixture()
def make_profile_fixture():
    return make_profile


@pytest.fixture()
def run_fixture():
    return run_profile