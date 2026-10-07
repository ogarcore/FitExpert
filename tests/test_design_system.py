"""
test_design_system.py
=====================
Garantías de la identidad única (fase 2):

1. Sin emojis como iconografía en ninguno de los tres canales
   (consola, web, desktop).
2. Pares Fluent / MDL2 alineados 1:1 (fallback desktop coherente).
3. Contrato del cliente de consola preservado: order/color/icon/label.
4. Utilerías de presentación web (SVG, chips, alerts, CSS) presentes
   y coherentes con la paleta de marca.

No toca bases de datos: solo importa el módulo de diseño.
"""
import re

import pytest

from design_system import (
    SEVERITY_STYLE, TIER_STYLE, CATEGORY_ICON, CONSOLE, FLUENT, FLUENT_MDL2,
    ICONS, icon_svg, brand_svg, chip_html, badge_html, alert_html,
    summary_line, cli_badge, WEB_CSS,
)

# Caras emoji y pictografías que NO deberían aparecer como iconos
EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF]"
)


def _walk_icons():
    """Todos los valores de icono de los tres canales."""
    yield from SEVERITY_STYLE.values()
    yield from CATEGORY_ICON.values()
    yield from FLUENT.values()
    yield from FLUENT_MDL2.values()
    yield from ICONS.keys()


def test_no_emojis_en_mapa_de_iconos():
    from design_system import SEVERITY_STYLE as SS, TIER_STYLE as TS

    for item in SS.values():
        icon = item.get("icon", "")
        assert not EMOJI_RE.search(str(icon)), f"Severidad con emoji: {icon!r}"
    for item in TS.values():
        icon = item.get("icon", "")
        assert not EMOJI_RE.search(str(icon)), f"Tier con emoji: {icon!r}"
    for icon in CATEGORY_ICON.values():
        assert not EMOJI_RE.search(str(icon)), f"Categoría con emoji: {icon!r}"
    for cp in FLUENT.values():
        assert not EMOJI_RE.search(str(cp)), f"Fluent con rango emoji: {cp!r}"


def test_fluent_y_mdl2_alineados_1a1():
    falta = set(FLUENT.keys()) - set(FLUENT_MDL2.keys())
    sobra = set(FLUENT_MDL2.keys()) - set(FLUENT.keys())
    # La única diferencia documentada: "calendario_dia" no tiene par MDL2.
    assert falta <= {"calendario_dia"}, f"Fluent sin par MDL2: {falta}"
    assert not sobra, f"MDL2 con claves ajenas: {sobra}"
    for key in FLUENT_MDL2:
        assert FLUENT[key], f"Clave {key} sin codepoint Fluent"


def test_codepoints_fluent_en_rango_privado():
    # Fuentes de símbolos (Segoe Fluent / MDL2) viven en el plano privado E000–F8FF
    for name, ch in FLUENT.items():
        code = ord(ch)
        assert 0xE000 <= code <= 0xF8FF, f"{name} fuera de zona de símbolos: {ch!r}"


def test_contrato_ui_consola():
    """ui.py espera (order/)color/icon/label y mapa por categoría."""
    for key, style in SEVERITY_STYLE.items():
        assert {"order", "color", "icon", "label"} <= set(style.keys()), \
            f"SEVERITY_STYLE[{key}] pierde campos"
    for key, style in TIER_STYLE.items():
        assert {"color", "icon", "label"} <= set(style.keys()), \
            f"TIER_STYLE[{key}] pierde campos"
    assert CATEGORY_ICON, "CATEGORY_ICON vacío"
    assert CONSOLE, "CONSOLE vacío"


def test_svg_propios_de_trazo():
    svg = icon_svg("inicio", 18, "#2DD4BF")
    assert svg.startswith("<svg") and svg.endswith("</svg>")
    assert 'stroke="currentColor"' in svg or "#2DD4BF" in svg
    brand = brand_svg(40)
    assert "<svg" in brand and "defs" in brand
    # La marca usa el color primario de la identidad
    assert "2DD4BF" in brand


def test_piezas_css_de_marca_presentes():
    assert "--fx-primary" in WEB_CSS and "#2DD4BF" in WEB_CSS
    for clase in ("fx-top-bar", "fx-top-ic", "fx-footer", "fx-stepper",
                  "fx-step", "fx-band", "fx-metric", "fx-card", "fx-chip",
                  "fx-alert", "fx-nav-label", "fx-auth-wrap"):
        assert ("." + clase) in WEB_CSS, f"Falta clase CSS .{clase}"
    # El sidebar de Streamlit se estiliza por atributo (no clase controlable)
    assert '[data-testid="stSidebar"]' in WEB_CSS


def test_chips_y_badges_no_contienen_emojis():
    for html in (chip_html("Prueba"), badge_html("Alta", "danger"),
                 alert_html("danger", "Titulo", "Cuerpo")):
        inner = re.sub(r"<[^>]+>", "", html)
        assert not EMOJI_RE.search(inner)


def test_helpers_consola_ascii():
    stats = {"evaluadas": 69, "activadas": 12, "suprimidas": 5,
             "inaplicadas": 51, "errores": 0}
    for text in (summary_line(stats), cli_badge("alta")):
        assert not EMOJI_RE.search(text)