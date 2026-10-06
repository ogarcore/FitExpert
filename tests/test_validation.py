"""
test_validation.py
==================
Validación centralizada de entradas (validation.py):

  - Rangos por campo (edad, peso, estatura, % grasa, comidas/día).
  - NaN / Inf / texto / tipos corruptos → nunca excepción, siempre mensaje.
  - Recorte y saneo de texto (bytes de control, nombres gigantes).
  - Dominios de opciones (objetivo, actividad, experiencia, sexo, lugar).
  - Listas filtradas (lesiones, alergias, preferencias, red flags).
  - Coherencias cruzadas (IMC plausible, menores, adultos mayores, dietas).
  - validate_credentials.
"""

import math

import pytest

from validation import (
    AGE_MAX, AGE_MIN, BODY_FAT_MAX, BODY_FAT_MIN, HEIGHT_MAX, HEIGHT_MIN,
    NAME_MAX, NOTES_MAX, WEIGHT_MAX, WEIGHT_MIN,
    validate_age, validate_body_fat, validate_credentials, validate_evaluation,
    validate_height, validate_meal_frequency, validate_name, validate_weight,
)


def base_data(**overrides) -> dict:
    data = {
        "name": "Mariana López",
        "age": 32,
        "sex": "femenino",
        "weight": 62.5,
        "height": 168,
        "body_fat_pct": "",
        "objective": "mantenimiento",
        "activity_level": "moderado",
        "experience": "intermedio",
        "training_place": "gimnasio",
        "diet_type": "omnivoro",
        "meal_frequency": 3,
        "injuries": [],
        "equipment": [],
        "allergies": [],
        "intolerances": [],
        "preferences": [],
        "red_flags": [],
        "injury_severity": "ninguna",
        "balance_issues": False,
    }
    data.update(overrides)
    return data


def test_valid_data_canonical():
    values, errores, advertencias = validate_evaluation(base_data())
    assert errores == {}, errores
    assert values["age"] == 32
    assert values["weight"] == 62.5
    assert values["height"] == 168.0
    assert values["body_fat_pct"] == 0.0  # vacío → 0 (dato no informado)
    assert values["sex"] == "femenino"
    assert values["injury_severity"] == "ninguna"
    assert values["balance_issues"] is False
    assert values["notes"] == ""
    assert isinstance(values["allergies"], list)


@pytest.mark.parametrize("campo,valor,mensaje", [
    ("age", 9, "mínima"),
    ("age", 101, "máxima"),
    ("age", "veinte", "entero"),
    ("age", 32.5, "entero"),
    ("weight", 29, "mínimo"),
    ("weight", 301, "máximo"),
    ("weight", -5, "mayor que cero"),
    ("weight", "setenta", "número"),
    ("height", 99, "mínima"),
    ("height", 251, "máxima"),
    ("height", 0, "mayor que cero"),
    ("body_fat_pct", 2.5, "entre"),
    ("body_fat_pct", 71, "entre"),
    ("body_fat_pct", -1, "negativo"),
    ("meal_frequency", 2, "Elige entre"),
    ("meal_frequency", 6, "Elige entre"),
    ("meal_frequency", "muchas", "entero"),
])
def test_range_violations_friendly(campo, valor, mensaje):
    data = base_data(**{campo: valor})
    values, errores, _ = validate_evaluation(data)
    assert campo in errores, f"{campo}={valor!r} debía tener error"
    assert mensaje in errores[campo]
    # El error es un mensaje humano, jamás un typename
    assert not errores[campo].startswith("ValueError")


def test_nan_and_inf_never_exception():
    for campo in ("age", "weight", "height", "body_fat_pct"):
        for malo in (math.nan, math.inf, -math.inf, float("nan")):
            data = base_data(**{campo: malo})
            _values, errores, _ = validate_evaluation(data)
            assert campo in errores, f"{campo}={malo!r} debía fallar"
    # strings que parecen NaN/Inf
    for campo in ("weight", "height", "body_fat_pct"):
        for texto in ("nan", "inf", "-inf", "NaN", "Infinity"):
            data = base_data(**{campo: texto})
            _values, errores, _ = validate_evaluation(data)
            assert campo in errores


def test_decimal_comma_accepted():
    values, errores, _ = validate_evaluation(base_data(weight="62,4", height="1,68 m"))
    assert "weight" not in errores or values["weight"] is not None


def test_garbage_types_never_raise():
    """Tipos catástrofe (dicts, listas, objetos) → error legible o limpieza."""
    for campo in ("name", "age", "sex", "weight", "height", "body_fat_pct",
                  "objective", "activity_level", "experience", "training_place",
                  "meal_frequency"):
        for basura in ({"x": 1}, [1, 2], object(), None, True):
            try:
                _values, errores, _ = validate_evaluation(base_data(**{campo: basura}))
            except Exception as exc:  # pragma: no cover
                pytest.fail(f"{campo}={basura!r} lanzó {type(exc).__name__}")


def test_name_sanitized_and_trimmed():
    pesado = "A" * 500
    values, errores, _ = validate_evaluation(base_data(name=pesado))
    assert "name" not in errores
    assert len(values["name"]) == NAME_MAX

    con_controles = "Mar\u0000iana\u0007\tLópez"
    values, errores, _ = validate_evaluation(base_data(name=con_controles))
    assert "name" not in errores
    assert "\x00" not in values["name"] and "\x07" not in values["name"]

    vacio = validate_evaluation(base_data(name="   "))
    assert "name" in vacio[1]


def test_name_forbidden_symbols():
    for nombre in ("Juan#", "x@y.com", "nom>bre", "a;b"):
        _values, errores, _ = validate_evaluation(base_data(name=nombre))
        assert "name" in errores


def test_invalid_choice_domain():
    for campo, malo in [("objective", "volverse millonario"),
                        ("activity_level", "muy activísimo"),
                        ("experience", "legendario"),
                        ("sex", "otro"),
                        ("training_place", "en la luna")]:
        _values, errores, _ = validate_evaluation(base_data(**{campo: malo}))
        assert campo in errores, campo
        assert "Selecciona una opción válida" in errores[campo]


def test_human_labels_reversed_to_keys():
    data = base_data(sex="Masculino", objective="Pérdida de grasa",
                     activity_level="Moderado (3–5 días/semana)")
    values, errores, _ = validate_evaluation(data)
    assert errores == {}
    assert values["sex"] == "masculino"
    assert values["objective"] == "perdida_grasa"


def test_sex_always_canonical():
    """La clave legada numérica (1/2) y la etiqueta humana deben producir
    SIEMPRE el valor canónico que consumen reglas, cálculos, PDF y hechos."""
    for entrada, esperado in (("masculino", "masculino"), ("femenino", "femenino"),
                              ("Masculino", "masculino"), ("Femenino", "femenino"),
                              ("1", "masculino"), ("2", "femenino")):
        values, errores, _ = validate_evaluation(base_data(sex=entrada))
        assert errores == {}, entrada
        assert values["sex"] == esperado, (entrada, values["sex"])


def test_diet_invalid_defaults_to_omnivoro():
    values, errores, _ = validate_evaluation(base_data(diet_type="paleoextremo"))
    assert "diet_type" not in errores
    assert values["diet_type"] == "omnivoro"


def test_bad_lists_filtered():
    data = base_data(
        injuries=["rodilla", "inexistente", "lumbar", 42, None],
        allergies=["soja", "bogus", "gluten", "x"],
        preferences=["alta_proteina", "zzz"],
        red_flags=["mareo_desmayo", "no-existe"],
        equipment=["mancuernas", "hoverboard"],
    )
    values, errores, _ = validate_evaluation(data)
    assert errores == {}
    assert values["injuries"] == ["rodilla", "lumbar"]
    assert values["allergies"] == ["soja", "gluten"]
    assert values["preferences"] == ["alta_proteina"]
    assert values["red_flags"] == ["mareo_desmayo"]
    assert values["equipment"] == ["mancuernas"]


def test_severity_coerced_when_no_injuries():
    data = base_data(injury_severity="aguda", balance_issues=True)
    values, errores, _ = validate_evaluation(data)
    assert errores == {}
    assert values["injury_severity"] == "ninguna"
    assert values["balance_issues"] is False  # coherencia: balance requiere lesión declarada


def test_severity_defaults_to_moderada():
    values, errores, _ = validate_evaluation(
        base_data(injuries=["rodilla"], injury_severity=None))
    assert errores == {}
    assert values["injury_severity"] == "moderada"


def test_imc_implausible_becomes_error():
    data = base_data(weight=300, height=100)  # IMC 300
    _values, errores, _ = validate_evaluation(data)
    assert "weight" in errores and "plausible" in errores["weight"]


def test_imc_extreme_warns():
    data = base_data(weight=32, height=170)  # IMC 11.1 → extremo bajo
    _values, errores, advertencias = validate_evaluation(data)
    assert errores == {}
    extreme = [w for w in advertencias if "IMC" in w and "extremo" in w]
    assert extreme
    assert any("Peso muy bajo" in w for w in advertencias)


def test_minor_warnings():
    data = base_data(age=15, objective="perdida_grasa", experience="avanzado")
    _values, errores, advertencias = validate_evaluation(data)
    assert errores == {}
    assert any("menor de edad" in w.lower() for w in advertencias)
    assert any("menores" in w.lower() and "supervisión" in w.lower() for w in advertencias)


def test_senior_warnings():
    data = base_data(age=68, activity_level="sedentario", injuries=["cadera"], balance_issues=True)
    values, errores, advertencias = validate_evaluation(data)
    assert errores == {}
    assert values["age"] == 68
    assert any("equilibrio" in w.lower() for w in advertencias)
    assert any("sedentarismo en adulto mayor" in w.lower() for w in advertencias)


def test_soja_vegan_warning():
    data = base_data(diet_type="vegano", allergies=["soja"])
    _values, errores, advertencias = validate_evaluation(data)
    assert sum("soja" in w.lower() and "vegana" in w.lower() for w in advertencias) >= 1


def test_gluten_allergy_warning():
    data = base_data(allergies=["gluten"])
    _values, errores, advertencias = validate_evaluation(data)
    assert any("celiaquía" in w.lower() for w in advertencias)


def test_red_flags_warning_first():
    data = base_data(red_flags=["dolor_toracico"])
    _values, errores, advertencias = validate_evaluation(data)
    assert advertencias and "ALARMA" in advertencias[0]


def test_nan_never_reaches_profile_values():
    data = base_data(weight=math.nan, height=math.inf)
    values, errores, _ = validate_evaluation(data)
    assert "weight" in errores and "height" in errores
    assert all(isinstance(v, (int, float)) or not isinstance(v, float)
               for k, v in values.items()
               if k in ("weight", "height", "body_fat_pct", "age"))


# ── validate_credentials ───────────────────────────────────────────────

def test_credentials_ok():
    r = validate_credentials("  Ana María  ", "ContrasenaSegura129", for_register=True)
    assert r["ok"] and r["username"] == "Ana María"


def test_credentials_empty_username():
    assert not validate_credentials(" ", "x", for_register=True)["ok"]


def test_credentials_short_username_register():
    assert not validate_credentials("ab", "ContrasenaSegura129", for_register=True)["ok"]


def test_credentials_short_password():
    assert not validate_credentials("ana", "1234567", for_register=True)["ok"]


def test_credentials_password_eql_username():
    assert not validate_credentials("mismaclave", "mismaclave", for_register=True)["ok"]


def test_credentials_long_password():
    assert not validate_credentials("ana", "x" * 129, for_register=True)["ok"]


def test_credentials_login_only_requires_password():
    assert not validate_credentials("ana", "", for_register=False)["ok"]
    assert validate_credentials("ana", "loquesea", for_register=False)["ok"]


def test_boundaries_valid():
    assert validate_age(AGE_MIN).ok and validate_age(AGE_MAX).ok
    assert validate_weight(WEIGHT_MIN).ok and validate_weight(WEIGHT_MAX).ok
    assert validate_height(HEIGHT_MIN).ok and validate_height(HEIGHT_MAX).ok
    assert validate_body_fat(BODY_FAT_MIN).ok and validate_body_fat(BODY_FAT_MAX).ok
    assert validate_meal_frequency(3).ok and validate_meal_frequency(5).ok


def test_short_name_rejected():
    assert not validate_name("A").ok
    assert not validate_name("").ok


def test_notes_trimmed():
    data = base_data(notes="x" * 900)
    values, errores, _ = validate_evaluation(data)
    assert errores == {}
    assert len(values["notes"]) == NOTES_MAX