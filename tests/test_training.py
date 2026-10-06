"""
test_training.py
================
Generador de entrenamiento (training.py) — seguridad biomecánica:

  - Matriz de lesiones: las 10 zonas de INJURY_OPTIONS deben excluir patrones
    de carga y sustituir con alternativas seguras (traza en 'alternativas_aplicadas')
  - FALLBACK_BASIC ante restricciones que agotaron el catálogo → sesión nunca vacía
  - Suspensión total (red flags o lesión aguda) → motivo_suspension + 0 días
  - Contrato: semana con dia/grupo/descanso/ejercicios, sesiones = días activos
"""

import pytest

from training import (INJURY_MATRIX, FALLBACK_BASIC, EXERCISE_LIBRARY,
                      generate_training_plan)
from conftest import make_profile


@pytest.mark.parametrize("zona", sorted(INJURY_MATRIX))
def test_injury_matrix_covers_all_ten_zones(zona):
    """Las 10 zonas declaradas en INJURY_OPTIONS tienen matriz con sustitución."""
    entry = INJURY_MATRIX[zona]
    assert entry.get("nombre")
    assert entry.get("ejercicios_clave"), zona          # claves contraindicadas
    assert entry.get("alternativas"), zona              # sustitutos seguros
    assert entry.get("consejo")
    assert entry.get("referencia_medica")
    # Las claves contraindicadas deben existir realmente en la librería
    for k in entry["ejercicios_clave"]:
        assert k in EXERCISE_LIBRARY, f"{zona}: clave {k} inexistente"
    # Las alternativas deben existir y NO estar contraindicadas ellas mismas
    for k in entry["alternativas"]:
        assert k in EXERCISE_LIBRARY, f"{zona}: alternativa {k} inexistente"
        assert k not in entry["ejercicios_clave"]


def test_injured_zone_never_in_plan():
    """Con una lesión de rodilla activa, ningún ejercicio prescrito puede
    ser un patrón contraindicado (ej.: sentadilla con carga pesada)."""
    p = make_profile(injuries=["rodilla"], injury_severity="moderada")
    result = generate_training_plan(p)
    forbidden_names = {EXERCISE_LIBRARY[k]["nombre"]
                       for k in INJURY_MATRIX["rodilla"]["ejercicios_clave"]}
    for day in result["semana"]:
        for (nombre, _serie, _musculo) in day["ejercicios"]:
            assert nombre not in forbidden_names, f"{nombre} contraindicado en más de rodilla"


def test_alternatives_applied_and_traced():
    """Rodilla + gimnasio activa alternativas y las expone en la traza."""
    p = make_profile(injuries=["rodilla"], injury_severity="moderada",
                     training_place="gimnasio", experience="intermedio",
                     objective="aumento_muscular")
    result = generate_training_plan(p)
    assert result["alternativas_aplicadas"], "debe haber sustituciones registradas"
    assert "rodilla" in [x.lower() for x in result["lesiones_consideradas"]]


def test_fallback_basic_for_high_restrictions():
    """Perfil con todas las lesiones y equipamiento nulo: el plan se genera
    igual y ninguna entrada queda con descanso=False y ejercicios vacíos.
    Los días sin opción segura se convierten en descanso con derivación."""
    all_zones = list(INJURY_MATRIX.keys())
    p = make_profile(injuries=all_zones, injury_severity="moderada",
                     training_place="casa", equipment=[], experience="principiante")
    result = generate_training_plan(p)
    for day in result["semana"]:
        if not day["descanso"]:
            assert day["ejercicios"], f"{day['dia']} vacía sin fallback"
            for (nombre, _s, _m) in day["ejercicios"]:
                assert nombre  # no puede existir un nombre vacío
    # Al haber bloqueado todas las zonas, debe existir al menos un día de
    # descanso por agotamiento seguro o todos los días cubiertos con fallback
    notas_conj = " ".join(d["nota"] for d in result["semana"])
    assert "descanso" in notas_conj.lower() or result["sesiones"]


def test_red_flag_suspends_plan():
    """Red flags → ausencia total de prescripción: motivo_suspension presente,
    cero sesiones, todos los días marcados descanso y derivación a médico."""
    p = make_profile(red_flags=["dolor_toracico"], objective="perdida_grasa")
    result = generate_training_plan(p)
    assert result["motivo_suspension"]
    assert result["sesiones"] == []
    assert all(d["descanso"] for d in result["semana"])
    assert "no entrenar" in result["nombre"].lower()
    assert "consulta" in result["notas"].lower()


def test_acute_injury_suspends_plan():
    p = make_profile(injuries=["hombro"], injury_severity="aguda")
    result = generate_training_plan(p)
    assert result["motivo_suspension"]
    assert any("aguda" in m for m in result["motivo_suspension"])
    assert all(d["descanso"] for d in result["semana"])


def test_healthy_plan_contract():
    """Contrato v3: semana con dia/grupo y día/grupo; sesiones solo los activos."""
    p = make_profile(experience="intermedio", objective="aumento_muscular")
    result = generate_training_plan(p)
    assert result["nombre"] and result["tipo"]
    assert len(result["semana"]) == 7
    for day in result["semana"]:
        assert set(("dia", "grupo", "descanso", "ejercicios",
                    "duracion", "descanso_entre_series", "nota")) <= set(day)
        if not day["descanso"]:
            assert day["ejercicios"]
    assert result["sesiones"] == [d for d in result["semana"] if not d["descanso"]]
    assert result["sesiones"], "un plan sano debe tener días de entrenamiento"


def test_casa_legacy_key_mapping():
    """El perfil consume 'bandas_elasticas' (equipamiento v3) y 'casa' como
    lugar: debe producirse un plan sin errores."""
    p = make_profile(training_place="casa", equipment=["bandas_elasticas"],
                     experience="principiante")
    result = generate_training_plan(p)
    assert result["nombre"]
    for day in result["semana"]:
        if not day["descanso"]:
            assert all(day["ejercicios"])  # nada vacío ni `None`


def test_cardio_recommendation_present():
    p = make_profile()
    result = generate_training_plan(p)
    assert isinstance(result["cardio_extra"], str) and result["cardio_extra"]


def test_days_count_label():
    p = make_profile(experience="principiante", objective="recomposicion")
    result = generate_training_plan(p)
    active = sum(1 for d in result["semana"] if not d["descanso"])
    assert f"{active} días" in result["dias"]