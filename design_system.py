"""
design_system.py
================
Sistema de diseño compartido de FitExpert — v1.0

Concentra las decisiones visuales (paleta, tipografía, espacios, estados,
accesibilidad y micro-interacciones) para que las tres interfaces
(Streamlit `gui.py`, consola `ui.py` y escritorio `app_desktop.pyw`)
sean coherentes entre sí y con la identidad de la aplicación.

Principios:
  - Contraste AA/AAA para texto (los pares de color están calibrados).
  - Estados semánticos de severidad con doble codificación (color + icono),
    nunca solo color (accesibilidad para daltonismo).
  - Micro-interacciones intencionadas: entrada de sección, carga con
    progreso, aparición escalonada de resultados y selección de pestañas.
  - `prefers-reduced-motion` respetado en las animaciones web.
"""

# ──────────────────────────────────────────────
#  Paleta (modo oscuro, base del producto)
# ──────────────────────────────────────────────

BG          = "#0B1220"   # fondo general
BG_ELEV     = "#111A2E"   # tarjetas / superficies
BG_ELEV_2   = "#182338"   # hover / rellenos secundarios
BORDER      = "#22304A"   # bordes
PRIMARY     = "#E94E4E"   # coral FitExpert (acento principal)
PRIMARY_HOV = "#D63C3C"
ACCENT      = "#4EC9B0"   # menta (datos, éxito)
ACCENT_HOV  = "#3BB99F"
TEXT        = "#F2F5FA"   # texto principal
TEXT_MUTED  = "#9AA8C0"   # texto secundario
INFO        = "#4C9AFF"   # azul informativo
WARNING     = "#FFB020"   # ámbar preventivo
DANGER      = "#FF5A5F"   # rojo crítico
SUCCESS     = "#3FC889"   # verde éxito

# ──────────────────────────────────────────────
#  Severidad → (etiqueta, color, icono, orden)
#  Doble codificación: color + icono para daltonismo
# ──────────────────────────────────────────────

SEVERITY_STYLE = {
    "critica": {"label": "Crítica", "color": DANGER,  "icon": "⛔", "order": 0},
    "alta":    {"label": "Alta",    "color": WARNING, "icon": "⚠️", "order": 1},
    "media":   {"label": "Media",   "color": INFO,    "icon": "▪️", "order": 2},
    "baja":    {"label": "Baja",    "color": SUCCESS, "icon": "▫️", "order": 3},
    "info":    {"label": "Info",    "color": TEXT_MUTED, "icon": "ℹ️", "order": 4},
}

# ──────────────────────────────────────────────
#  Tiers de la base de conocimiento → estilo
# ──────────────────────────────────────────────

TIER_STYLE = {
    "SEGURIDAD":           {"label": "Seguridad",         "color": DANGER,  "icon": "🛡️"},
    "CONTRAINDICACIONES":  {"label": "Contraindicaciones", "color": WARNING, "icon": "🚫"},
    "EDAD":                {"label": "Edad",              "color": INFO,    "icon": "🎂"},
    "CONDICION_FISICA":    {"label": "Condición física",   "color": PRIMARY, "icon": "🏥"},
    "OBJETIVO":            {"label": "Objetivo",          "color": ACCENT,  "icon": "🎯"},
    "PREFERENCIAS":        {"label": "Preferencias",      "color": "#B48CF2", "icon": "⭐"},
    "SEGUIMIENTO":         {"label": "Seguimiento",       "color": "#F2C14E", "icon": "📈"},
}

# ──────────────────────────────────────────────
#  Categorías → icono (consolas y web)
# ──────────────────────────────────────────────

CATEGORY_ICON = {
    "nutricion":     "🥗",
    "entrenamiento": "🏋️",
    "lesión":        "🩹",
    "biomecánica":   "🧍",
    "alerta":        "⚠️",
    "seguimiento":   "📈",
    "objetivo":      "🎯",
    "preferencias":  "⭐",
    "edad":          "🎂",
    "salud":         "❤️",
}

# ──────────────────────────────────────────────
#  Tipografía y espaciado
# ──────────────────────────────────────────────

FONT_FAMILY_WEB = '"Inter", "Segoe UI", system-ui, -apple-system, sans-serif'
FONT_FAMILY_MONO = '"JetBrains Mono", "Cascadia Code", Consolas, monospace'

SPACE = {
    "xs": 4, "sm": 8, "md": 16, "lg": 24, "xl": 40, "2xl": 64,
}


def severity_style(severity: str) -> dict:
    """Devuelve el estilo de severidad (con fallback seguro)."""
    return SEVERITY_STYLE.get(severity or "info", SEVERITY_STYLE["info"])


def tier_style(tier: str) -> dict:
    """Devuelve el estilo visual de un tier de la base de conocimiento."""
    return TIER_STYLE.get(tier, {"label": tier, "color": TEXT_MUTED, "icon": "•"})


def badge_html(severity: str, tier: str = "") -> str:
    """
    Genera HTML de insignia de severidad (+ tier opcional) con doble
    codificación color/icono. Usado solo por interfaces web (gui.py).
    """
    sev = severity_style(severity)
    parts = [
        f'<span style="color:{sev["color"]};font-weight:600;'
        f'font-size:0.78em;padding:2px 8px;border:1px solid {sev["color"]}55;'
        f'border-radius:999px;white-space:nowrap;">'
        f'{sev["icon"]} {sev["label"].upper()}</span>'
    ]
    if tier:
        ts = tier_style(tier)
        parts.append(
            f'<span style="color:{ts["color"]};font-weight:600;'
            f'font-size:0.78em;padding:2px 8px;border:1px solid {ts["color"]}55;'
            f'border-radius:999px;white-space:nowrap;">'
            f'{ts["icon"]} {ts["label"].upper()}</span>'
        )
    return "&nbsp;".join(parts)


# ──────────────────────────────────────────────
#  CSS web compartido (gui.py)
# ──────────────────────────────────────────────

WEB_CSS = f"""
<style>
:root {{
    --fx-bg:        {BG};
    --fx-bg-elev:   {BG_ELEV};
    --fx-bg-elev-2: {BG_ELEV_2};
    --fx-border:    {BORDER};
    --fx-primary:   {PRIMARY};
    --fx-acc:       {ACCENT};
    --fx-text:      {TEXT};
    --fx-muted:     {TEXT_MUTED};
    --fx-info:      {INFO};
    --fx-warn:      {WARNING};
    --fx-danger:    {DANGER};
    --fx-success:   {SUCCESS};
}}

.stApp {{
    font-family: {FONT_FAMILY_WEB};
    background: linear-gradient(180deg, #0B1220 0%, #0E1730 45%, #0B1220 100%);
    color: var(--fx-text);
}}

#MainMenu, footer {{ visibility: hidden; }}

/* Títulos */
.fx-hero {{
    font-size: 2.1rem; font-weight: 800; letter-spacing: -0.02em;
    background: linear-gradient(90deg, var(--fx-text), var(--fx-acc));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem; line-height: 1.15;
}}
.fx-sub {{
    color: var(--fx-muted); font-size: 1.05rem; margin-bottom: 1.4rem;
}}
.fx-section-title {{
    font-weight: 700; font-size: 1.05rem; color: var(--fx-text);
    border-left: 3px solid var(--fx-primary); padding-left: 0.6rem; margin: 0;
}}

/* Tarjetas de resultado */
.fx-card {{
    background: var(--fx-bg-elev);
    border: 1px solid var(--fx-border);
    border-radius: 14px;
    padding: 1rem 1.15rem;
    margin-bottom: 0.8rem;
    border-left: 4px solid var(--fx-border);
}}
.fx-card--crit  {{ border-left-color: var(--fx-danger); }}
.fx-card--alta  {{ border-left-color: var(--fx-warn); }}
.fx-card--media {{ border-left-color: var(--fx-info); }}
.fx-card--baja  {{ border-left-color: var(--fx-success); }}
.fx-card--info  {{ border-left-color: var(--fx-muted); }}
.fx-card--sup   {{ border-left-color: #B48CF2; border-style: dashed; opacity: 0.85; }}
.fx-card--err   {{ border-left-color: var(--fx-danger); background: {DANGER}0D; }}

/* Métricas */
.fx-metric {{
    background: var(--fx-bg-elev);
    border: 1px solid var(--fx-border); border-radius: 14px;
    padding: 0.9rem 1rem; text-align: center;
    transition: transform 160ms ease, border-color 160ms ease;
}}
.fx-metric:hover {{ transform: translateY(-2px); border-color: var(--fx-acc); }}
.fx-metric .v {{
    font-size: 1.7rem; font-weight: 800; color: var(--fx-text); line-height: 1.1;
}}
.fx-metric .l {{ color: var(--fx-muted); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.06em; }}
.fx-metric .s {{ color: var(--fx-muted); font-size: 0.72rem; }}

/* Primer render de resultados: aparición escalonada */
@keyframes fx-rise {{
    from {{ opacity: 0; transform: translateY(8px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}
.fx-rise {{ animation: fx-rise 320ms ease both; }}

/* Barra de pasos del formulario */
.fx-stepper {{ display: flex; gap: 0.4rem; align-items: center; margin: 0.9rem 0 1.2rem; }}
.fx-step {{
    flex: 1; text-align: center; padding: 0.45rem 0.3rem; border-radius: 10px;
    background: var(--fx-bg-elev); border: 1px solid var(--fx-border);
    color: var(--fx-muted); font-size: 0.78rem; font-weight: 600;
    transition: all 180ms ease;
}}
.fx-step.active {{
    background: var(--fx-primary); color: #fff; border-color: var(--fx-primary);
    box-shadow: 0 4px 14px rgba(233, 78, 78, 0.35);
}}
.fx-step.done {{ border-color: var(--fx-acc); color: var(--fx-acc); }}

/* Botón principal con pulso sutil (solo una vez, no constante) */
@keyframes fx-pop {{ 0% {{ transform: scale(1); }} 50% {{ transform: scale(0.985); }} 100% {{ transform: scale(1); }} }}
.fx-cta:hover {{ animation: fx-pop 240ms ease; }}

/* Accesibilidad: foco visible + reducción de movimiento */
:focus-visible {{ outline: 2px solid var(--fx-acc); outline-offset: 2px; }}
@media (prefers-reduced-motion: reduce) {{
    .fx-metric, .fx-rise, .fx-step, .fx-cta {{ transition: none !important; animation: none !important; }}
}}
[data-testid="stSidebar"] {{
    background: var(--fx-bg-elev); border-right: 1px solid var(--fx-border);
}}
[data-testid="stSidebar"] a, [data-testid="stSidebar"] .stMarkdown {{ color: var(--fx-text); }}
.stTabs [data-baseweb="tab-list"] {{ gap: 0.4rem; }}
.stTabs [data-baseweb="tab"] {{
    background: var(--fx-bg-elev); border: 1px solid var(--fx-border);
    border-radius: 10px; padding: 0.4rem 1rem; color: var(--fx-muted);
    transition: all 160ms ease;
}}
.stTabs [aria-selected="true"] {{
    background: var(--fx-bg-elev-2); color: var(--fx-text);
    border-color: var(--fx-primary);
}}
</style>
"""


# ──────────────────────────────────────────────
#  Paleta de consola priorizada por Colorama/rich
#  (estilos numerados, compatibles con TUI)
# ──────────────────────────────────────────────

CONSOLE = {
    "primary":  "bold #E94E4E",
    "accent":   "bold #4EC9B0",
    "info":     "bold #4C9AFF",
    "warn":     "bold #FFB020",
    "danger":   "bold #FF5A5F",
    "success":  "bold #3FC889",
    "muted":    "dim #9AA8C0",
    "text":     "#F2F5FA",
}


def cli_badge(severity: str) -> str:
    """Badge de consola: `[estilo]icono ETIQUETA[/estilo]` (rich markup)."""
    sev = severity_style(severity)
    return f"[{sev['color']}]{sev['icon']} {sev['label'].upper()}[/{sev['color']}]"


def summary_line(stats: dict) -> str:
    """Línea de resumen del ciclo de inferencia para todos los frontends."""
    return (
        f"{stats.get('fired', 0)} reglas activadas · "
        f"{stats.get('suppressed', 0)} suprimidas · "
        f"{stats.get('skipped', 0)} inaplicadas · "
        f"{stats.get('errors', 0)} con error"
    )