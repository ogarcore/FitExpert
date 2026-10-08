"""
test_macros_chart.py
====================
Drona de macronutrientes: % por mayor resto, ángulos, SVG, robustez.
"""
import pytest

from macros_chart import (macro_pcts, donut_svg, macro_legend_html,
                          _angulo_segmento, _macros_normalizados)


def test_sum_pcts_from_plan():
    mpcts = macro_pcts({"proteinas": 168, "carbohidratos": 280, "grasas": 50,
                        "p_pct": 30, "c_pct": 50, "g_pct": 20})
    assert mpcts == {"proteinas": 30, "carbohidratos": 50, "grasas": 20}
    assert sum(mpcts.values()) == 100


def test_pcts_from_grams_largest_remainder():
    # 170 / 280 / 50 g → 680/1120/450 kcal ≈ 30.1/49.6/19.9 %
    m = macro_pcts({"proteinas": 170, "carbohidratos": 280, "grasas": 50})
    assert sum(m.values()) == 100
    assert m["carbohidratos"] == 50


def test_angles_sum_360_con_segmentos_normales():
    ang = sum(_angulo_segmento(p) for p in (30, 50, 20))
    assert abs(ang - 360.0) < 1e-6


def test_donut_svg_datos_normales():
    svg = donut_svg({"proteinas": 168, "carbohidratos": 280, "grasas": 50}, 2242)
    assert svg.startswith('<svg') or '<svg' in svg
    assert 'fecha_der' not in svg
    assert 'role="img"' in svg and 'aria-label=' in svg
    assert 'Proteínas' in svg and 'Carbohidratos' in svg


def test_donut_svg_macro_cero_excluido():
    svg = donut_svg({"proteinas": 168, "carbohidratos": 280, "grasas": 0}, 2000)
    assert 'Grasas' not in svg
    assert 'Proteínas' in svg and 'Carbohidratos' in svg


def test_donut_svg_datos_ausentes_no_falla():
    assert donut_svg(None, 2000) == ""
    assert donut_svg({}, None) == ""
    assert donut_svg({"proteinas": 0, "carbohidratos": 0, "grasas": 0}, 2000) == ""
    assert macro_legend_html(None) == ""


def test_texto_escapado():
    # Por combinación de parámetros se refleja el nombre escapado
    html = macro_legend_html({"proteinas": 168, "carbohidratos": 280, "grasas": 50})
    assert 'fx-mleg-name' in html


def test_macros_normalizados_robusto():
    m = _macros_normalizados({"proteinas": "abc", "carbohidratos": None, "grasas": float('inf')})
    assert m["proteinas"] == 0 and m["carbohidratos"] == 0 and m["grasas"] == 0
