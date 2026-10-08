"""
macros_chart.py
===============
Gráfico de dona de macronutrientes + leyenda (generados en SVP inline).

Funciones puras y testeables: no tocan `st`. `gui.py` solo las consume.

Colores: reaprovecha los mismos tokens que las barras antiguas
(proteínas → DS.PRIMARY, carbohidratos → DS.ACCENT, grasas → DS.GOLD).

Robustez: total 0, datos ausentes o macro 0% no lanzan excepción.
Texto de etiquetas escapado.
"""

from __future__ import annotations

import html
import math

import design_system as DS

_KCAL_PER_GRAM = {"proteinas": 4.0, "carbohidratos": 4.0, "grasas": 9.0}

_SEGS = (
    ("proteinas", "Proteínas", "P"),
    ("carbohidratos", "Carbohidratos", "C"),
    ("grasas", "Grasas", "G"),
)


def _macros_normalizados(macros: dict | None) -> dict:
    macros = macros or {}
    def _g(k):
        try:
            v = float(macros.get(k, 0) or 0)
            return v if v == v and v != float("inf") and v != float("-inf") else 0.0
        except (TypeError, ValueError):
            return 0.0
    return {
        "proteinas": _g("proteinas"),
        "carbohidratos": _g("carbohidratos"),
        "grasas": _g("grasas"),
        "p_pct": _g("p_pct"),
        "c_pct": _g("c_pct"),
        "g_pct": _g("g_pct"),
    }


def macro_pcts(macros: dict | None) -> dict:
    """
    Devuelve {'proteinas': int, 'carbohidratos': int, 'grasas': int}
    (% de calorías), sumando exactamente 100.

    - Si el plan ya trae p_pct/c_pct/g_pct, se usan (normalizados por
      el mayor resto).
    - Si no, se calculan como gramos × kcal/g / total y se redondean con
      el mayor resto.
    """
    m = _macros_normalizados(macros)
    raw_p, raw_c, raw_g = m["p_pct"], m["c_pct"], m["g_pct"]
    if raw_p <= 0 and raw_c <= 0 and raw_g <= 0:
        total_cal = (m["proteinas"] * 4 + m["carbohidratos"] * 4
                     + m["grasas"] * 9)
        if total_cal <= 0:
            return {"proteinas": 0, "carbohidratos": 0, "grasas": 0}
        raw_p = m["proteinas"] * 4 / total_cal * 100
        raw_c = m["carbohidratos"] * 4 / total_cal * 100
        raw_g = m["grasas"] * 9 / total_cal * 100
    else:
        raw_p = max(raw_p, 0); raw_c = max(raw_c, 0); raw_g = max(raw_g, 0)
        s = raw_p + raw_c + raw_g
        if s <= 0:
            return {"proteinas": 0, "carbohidratos": 0, "grasas": 0}
        raw_p, raw_c, raw_g = raw_p / s * 100, raw_c / s * 100, raw_g / s * 100

    return _mayor_resto([raw_p, raw_c, raw_g], ["proteinas", "carbohidratos", "grasas"])


def _mayor_resto(valores: list, claves: list) -> dict:
    pisos = [int(v) for v in valores]
    resto = 100 - sum(pisos)
    scores = sorted(
        [(valores[i] - pisos[i], claves[i]) for i in range(len(valores))],
        key=lambda t: (-t[0], claves.index(t[1])),
    )
    for i in range(resto):
        pisos[claves.index(scores[i][1])] += 1
    return {claves[i]: pisos[i] for i in range(len(valores))}


def _angulo_segmento(pct: float) -> float:
    return max(0.0, min(100.0, pct)) * 3.6


def donut_svg(macros: dict | None, target_calories: float | None) -> str:
    """
    HTML (SVG inline) del gráfico de dona con etiquetas y líneas guía.
    Devuelve "" si no hay datos con los que dibujar.
    """
    m = _macros_normalizados(macros)
    pcts = macro_pcts(m)
    total = sum(pcts.values())
    if total <= 0:
        return ""

    colores = {
        "proteinas": DS.PRIMARY,
        "carbohidratos": DS.ACCENT,
        "grasas": DS.GOLD,
    }

    W, H, cx, cy, R, sw = 420, 260, 210, 130, 84, 28
    gap = 2.0  # grados entre segmentos

    partes = []
    ang_inicio = -90.0
    labels = []
    for key, label, _short in _SEGS:
        pct = pcts[key]
        if pct <= 0:
            continue
        a0 = ang_inicio + gap / 2
        a1 = ang_inicio + _angulo_segmento(pct) - gap / 2
        if a1 < a0:
            a1 = a0
        grande = 1 if (a1 - a0) > 180 else 0
        x0, y0 = _polar(cx, cy, R, a0)
        x1, y1 = _polar(cx, cy, R, a1)
        d = f"M {x0:.1f} {y0:.1f} A {R} {R} 0 {grande} 1 {x1:.1f} {y1:.1f}"
        partes.append(
            f'<path d="{d}" fill="none" stroke="{colores[key]}" '
            f'stroke-width="{sw}" stroke-linecap="butt" />'
        )
        ang_mid = (a0 + a1) / 2
        labels.append({
            "key": key, "label": label, "pct": pct, "grams": m[key],
            "color": colores[key], "ang": ang_mid,
        })
        ang_inicio += _angulo_segmento(pct)

    # Etiquetas como HTML absoluto (texto NO escala con el SVG). El SVG sólo
    # conserva el anillo y las guías finas (vector-effect: non-scaling-stroke).
    labels_html = []
    divs_html = []
    for lab in labels:
        cos_m = math.cos(math.radians(lab["ang"]))
        sin_m = math.sin(math.radians(lab["ang"]))
        xA, yA = _polar(cx, cy, R + sw / 2 + 4, lab["ang"])
        # Guía corta: termina antes de llegar al borde del texto.
        xB, yB = _polar(cx, cy, R + sw / 2 + DS.DONUT_LABEL_GAP, lab["ang"])
        # Punto de anclaje del bloque de texto: a GAP px del borde del anillo.
        xL, yL = _polar(cx, cy, R + sw / 2 + DS.DONUT_LABEL_GAP, lab["ang"])
        left = min(max(xL / W * 100, 0), 100)
        top = min(max(yL / H * 100, 0), 100)
        if abs(cos_m) >= abs(sin_m):
            anchor_cls = "r" if cos_m >= 0 else "l"
        else:
            anchor_cls = "b" if sin_m >= 0 else "t"
        labels_html.append(
            f'<path d="M {xA:.1f} {yA:.1f} L {xB:.1f} {yB:.1f}" '
            f'fill="none" stroke="var(--fx-border-2)" stroke-width="1.2" '
            f'vector-effect="non-scaling-stroke" />'
            f'<circle cx="{xA:.1f}" cy="{yA:.1f}" r="2.2" fill="{lab["color"]}" />'
        )
        divs_html.append(
            f'<div class="fx-donut-lbl {anchor_cls}" '
            f'style="left:{left:.1f}%;top:{top:.1f}%">'
            f'<b>{html.escape(lab["label"])}</b>'
            f'<small>{html.escape(f"{lab["grams"]:.0f} g · {lab["pct"]}%")}</small></div>'
        )

    target = target_calories or 0
    centro_html = (
        f'<span class="fx-donut-ct">'
        f'<b>{target:.0f} kcal</b><small>meta diaria</small></span>'
    )

    aria = html.escape(_aria_label(pcts))
    svg = (
        f'<svg class="fx-donut" viewBox="0 0 {W} {H}" role="img" '
        f'aria-label="{aria}" preserveAspectRatio="xMidYMid meet">'
        + "".join(partes)
        + "".join(labels_html)
        + '</svg>'
    )
    return (
        f'<div class="fx-donut-wrap">'
        + svg
        + centro_html
        + ''.join(divs_html)
        + '</div>'
    )


def _polar(cx: float, cy: float, r: float, ang_deg: float) -> tuple:
    a = math.radians(ang_deg)
    return (cx + r * math.cos(a), cy + r * math.sin(a))


def _aria_label(pcts: dict) -> str:
    return (f"Distribución de macronutrientes: proteínas {pcts['proteinas']}%, "
            f"carbohidratos {pcts['carbohidratos']}%, grasas {pcts['grasas']}%")


def macro_legend_html(macros: dict | None) -> str:
    """Leyenda compacta (punto + nombre + gramos · %) para modo estrecho."""
    m = _macros_normalizados(macros)
    pcts = macro_pcts(m)
    if sum(pcts.values()) <= 0:
        return ""
    colores = {
        "proteinas": DS.PRIMARY,
        "carbohidratos": DS.ACCENT,
        "grasas": DS.GOLD,
    }
    filas = []
    for key, label, _short in _SEGS:
        if pcts[key] <= 0:
            continue
        filas.append(
            f'<div class="fx-mleg-row"><span class="fx-mleg-dot" '
            f'style="background:{colores[key]}"></span>'
            f'<span class="fx-mleg-name">{html.escape(label)}</span>'
            f'<b class="fx-mleg-val">{m[key]:.0f} g · {pcts[key]}%</b></div>'
        )
    return f'<div class="fx-mleg">{"".join(filas)}</div>'
