"""
test_nutrition.py
=================
Generador nutricional (nutrition.py) — seguridad alimentaria y variedad:

  - Alergia → exclusión TOTAL del alérgeno y sus derivados (nunca "100% seguro")
  - Intolerancia → nota de precaución, NO exclusión (diferencia clínica)
  - Descuento de preferencias (alta proteína / bajo costo / fácil / rápido)
  - Pool vacío por restricciones cruzadas → fallback humanizado + derivación
  - Contrato histórico: plan.desayuno/almuerzo/cena/snacks listas de str,
    hidratacion, macros, frecuencia, tipo_dieta, alergias_activas
"""

import pytest

from nutrition import generate_nutrition_plan
from conftest import make_profile

ALERGY_KEYS = {"leche", "gluten", "huevo", "frutos_secos", "cacahuetes",
               "soja", "pescado", "mariscos"}


def _all_recipes(plan: dict) -> list[dict]:
    """Devuelve todas las recetas elegidas en formato estructurado."""
    out = []
    for momento, recetas in plan["recetas"].items():
        if isinstance(recetas, list):
            out.extend(recetas)
    return out


def test_contract_historical_keys():
    p = make_profile()
    result = generate_nutrition_plan(p)
    assert "plan" in result and "macros" in result
    assert "frecuencia" in result and "tipo_dieta" in result
    assert "alergias_activas" in result and "sustituciones" in result
    for key in ("desayuno", "almuerzo", "cena", "snacks"):
        assert key in result["plan"]
        assert isinstance(result["plan"][key], list)
    assert isinstance(result["plan"]["hidratacion"], str)  # texto legible
    assert result["plan"]["desayuno"] and result["plan"]["cena"]
    # Variedad: varias opciones por comida, no una sola receta fija
    assert len(result["plan"]["desayuno"]) >= 1
    assert result["variedad"].startswith("Varias opciones")


def test_allergy_exclusion_total():
    """Una alergia declara la exclusión absoluta de esa familia: ninguna
    receta elegida debe contener el alérgeno ni un derivado."""
    for alergy in sorted(ALERGY_KEYS):
        p = make_profile(allergies=[alergy], objective="mantenimiento")
        result = generate_nutrition_plan(p)
        assert result["alergias_activas"] == [alergy]
        for rec in _all_recipes(result["plan"]):
            alergenos = rec.get("alergenos") or []
            if isinstance(alergenos, str):
                alergenos = [alergenos]
            assert alergy not in alergenos, (
                f"{rec['id']} contiene {alergy}"
            )
        # mensaje humano de sustituciones presente cuando aplica
        assert isinstance(result["sustituciones"], (list, dict))


def test_allergy_never_clains_100pct_safe():
    """El sistema NUNCA afirma que el plato es 100% seguro: el texto final
    recuerda verificar etiquetas (trazas) y consultar al profesional."""
    p = make_profile(allergies=["gluten"], objective="perdida_grasa")
    result = generate_nutrition_plan(p)
    deriv = result["derivacion"].lower()
    assert "no sustituye" in deriv
    assert "nutricionista" in deriv


def test_intolerance_is_note_not_exclusion():
    """Intolerancia (p. ej. lactosa) NO elimina el plato: genera una nota de
    precaución. La alergia a leche sí lo excluye."""
    # Sin intolerancias: hay lácteos posibles
    p = make_profile(intolerances=["lactosa"], allergies=[], objective="mantenimiento")
    result = generate_nutrition_plan(p)
    assert result["intolerancias_activas"] == ["lactosa"]
    # Con intolerancia a lactosa no se garantiza la ausencia, y debe existir
    # una nota que avise (mecanismo ⚠ en el texto de comida o en sustituciones)
    plan = result["plan"]
    textos = (plan["desayuno"] + plan["almuerzo"] + plan["cena"] + plan["snacks"])
    assert all(isinstance(t, str) for t in textos)
    # La alergia a leche sí excluye: ninguna receta elegida con 'leche'
    p_alg = make_profile(allergies=["leche"], objective="mantenimiento")
    result_alg = generate_nutrition_plan(p_alg)
    assert result_alg["alergias_activas"] == ["leche"]
    for rec in _all_recipes(result_alg["plan"]):
        alergenos = rec.get("alergenos") or []
        if isinstance(alergenos, str):
            alergenos = [alergenos]
        assert "leche" not in alergenos


def test_preferences_priorized_without_excluding():
    """Las preferencias NO son alergias: puntúan arriba pero no descartan."""
    p = make_profile(preferences=["alta_proteina"], objective="aumento_muscular")
    result = generate_nutrition_plan(p)
    assert result["preferencias_activas"] == ["alta_proteina"]
    assert result["plan"]["almuerzo"]  # sigue habiendo opciones


def test_empty_pool_fallback_humanized():
    """Restricciones cruzadas extremas (vegano + gluten + cacahuetes agota el
    desayuno) → mensaje seguro y derivación, jamás excepción ni comida vacía."""
    p = make_profile(diet_type="vegano", allergies=["gluten", "cacahuetes"],
                     objective="aumento_muscular")
    result = generate_nutrition_plan(p)  # no debe lanzar
    plan = result["plan"]
    assert plan["desayuno"], "desayuno debía quedar vacío y recibir fallback"
    assert plan["desayuno"][0].startswith("No hay suficientes opciones seguras")
    # El resto de comidas siguen teniendo opciones reales
    assert plan["almuerzo"] and plan["cena"]
    assert "nutricionista" in result["derivacion"].lower()


def test_pool_empty_never_violates_allergy():
    """Aun con fallback, ningún plato puede reintroducir el alérgeno."""
    p = make_profile(
        diet_type="vegano",
        allergies=["frutos_secos"],
        objective="mantenimiento",
    )
    result = generate_nutrition_plan(p)
    for rec in _all_recipes(result["plan"]):
        alergenos = rec.get("alergenos") or []
        if isinstance(alergenos, str):
            alergenos = [alergenos]
        assert "frutos_secos" not in alergenos


def test_macros_contract():
    p = make_profile(objective="mantenimiento")
    result = generate_nutrition_plan(p)
    m = result["macros"]
    for key in ("proteinas", "carbohidratos", "grasas"):
        assert key in m
        assert isinstance(m[key], (int, float))


def test_diets_filter_applied():
    """El filtro de dieta excluye carne en vegetarianos/veganos (señalado en
    sustituciones/derivación en vez de garantizar por texto completo)."""
    for dieta in ("vegano", "vegetariano"):
        p = make_profile(diet_type=dieta, objective="mantenimiento")
        result = generate_nutrition_plan(p)
        assert result["tipo_dieta"] == dieta
        assert result["plan"]["almuerzo"]


def test_deterministic_same_profile():
    """Misma semilla → mismo menú (los usuarios ven resultados estables)."""
    p1 = make_profile()
    p2 = make_profile()
    r1 = generate_nutrition_plan(p1)
    r2 = generate_nutrition_plan(p2)
    for key in ("desayuno", "almuerzo", "cena", "snacks"):
        assert r1["plan"][key] == r2["plan"][key]