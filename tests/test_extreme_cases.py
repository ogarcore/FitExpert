"""
test_extreme_cases.py
=====================
20 casos extremos (auditoría de robustez): los perfiles más límite que un
usuario real (o un atacante de formulario) puede producir deben pasar por
validación → cálculos → motor → planes y exportación SIN excepción, con
conclusiones ordenadas por jerarquía y, cuando corresponde, derivación.

Cada caso verifica la propiedad clave del sistema: "nunca un Traceback".
"""

import math

import pytest

from validation import validate_evaluation
from user_profile import UserProfile
from inference_engine import InferenceEngine
from nutrition import generate_nutrition_plan
from training import generate_training_plan

MIN = 10
MAX = 100


BASE_EXTREME = dict(
    name="Caso extremo", age=30, sex="masculino", weight=75.0, height=175.0,
    objective="mantenimiento", activity_level="moderado", experience="intermedio",
    training_place="gimnasio", diet_type="omnivoro", meal_frequency=3,
    injuries=[], equipment=[], allergies=[], intolerances=[], preferences=[],
    red_flags=[], injury_severity="ninguna", balance_issues=False,
    notes="",
)


def run_extreme(data: dict):
    """Empuja un perfil extremo por la tubería completa sin que lance."""
    values, errores, advertencias = validate_evaluation({**BASE_EXTREME, **data})
    profile = UserProfile(**values)
    engine = InferenceEngine()
    engine.run(profile)
    return profile, errores, advertencias, engine


# 1–10 — Edades límite ─────────────────────────────────────────────

def test_caso_1_edad_10_minor():
    p, err, _w, _e = run_extreme(dict(age=10, weight=35, height=140))
    assert not err
    ids = [c["id"] for c in p.conclusions]
    assert "EDAD-01" in ids and "EDAD-02" in ids and "EDAD-03" in ids
    assert p.engine_errors == []


def test_caso_2_edad_12_minor():
    p, err, _w, _e = run_extreme(dict(age=12, weight=40, height=150))
    assert not err
    ids = [c["id"] for c in p.conclusions]
    assert "EDAD-03" in ids   # 10-13
    assert p.engine_errors == []


def test_caso_3_edad_16_minor():
    p, err, _w, _e = run_extreme(dict(age=16, weight=55, height=165))
    assert not err
    ids = [c["id"] for c in p.conclusions]
    assert "EDAD-04" in ids          # 14-17
    assert "EDAD-02" not in ids      # 16 ya no < 16
    assert p.engine_errors == []


def test_caso_4_edad_17_adolescente():
    p, err, _w, _e = run_extreme(dict(age=17, weight=60, height=170))
    assert not err
    ids = [c["id"] for c in p.conclusions]
    assert "EDAD-04" in ids
    assert "EDAD-02" not in ids   # >= 16 sin restricción de placas
    assert p.engine_errors == []


def test_caso_5_edad_18_mayoria():
    p, err, _w, _e = run_extreme(dict(age=18, weight=65, height=175))
    assert not err
    ids = [c["id"] for c in p.conclusions]
    assert "EDAD-01" not in ids and "EDAD-02" not in ids
    assert p.engine_errors == []


def test_caso_6_edad_59_limite_adulto():
    p, err, _w, _e = run_extreme(dict(age=59, weight=80, height=175))
    assert not err
    ids = [c["id"] for c in p.conclusions]
    assert "EDAD-MAY-01" not in ids    # senior es >= 60
    assert p.engine_errors == []


def test_caso_7_edad_60_senior():
    p, err, _w, _e = run_extreme(dict(age=60, weight=75, height=170))
    assert not err
    ids = [c["id"] for c in p.conclusions]
    assert "EDAD-MAY-01" in ids        # proteína 1.0-1.2 g/kg
    assert p.engine_errors == []


def test_caso_8_edad_74_no_75():
    p, err, _w, _e = run_extreme(dict(age=74, weight=70, height=165))
    assert not err
    ids = [c["id"] for c in p.conclusions]
    assert "EDAD-MAY-02" in ids        # >= 70 o balance → caídas
    assert "EDAD-MAY-03" not in ids    # solo >= 75
    assert p.engine_errors == []


def test_caso_9_edad_75_muy_mayor():
    p, err, _w, _e = run_extreme(dict(age=75, weight=68, height=160))
    assert not err
    ids = [c["id"] for c in p.conclusions]
    assert "EDAD-MAY-03" in ids        # >= 75 → volumen conservador
    assert p.engine_errors == []


def test_caso_10_edad_110_fuera_de_rango():
    _p, err, _w, _e = run_extreme(dict(age=110))
    assert "age" in err
    assert "máxima" in err["age"]


# 11–14 — Peso / estatura / IMC extremos ───────────────────────────

def test_caso_11_peso_20kg_estatura_250():
    _p, err, _w, _e = run_extreme(dict(weight=20, height=250))
    assert "weight" in err            # < WEIGHT_MIN (30)
    assert "mínimo" in err["weight"]


def test_caso_12_peso_400kg_estatura_100():
    _p, err, _w, _e = run_extreme(dict(weight=400, height=100))
    assert "weight" in err            # > WEIGHT_MAX
    assert "máximo" in err["weight"]


def test_caso_13_imc_bajo_extremo():
    p, err, _w, _e = run_extreme(dict(age=30, weight=40, height=175))
    assert not err
    ids = [c["id"] for c in p.conclusions]
    assert "NUT-07" in ids            # bajo peso: suprime déficit
    assert "NUT-01" not in ids
    # el plan de comida con suma mínima de calorías debe existir igualmente
    plan = generate_nutrition_plan(p)
    assert plan["calorias_objetivo"] > 0


def test_caso_14_imc_alto_extremo():
    p, err, _w, _e = run_extreme(dict(age=30, weight=130, height=165))
    assert not err
    ids = [c["id"] for c in p.conclusions]
    assert "NUT-08" in ids            # IMC >= 30
    assert "BIO-03" in ids            # IMC >= 40: bajo impacto
    rutina = generate_training_plan(p)
    assert rutina["nombre"]           # no suspendida: no hay red flags


# 15–16 — % grasa límite ───────────────────────────────────────────

def test_caso_15_body_fat_3pct():
    p, err, _w, _e = run_extreme(dict(age=30, sex="masculino",
                                      weight=75, height=175, body_fat_pct=3))
    assert not err
    assert p.engine_errors == []


def test_caso_16_body_fat_70pct():
    p, err, _w, _e = run_extreme(dict(age=30, sex="femenino",
                                      weight=75, height=175, body_fat_pct=70))
    assert not err
    ids = [c["id"] for c in p.conclusions]
    assert "COMP-01" in ids           # % grasa excesivo para el sexo (ACSM)
    comp = [c for c in p.conclusions if c["id"] == "COMP-01"][0]
    assert comp["severity"] == "media"
    assert p.engine_errors == []


# 17 — NaN / Inf ───────────────────────────────────────────────────

@pytest.mark.parametrize("valor", [math.nan, math.inf, -math.inf])
def test_caso_17_nan_inf(valor):
    _p, err, _w, _e = run_extreme(dict(weight=valor, height=valor,
                                       age=valor, body_fat_pct=valor))
    assert err, "NaN/Inf deben bloquearse en validación sin excepción"


# 18 — Perfil vacío (cero datos) ───────────────────────────────────

def test_caso_18_perfil_vacio_completo():
    """Un UserProfile() sin datos no debe romper ninguna capa."""
    profile = UserProfile()
    engine = InferenceEngine()
    engine.run(profile)                      # motor
    plan = generate_nutrition_plan(profile)  # nutrición
    assert plan["plan"]["almuerzo"] or plan["plan"]["desayuno"]
    assert profile.engine_errors == []


# 19 — Todas las lesiones + severidad aguda ────────────────────────

def test_caso_19_todas_lesiones_aguda():
    p = UserProfile(age=30, injuries=["lumbar", "rodilla", "hombro", "cervical",
                                      "codo", "muneca", "tobillo", "cadera",
                                      "dolor_general", "movilidad"],
                    injury_severity="aguda")
    engine = InferenceEngine()
    engine.run(p)
    rutina = generate_training_plan(p)
    assert rutina["motivo_suspension"]
    assert any("aguda" in m for m in rutina["motivo_suspension"])
    assert all(d["descanso"] for d in rutina["semana"])
    assert p.engine_errors == []


# 20 — Señales de alarma (red flags) ───────────────────────────────

def test_caso_20_red_flags_derivan():
    p, err, _w, _e = run_extreme(dict(age=30, red_flags=["dolor_toracico",
                                                         "mareo_desmayo"]))
    assert not err
    ids = [c["id"] for c in p.conclusions]
    assert "SEG-RF-01" in ids and "SEG-RF-02" in ids
    assert p.conclusions[0]["severity"] == "critica"
    rutina = generate_training_plan(p)
    assert rutina["motivo_suspension"]
    assert "señales de alarma" in rutina["notas"]


# ── Casos extra que ya no se numeran como 21-22 (auditoría) ───────

def test_caso_extra_vegano_soja():
    p, err, adm, _e = run_extreme(dict(age=30, diet_type="vegano",
                                       allergies=["soja"]))
    assert not err
    assert any("soja" in w.lower() and "vegan" in w.lower() for w in adm)
    plan = generate_nutrition_plan(p)
    for rec_list in plan["plan"]["recetas"].values():
        for rec in rec_list:
            assert "soja" not in (rec.get("alergenos") or [])


def test_caso_extra_nombre_notas_gigantes():
    nombre = "A" * 500
    notas  = "x" * 900
    p, err, _w, _e = run_extreme(dict(name=nombre, notes=notas))
    assert not err
    assert len(p.name) == 60      # recortado a NAME_MAX
    assert len(p.notes) == 300    # recortado a NOTES_MAX
    assert p.engine_errors == []