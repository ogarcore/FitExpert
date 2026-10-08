"""
test_sidebar_css.py
===================
Garantías del control de la sidebar (plegado/desplegado):

  - El CSS restaura la fuente de Material Symbols para que los iconos
    nativos no se vean como texto crudo ("keyboard_double").
  - Los selectores de los botones de colapsar/expandir están presentes.
  - El CSS NO oculta el header/toolbar (ahí vive el botón que reabre
    la sidebar cuando está plegada).
  - Tests validados contra Streamlit 1.58 (ver comments en design_system).
"""
from design_system import WEB_CSS


def test_restauracion_fuente_iconos():
    assert '"Material Symbols Rounded"' in WEB_CSS
    assert 'span[data-testid="stIconMaterial"]' in WEB_CSS
    assert 'font-feature-settings: "liga"' in WEB_CSS


def test_selectores_botones_sidebar():
    assert 'button[data-testid="stSidebarCollapseButton"]' in WEB_CSS
    assert 'button[data-testid="stExpandSidebarButton"]' in WEB_CSS


def test_no_oculta_header_ni_toolbar():
    assert 'header[data-testid="stHeader"] { visibility: hidden' not in WEB_CSS
    assert '[data-testid="stToolbar"] { display: none' not in WEB_CSS


def test_solo_accesorios_ocultos():
    # MainMenu, deploy, etc. sí se ocultan; el header/toolbar no.
    assert "#MainMenu" in WEB_CSS
    assert 'data-testid="stAppDeployButton"' in WEB_CSS
