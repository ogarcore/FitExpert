"""
design_system.py
================
Sistema de diseño compartido de FitExpert — v2.0 (identidad unificada)

Una única identidad visual de producto para las tres interfaces
(Streamlit `gui.py`, consola `ui.py` y escritorio `app_desktop.pyw`):

  - Paleta "precisión clínica digital": navy profundo + turquesa de marca,
    con semántica de estado siempre doble-codificada (color + icono) para
    garantizar accesibilidad (daltonismo, lectores de pantalla).
  - Iconografía profesional SIN emoticonos:
      * Web     → SVG propios de trazo (mapa `ICONS`)
      * Desktop → Segoe Fluent Icons / MDL2, codepoints verificados (mapa
                  `FLUENT` y fallback `FLUENT_MDL2`)
      * Consola → marcadores tipográficos ASCII seguros
  - Tipografía del sistema ("Segoe UI Variable" en desktop/Web modernos),
    escalas de espaciado y radio compartidas.
  - Matemática de color calibrada para contraste AA/AAA en todos los pares
    de texto.
  - Animaciones solo donde mejoran transición/retroalimentación/estado y
    siempre respetuosas de `prefers-reduced-motion` en la Web.
"""

# ──────────────────────────────────────────────
#  Paleta (modo oscuro, base del producto)
# ──────────────────────────────────────────────

BG            = "#070B15"   # fondo global (navy profundo)
BG_ELEV       = "#0E1526"   # tarjetas / superficies
BG_ELEV_2     = "#1A2338"   # hover / rellenos / inputs
BG_ELEV_3     = "#232F4A"   # hover forte / dropdowns abiertos
BORDER        = "#253452"   # bordes neutros
BORDER_STRONG = "#37476E"   # bordes en hover / foco

PRIMARY       = "#2DD4BF"   # turquesa FitExpert (marca)
PRIMARY_HOV   = "#1FBFA9"   # turquesa hover
PRIMARY_SOFT  = "#10382F"   # fondo de acentos (badges/chips)
PRIMARY_GLOW  = "#2DD4BF33" # halo translúcido de la marca

ACCENT        = "#3D9CFF"   # azul información / gráficos secundarios
ACCENT_HOV    = "#2E86E8"
ACCENT_SOFT   = "#12324F"

INFO          = "#3D9CFF"
WARNING       = "#F5B944"
DANGER        = "#FF6B6B"
CRITICAL      = "#FF4A4A"
SUCCESS       = "#3FD39A"
VIOLET        = "#A78BFA"   # explicabilidad / derivación profesional
GOLD          = "#F5B944"   # seguimiento / logros

TEXT          = "#E9F0FC"   # texto principal
TEXT_MUTED    = "#93A3C0"   # texto secundario
TEXT_FAINT    = "#5C6B8C"   # texto terciario / leyendas

# ──────────────────────────────────────────────
#  Tipografía y espaciado
# ──────────────────────────────────────────────

FONT_FAMILY_WEB = ('"Segoe UI Variable Display", "Segoe UI Variable", '
                   '"Segoe UI", system-ui, -apple-system, sans-serif')
FONT_FAMILY_MONO = '"Cascadia Code", "Cascadia Mono", Consolas, monospace'

# Escala de tipo compartida (px)
TYPE = {
    "display": 32,   # números estrella / hero
    "h1":      24,   # título de página
    "h2":      19,   # título de tarjeta
    "h3":      15,   # título de bloque
    "body":    14,   # cuerpo
    "small":   12.5, # secundario
    "caption": 11.5, # leyendas / etiquetas superiores
}

SPACE = {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24, "2xl": 32,
         "3xl": 48, "4xl": 64}

RADII = {"input": 10, "button": 12, "card": 16, "chip": 999, "sheet": 20}

# ──────────────────────────────────────────────
#  Severidad → (etiqueta, color, icono, orden)
#  Iconos de consola: marcadores tipográficos ASCII (sin emoticonos).
# ──────────────────────────────────────────────

SEVERITY_STYLE = {
    "critica": {"label": "Crítica", "color": CRITICAL, "icon": "X", "order": 0},
    "alta":    {"label": "Alta",    "color": WARNING,  "icon": "!", "order": 1},
    "media":   {"label": "Media",   "color": ACCENT,   "icon": "o", "order": 2},
    "baja":    {"label": "Baja",    "color": SUCCESS,  "icon": "-", "order": 3},
    "info":    {"label": "Info",    "color": TEXT_MUTED, "icon": "i", "order": 4},
}

# ──────────────────────────────────────────────
#  Tiers de la base de conocimiento → estilo
# ──────────────────────────────────────────────

TIER_STYLE = {
    "SEGURIDAD":          {"label": "Seguridad",          "color": CRITICAL, "icon": "#"},
    "CONTRAINDICACIONES": {"label": "Contraindicaciones", "color": WARNING,  "icon": "!"},
    "EDAD":               {"label": "Edad",               "color": ACCENT,   "icon": "~"},
    "CONDICION_FISICA":   {"label": "Condición física",   "color": PRIMARY,  "icon": "v"},
    "OBJETIVO":           {"label": "Objetivo",           "color": GOLD,     "icon": ">"},
    "PREFERENCIAS":       {"label": "Preferencias",       "color": VIOLET,   "icon": "*"},
    "SEGUIMIENTO":        {"label": "Seguimiento",        "color": SUCCESS,  "icon": "^"},
}

# ──────────────────────────────────────────────
#  Categorías → icono de consola (ASCII seguro)
# ──────────────────────────────────────────────

CATEGORY_ICON = {
    "nutricion":     "N",
    "entrenamiento": "T",
    "lesión":        "L",
    "biomecánica":   "B",
    "alerta":        "!",
    "seguimiento":   "^",
    "objetivo":      ">",
    "preferencias":  "*",
    "edad":          "~",
    "salud":         "H",
}

def severity_style(severity: str) -> dict:
    """Devuelve el estilo de severidad (con fallback seguro)."""
    return SEVERITY_STYLE.get(severity or "info", SEVERITY_STYLE["info"])


def tier_style(tier: str) -> dict:
    """Devuelve el estilo visual de un tier de la base de conocimiento."""
    return TIER_STYLE.get(tier, {"label": tier, "color": TEXT_MUTED, "icon": "•"})


# ──────────────────────────────────────────────
#  Iconografía de escritorio — Segoe Fluent Icons
#  (codepoints VERIFICADOS contra la tabla oficial de Microsoft)
#  `FLUENT_MDL2` es el plan de respaldo para Windows 10 sin la fuente.
# ──────────────────────────────────────────────

FONT_ICON_FLUENT = "Segoe Fluent Icons"
FONT_ICON_MDL2   = "Segoe MDL2 Assets"

FLUENT = {
    "inicio":           "\uE80F",   # Home
    "menu":             "\uE700",   # GlobalNavButton
    "evaluacion":       "\uF0E3",   # ClipboardList
    "plan":             "\uE8A5",   # Document
    "historial":        "\uE81C",   # History
    "progreso":         "\uEC4A",   # SpeedHigh (gauge)
    "nutricion":        "\uE8BE",   # Leaf
    "entrenamiento":    "\uE805",   # Walk
    "explicacion":      "\uEA80",   # Lightbulb
    "configuracion":    "\uE713",   # Settings
    "perfil":           "\uE77B",   # Contact
    "personas":         "\uE716",   # People
    "salir":            "\uF3B1",   # SignOut
    "guardar":          "\uE74E",   # Save
    "descargar":        "\uE896",   # Download
    "exportar":         "\uEDE1",   # Export
    "imprimir":         "\uE749",   # Print
    "ver":              "\uE890",   # View
    "ocultar":          "\uED1A",   # Hide
    "candado":          "\uE72E",   # Lock
    "check":            "\uE73E",   # CheckMark
    "agregar":          "\uE710",   # Add
    "cerrar":           "\uE711",   # Cancel
    "volver":           "\uE72B",   # Back
    "siguiente":        "\uE72A",   # Forward
    "alerta":           "\uE7BA",   # Warning
    "critico":          "\uEA39",   # ErrorBadge
    "info":             "\uE946",   # Info
    "corazon":          "\uEB51",   # Heart
    "agua":             "\uEB42",   # Drop
    "calendario":       "\uE787",   # Calendar
    "cronometro":       "\uE916",   # Stopwatch
    "estrella":         "\uE734",   # FavoriteStar
    "escudo":           "\uEA18",   # Shield
    "campana":          "\uEA8F",   # Ringer
    "grafico":          "\uE9D2",   # AreaChart
    "reloj":            "\uE917",   # Clock
    "flecha_der":       "\uE76C",   # ChevronRight
    "flecha_izq":       "\uE76B",   # ChevronLeft
    "flecha_abajo":     "\uE70D",   # ChevronDown
    "editar":           "\uE70F",   # Edit
    "actualizar":       "\uE72C",   # Refresh
    "salud":            "\uE95E",   # Health
    "libro":            "\uE8F1",   # Library
    "diagnostico":      "\uE9D9",   # Diagnostic
    "check_circulo":    "\uF13E",   # StatusCircleCheckmark
    "documento":        "\uE8A5",   # Document
    "pagina":           "\uE7C3",   # Page
    "calculadora":      "\uE8EF",   # Calculator
    "usuario_agregar":  "\uE8FA",   # AddFriend
    "mapa":             "\uE707",   # MapPin
    "flag":             "\uE7C1",   # Flag
}

# Respaldo MDL2 (misma semántica; solo claves existentes en la fuente MDL2)
FLUENT_MDL2 = {
    "inicio":        "\uE80F",   # Home            (MDL2: Home)
    "menu":          "\uE700",   # GlobalNavButton (MDL2: GlobalNavButton)
    "evaluacion":    "\uE9D9",   # Diagnostic      (MDL2: no ClipboardList)
    "plan":          "\uE8A5",   # Document         (MDL2: Document)
    "historial":     "\uE81C",   # History          (MDL2: History)
    "progreso":      "\uEC4A",   # SpeedHigh        (MDL2: SpeedHigh)
    "nutricion":     "\uE8BE",   # Leaf             (MDL2: Leaf)
    "entrenamiento": "\uE805",   # Walk             (MDL2: Walk)
    "explicacion":   "\uEA80",   # Lightbulb        (MDL2: Lightbulb)
    "configuracion": "\uE713",   # Settings         (MDL2: Settings)
    "perfil":        "\uE77B",   # Contact          (MDL2: Contact)
    "personas":      "\uE716",   # People           (MDL2: People)
    "salir":         "\uF3B1",   # SignOut          (MDL2: SignOut)
    "guardar":       "\uE74E",   # Save             (MDL2: Save)
    "descargar":     "\uE896",   # Download         (MDL2: Download)
    "exportar":      "\uEDE1",   # Export           (MDL2: Export)
    "imprimir":      "\uE749",   # Print            (MDL2: Print)
    "ver":           "\uE890",   # View             (MDL2: View)
    "ocultar":       "\uED1A",   # Hide             (MDL2: Hide)
    "candado":       "\uE72E",   # Lock             (MDL2: Lock)
    "check":         "\uE73E",   # CheckMark        (MDL2: CheckMark)
    "agregar":       "\uE710",   # Add              (MDL2: Add)
    "cerrar":        "\uE711",   # Cancel           (MDL2: Cancel)
    "volver":        "\uE72B",   # Back             (MDL2: Back)
    "siguiente":     "\uE72A",   # Forward          (MDL2: Forward)
    "alerta":        "\uE7BA",   # Warning          (MDL2: Warning)
    "critico":       "\uEA39",   # ErrorBadge       (MDL2: ErrorBadge)
    "info":          "\uE946",   # Info             (MDL2: Info)
    "corazon":       "\uEB51",   # Heart            (MDL2: Heart)
    "agua":          "\uEB42",   # Drop             (MDL2: Drop)
    "calendario":    "\uE787",   # Calendar         (MDL2: Calendar)
    "cronometro":    "\uE916",   # Stopwatch        (MDL2: Stopwatch)
    "estrella":      "\uE734",   # FavoriteStar     (MDL2: FavoriteStar)
    "escudo":        "\uEA18",   # Shield           (MDL2: Shield)
    "campana":       "\uEA8F",   # Ringer           (MDL2: Ringer)
    "grafico":       "\uE9D2",   # AreaChart        (MDL2: AreaChart)
    "reloj":         "\uE917",   # Clock            (MDL2: Clock)
    "flecha_der":    "\uE76C",   # ChevronRight     (MDL2: ChevronRight)
    "flecha_izq":    "\uE76B",   # ChevronLeft      (MDL2: ChevronLeft)
    "flecha_abajo":  "\uE70D",   # ChevronDown      (MDL2: ChevronDown)
    "editar":        "\uE70F",   # Edit             (MDL2: Edit)
    "actualizar":    "\uE72C",   # Refresh          (MDL2: Refresh)
    "salud":         "\uE95E",   # Health           (MDL2: Health)
    "libro":         "\uE8F1",   # Library          (MDL2: Library)
    "diagnostico":   "\uE9D9",   # Diagnostic       (MDL2: Diagnostic)
    "check_circulo": "\uF13E",   # StatusCircle...  (MDL2: no verificado)
    "documento":     "\uE8A5",   # Document         (MDL2: Document)
    "pagina":        "\uE7C3",   # Page             (MDL2: Page)
    "calculadora":   "\uE8EF",   # Calculator       (MDL2: Calculator)
    "usuario_agregar": "\uE8FA", # AddFriend        (MDL2: AddFriend)
    "mapa":          "\uE707",   # MapPin           (MDL2: MapPin)
    "flag":          "\uE7C1",   # Flag             (MDL2: Flag)
}


# ──────────────────────────────────────────────
#  Iconografía web — SVG de trazo propio (24×24)
#  Conjunto consistente tipo "feather": stroke=2,
#  terminaciones redondeadas, color heredado currentColor.
# ──────────────────────────────────────────────

def _ic(inner: str) -> str:
    """Envuelve el interior de un icono SVG de 24×24."""
    return (f'<svg viewBox="0 0 24 24" width="24" height="24" fill="none" '
            f'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            f'stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg">{inner}</svg>')


ICONS = {
    "inicio": _ic('<polyline points="2.5 11 12 3.5 21.5 11"/><path d="M6 9.5V21h12V9.5"/>'
                  '<path d="M9.5 21v-6h5v6"/>'),

    "dashboard": _ic('<rect x="3" y="3" width="7.5" height="7.5" rx="1.6"/>'
                     '<rect x="13.5" y="3" width="7.5" height="7.5" rx="1.6"/>'
                     '<rect x="3" y="13.5" width="7.5" height="7.5" rx="1.6"/>'
                     '<rect x="13.5" y="13.5" width="7.5" height="7.5" rx="1.6"/>'),

    "evaluacion": _ic('<path d="M8 4.2h2.4a3 3 0 0 1 3.2 0H16a2 2 0 0 1 2 2v13a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2v-13a2 2 0 0 1 2-2Z"/>'
                      '<path d="M8 2.8h2.2a1.6 1.6 0 0 0 3.2 0H16a1.2 1.2 0 0 1 1.2 1.2"/>'
                      '<path d="M8.5 11h7M8.5 15h5"/>'),

    "plan": _ic('<path d="M13.5 2.5H6.5a2 2 0 0 0-2 2v15a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2V8z"/>'
                '<path d="M13.5 2.5V8H19"/>'
                '<path d="M8.5 12.5h7M8.5 16h4.5"/>'),

    "historial": _ic('<path d="M3.5 3.5V8h4.5"/>'
                     '<path d="M3.8 13a8.2 8.2 0 1 0 2.3-6L3.5 8"/>'
                     '<path d="M12 7.5V12l3 1.8"/>'),

    "progreso": _ic('<polyline points="2.5 20.5 9 14 13 18 21.5 9"/>'
                    '<polyline points="15.5 9 21.5 9 21.5 15"/>'),

    "nutricion": _ic('<path d="M11 20A6.5 6.5 0 0 1 9.8 7.3C15 6 17 4.9 19 2.5c1 1.9 2 4.2 2 7.5 0 5.2-4.5 10-10 10Z"/>'
                     '<path d="M2 21.5c0-2.8 1.9-5.2 5.4-6C9.7 15 12 13.7 13.2 12.6"/>'),

    "entrenamiento": _ic('<rect x="2" y="7.6" width="2.8" height="8.8" rx="1.2"/>'
                         '<rect x="19.2" y="7.6" width="2.8" height="8.8" rx="1.2"/>'
                         '<rect x="5.6" y="5.4" width="2" height="13.2" rx="1"/>'
                         '<rect x="16.4" y="5.4" width="2" height="13.2" rx="1"/>'
                         '<line x1="7.7" y1="12" x2="16.3" y2="12"/>'),

    "explicacion": _ic('<path d="M9.5 18.5h5"/>'
                       '<path d="M10.5 21.5h3"/>'
                       '<path d="M15.2 14.2c.16-.9.6-1.65 1.35-2.4A4.5 4.5 0 0 0 18 8a6 6 0 0 0-12 0c0 1 .2 2.1 1.4 3.3.3.3.65.65.88 1.2.14.36.22.74.22 1.1 0 .4.1.8.4 1.05v1.15"/>'),

    "configuracion": _ic('<line x1="4" y1="21" x2="4" y2="14.5"/><line x1="4" y1="10.5" x2="4" y2="3"/>'
                         '<line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/>'
                         '<line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/>'
                         '<line x1="1.5" y1="14.5" x2="6.5" y2="14.5"/>'
                         '<line x1="9.5" y1="8" x2="14.5" y2="8"/>'
                         '<line x1="17.5" y1="16" x2="22.5" y2="16"/>'),

    "perfil": _ic('<circle cx="12" cy="8" r="4.2"/>'
                  '<path d="M4.5 21v-1.5a5.5 5.5 0 0 1 5.5-5.5h4a5.5 5.5 0 0 1 5.5 5.5V21"/>'),

    "salir": _ic('<path d="M9.5 21H5.5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>'
                 '<polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>'),

    "guardar": _ic('<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>'
                   '<polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>'),

    "descargar": _ic('<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>'
                     '<polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>'),

    "ver": _ic('<path d="M1.5 12s3.8-7.5 10.5-7.5S22.5 12 22.5 12s-3.8 7.5-10.5 7.5S1.5 12 1.5 12z"/>'
               '<circle cx="12" cy="12" r="3"/>'),

    "ocultar": _ic('<path d="M17.9 17.9A10.1 10.1 0 0 1 12 19.5C5.3 19.5 1.5 12 1.5 12a18.4 18.4 0 0 1 5-5.9"/>'
                   '<path d="M9.9 4.3A9.1 9.1 0 0 1 12 4.5c6.7 0 10.5 7.5 10.5 7.5a18.5 18.5 0 0 1-2.2 3.2"/>'
                   '<line x1="1.5" y1="1.5" x2="22.5" y2="22.5"/><line x1="9.5" y1="9.5" x2="9.2" y2="9.8"/>'),

    "candado": _ic('<rect x="3.5" y="11" width="17" height="10.5" rx="2.2"/>'
                   '<path d="M7.5 11V7a4.5 4.5 0 0 1 9 0v4"/>'),

    "check": _ic('<polyline points="20 6.5 9.5 17 4 11.5"/>'),

    "agregar": _ic('<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>'),

    "alerta": _ic('<path d="M10.3 3.9 1.9 18a2 2 0 0 0 1.7 3h16.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/>'
                  '<line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>'),

    "critico": _ic('<path d="M7.9 2.5h8.2L21.5 7.9v8.2l-5.4 5.4H7.9L2.5 16.1V7.9z"/>'
                   '<line x1="12" y1="8" x2="12" y2="12.5"/><line x1="12" y1="16" x2="12.01" y2="16"/>'),

    "info": _ic('<circle cx="12" cy="12" r="9.5"/><line x1="12" y1="16.5" x2="12" y2="11.5"/>'
                '<line x1="12" y1="8" x2="12.01" y2="8"/>'),

    "corazon": _ic('<path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8l1.1 1L12 21.2l7.7-7.8 1.1-1a5.5 5.5 0 0 0 0-7.8z"/>'),

    "agua": _ic('<path d="M12 2.7 17.7 8.4a8 8 0 1 1-11.4 0z"/>'),

    "calendario": _ic('<rect x="3.5" y="4.5" width="17" height="17" rx="2.5"/>'
                      '<line x1="16" y1="2.5" x2="16" y2="6.5"/>'
                      '<line x1="8" y1="2.5" x2="8" y2="6.5"/>'
                      '<line x1="3.5" y1="10" x2="20.5" y2="10"/>'),

    "cronometro": _ic('<circle cx="12" cy="13" r="8"/>'
                      '<line x1="12" y1="9.5" x2="12" y2="13.5"/><line x1="15" y1="15.5" x2="14.2" y2="14.7"/>'
                      '<line x1="9" y1="2.5" x2="15" y2="2.5"/><line x1="12" y1="2.5" x2="12" y2="5"/>'),

    "estrella": _ic('<polygon points="12 3 14.7 8.8 21 9.6 16.3 14 17.6 20.3 12 17.2 6.4 20.3 7.7 14 3 9.6 9.3 8.8"/>'),

    "escudo": _ic('<path d="M12 22s8-4 8-10V5.5L12 2.5 4 5.5V12c0 6 8 10 8 10z"/>'),

    "campana": _ic('<path d="M18 8.5a6 6 0 1 0-12 0c0 6.5-2 7.5-2 7.5h16s-2-1-2-7.5"/>'
                   '<path d="M9.5 19a2.5 2.5 0 0 0 5 0"/>'),

    "grafico": _ic('<path d="M3.5 3.5v17h17"/>'
                   '<path d="M7.5 16.5l3.5-4.5 3 2.5 5-6.5"/>'),

    "reloj": _ic('<circle cx="12" cy="12" r="9.5"/><polyline points="12 6.8 12 12 15.5 14.2"/>'),

    "flecha_der": _ic('<polyline points="9 18 15 12 9 6"/>'),

    "flecha_abajo": _ic('<polyline points="6 9 12 15 18 9"/>'),

    "editar": _ic('<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>'
                  '<path d="M18.5 2.5a2.1 2.1 0 0 1 3 3L12 15l-4 1 1-4z"/>'),

    "actualizar": _ic('<path d="M23 4.5v6h-6"/>'
                      '<path d="M1 19.5v-6h6"/>'
                      '<path d="M3.5 9a9 9 0 0 1 14.9-3.4L23 10.5"/>'
                      '<path d="M1 13.5l4.6 4.4A9 9 0 0 0 20.5 15"/>'),

    "salud": _ic('<path d="M3 12h4l2.5-6 4 12 2.5-6h5"/>'),

    "libro": _ic('<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>'
                 '<path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>'),

    "personas": _ic('<circle cx="9" cy="8.5" r="3.5"/>'
                    '<path d="M2.5 21v-1.5a5 5 0 0 1 5-5h3a5 5 0 0 1 5 5V21"/>'
                    '<path d="M16.2 5.2a3.5 3.5 0 0 1 0 6.6"/>'
                    '<path d="M18 14.5a5 5 0 0 1 3.5 4.8V21"/>'),

    "objetivo": _ic('<circle cx="12" cy="12" r="9.5"/><circle cx="12" cy="12" r="5.2"/>'
                    '<circle cx="12" cy="12" r="1"/>'),

    "menu": _ic('<line x1="3.5" y1="6" x2="20.5" y2="6"/>'
                '<line x1="3.5" y1="12" x2="20.5" y2="12"/>'
                '<line x1="3.5" y1="18" x2="20.5" y2="18"/>'),

    "notas": _ic('<path d="M7 3.5h10a1.5 1.5 0 0 1 1.5 1.5v14a1.5 1.5 0 0 1-1.5 1.5H7A1.5 1.5 0 0 1 5.5 19V5A1.5 1.5 0 0 1 7 3.5z"/>'
                 '<path d="M8.5 8h7M8.5 12h7M8.5 16h4"/>'),

    "risa": _ic('<circle cx="12" cy="12" r="9.5"/>'
                '<path d="M8.5 14.5a4.6 4.6 0 0 0 7 0"/>'
                '<path d="M9 9h.01M15 9h.01"/>'),

    "pulso": _ic('<path d="M2.5 12h4.2l2.4-6 4.6 12 2.4-6h5.4"/>'),

    "bandera": _ic('<path d="M4.5 21.5v-18"/>'
                   '<path d="M4.5 4.5c3-1.8 6 .6 8.5-.5 1.8-.8 3.4-.7 6.5.5v9c-3-1.4-5.5.3-7.5.8-2.4.6-4.7-1-7.5-1.3"/>'),
}


def icon_svg(name: str, size: int = 18, color: str = "currentColor",
             stroke: float = 2.0, cls: str = "") -> str:
    """Devuelve el SVG del icono web con tamaño/color/estilo configurable."""
    svg = ICONS.get(name, ICONS["info"])
    return svg.replace('width="24" height="24" stroke-width="2"',
                       f'width="{size}" height="{size}" stroke-width="{stroke}"'
                       ).replace('</svg>', f' style="color:{color};flex:none;" class="{cls}"></svg>')


def brand_svg(size: int = 40, with_name: bool = True) -> str:
    """Logotipo FitExpert en SVG (marca + nombre) para interfaces web."""
    mark = (f'<svg viewBox="0 0 48 48" width="{size}" height="{size}" '
            f'xmlns="http://www.w3.org/2000/svg" style="flex:none;">'
            f'<defs><linearGradient id="fxg" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" stop-color="#2DD4BF"/><stop offset="1" stop-color="#0EA5E9"/>'
            f'</linearGradient></defs>'
            f'<rect x="2" y="2" width="44" height="44" rx="13" fill="url(#fxg)"/>'
            f'<path d="M15 17h5.5a7 7 0 0 1 0 14H15z" fill="#07222A" opacity=".92"/>'
            f'<path d="M33 17H27.5a7 7 0 0 0 0 14H33z" fill="#07222A" opacity=".92"/>'
            f'<path d="M15 17l18 14M33 17L15 31" stroke="#2DD4BF" stroke-width="3.2" '
            f'stroke-linecap="round"/></svg>')
    if not with_name:
        return mark
    return (f'<span style="display:inline-flex;align-items:center;gap:10px;">{mark}'
            f'<span style="font-family:{FONT_FAMILY_WEB};font-weight:700;'
            f'font-size:{size*0.55:.0f}px;color:{TEXT};letter-spacing:-0.01em;">'
            f'Fit<span style="color:{PRIMARY};">Expert</span></span></span>')


# ──────────────────────────────────────────────
#  Helpers de estado (web)
# ──────────────────────────────────────────────

_CHIP_BG = {
    "info":    ACCENT_SOFT,
    "ok":      "#0E3A2A",
    "warn":    "#3A2E0E",
    "danger":  "#3A1414",
    "crit":    "#421112",
    "violet":  "#2A1F4A",
    "gold":    "#3A2E0E",
    "primary": PRIMARY_SOFT,
    "muted":   BG_ELEV_2,
}

def chip_html(text: str, kind: str = "muted", *, outline: bool = False) -> str:
    """Chip de estado (pill) con doble codificación color + etiqueta."""
    bg = _CHIP_BG.get(kind, BG_ELEV_2)
    color = {"info": ACCENT, "ok": SUCCESS, "warn": WARNING, "danger": DANGER,
             "crit": CRITICAL, "violet": VIOLET, "gold": GOLD, "primary": PRIMARY,
             "muted": TEXT_MUTED}.get(kind, TEXT_MUTED)
    border = f"1px solid {color}55" if not outline else f"1px solid {color}"
    return (f'<span class="fx-chip" style="background:{bg};color:{color};'
            f'border:{border};">{text}</span>')


def badge_html(severity: str, tier: str = "") -> str:
    """Badge web de severidad (+ tier) con icono SVG y doble codificación."""
    sev = severity_style(severity)
    parts = [
        f'<span class="fx-chip" style="background:{_CHIP_BG.get(severity, BG_ELEV_2)};'
        f'color:{sev["color"]};border:1px solid {sev["color"]}55;">'
        f'{icon_svg({"critica": "critico", "alta": "alerta", "media": "info",
                      "baja": "check", "info": "info"}.get(severity, "info"), 12, sev["color"], 2.4)}&nbsp;'
        f'{sev["label"].upper()}</span>'
    ]
    if tier:
        ts = tier_style(tier)
        parts.append(
            f'<span class="fx-chip" style="background:{_CHIP_BG.get("violet", BG_ELEV_2)};'
            f'color:{ts["color"]};border:1px solid {ts["color"]}55;">{ts["icon"]}&nbsp;{ts["label"].upper()}</span>'
        )
    return "&nbsp;".join(parts)


def alert_html(kind: str, title: str, body: str) -> str:
    """Alerta web informativa con icono SVG (info/warn/danger/success/violet)."""
    icon = {"danger": "critico", "warn": "alerta", "info": "info",
            "success": "check", "violet": "explicacion"}.get(kind, "info")
    return (f'<div class="fx-alert fx-alert--{kind}" role="alert">'
            f'{icon_svg(icon, 20, "currentColor", 2)}'
            f'<div><b>{title}</b>{"<br>" + body if body else ""}</div></div>')


# ──────────────────────────────────────────────
#  Ayudas de consola (rich/Colorama)
# ──────────────────────────────────────────────

CONSOLE = {
    "primary":  f"bold {PRIMARY}",
    "accent":   f"bold {ACCENT}",
    "info":     f"bold {INFO}",
    "warn":     f"bold {WARNING}",
    "danger":   f"bold {CRITICAL}",
    "success":  f"bold {SUCCESS}",
    "muted":    f"dim {TEXT_MUTED}",
    "text":     TEXT,
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


# ──────────────────────────────────────────────
#  CSS web compartido (gui.py) — estética SaaS premium
# ──────────────────────────────────────────────

_CSS_ROOT = f"""
:root {{
    --fx-bg:        {BG};
    --fx-bg-elev:   {BG_ELEV};
    --fx-bg-2:      {BG_ELEV_2};
    --fx-bg-3:      {BG_ELEV_3};
    --fx-border:    {BORDER};
    --fx-border-2:  {BORDER_STRONG};
    --fx-primary:   {PRIMARY};
    --fx-primary-h: {PRIMARY_HOV};
    --fx-primary-soft: {PRIMARY_SOFT};
    --fx-acc:       {ACCENT};
    --fx-info:      {INFO};
    --fx-warn:      {WARNING};
    --fx-danger:    {DANGER};
    --fx-crit:      {CRITICAL};
    --fx-ok:        {SUCCESS};
    --fx-violet:    {VIOLET};
    --fx-gold:      {GOLD};
    --fx-text:      {TEXT};
    --fx-muted:     {TEXT_MUTED};
    --fx-faint:     {TEXT_FAINT};
    --fx-font:      {FONT_FAMILY_WEB};
    --fx-mono:      {FONT_FAMILY_MONO};
}}
"""

_CSS_BODY = """
/* ── Base ────────────────────────────────────────── */
.stApp {
    background:
        radial-gradient(1100px 500px at 85% -10%, rgba(45,212,191,0.07), transparent 60%),
        radial-gradient(900px 460px at -10% 8%, rgba(61,156,255,0.06), transparent 55%),
        var(--fx-bg);
    color: var(--fx-text);
    font-family: var(--fx-font);
    -webkit-font-smoothing: antialiased;
}
html, body, .stApp { background: var(--fx-bg); }
.block-container { max-width: 1060px; padding-top: 1.1rem; padding-bottom: 4rem; }
#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }
[data-testid="stToolbar"] { display: none; }
::selection { background: var(--fx-primary-soft); color: var(--fx-text); }
* { transition: color 120ms ease, background-color 120ms ease, border-color 120ms ease; }

/* Streamlit inyecta su propia fuente ("Source Sans") después de nuestros
 * estilos; reforzamos la tipografía de marca con precedencia para que la
 * identidad se mantenga en todos los controles nativos. */
html, body, .stApp, [data-testid="stApp"], .block-container,
div, p, h1, h2, h3, h4, h5, h6, span, label, li, td, th, a,
button, input, textarea, select, legend, small, strong, em {
    font-family: var(--fx-font) !important;
}

::-webkit-scrollbar { width: 9px; height: 9px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--fx-bg-3); border-radius: 8px; border: 2px solid var(--fx-bg); }
::-webkit-scrollbar-thumb:hover { background: var(--fx-border-2); }

/* ── Tipografía de producto ──────────────────────── */
.fx-kicker { font-size: .72rem; font-weight: 700; letter-spacing: .14em;
             text-transform: uppercase; color: var(--fx-primary); margin-bottom: .35rem; }
.fx-hero { font-size: 2.05rem; font-weight: 800; letter-spacing: -0.02em;
           line-height: 1.12; margin: 0 0 .3rem; }
.fx-hero .tint { color: var(--fx-primary); }
.fx-sub { color: var(--fx-muted); font-size: .98rem; margin: 0 0 1.3rem; line-height: 1.55; }
.fx-h1 { font-size: 1.45rem; font-weight: 750; letter-spacing: -.01em; margin: 0; }
.fx-top-bar { display: flex; align-items: center; gap: .85rem; margin: .1rem 0 1.1rem; }
.fx-top-ic { width: 44px; height: 44px; border-radius: 13px; flex: none;
             display: inline-flex; align-items: center; justify-content: center;
             background: var(--fx-primary-soft); color: var(--fx-primary);
             box-shadow: inset 0 0 0 1px rgba(45,212,191,.25); }
.fx-footer { margin-top: 2.2rem; color: var(--fx-faint); font-size: .72rem;
             line-height: 1.6; text-align: center; }
.fx-h2 { font-size: 1.05rem; font-weight: 700; margin: 0 0 .35rem; color: var(--fx-text); }
.fx-muted { color: var(--fx-muted); }
.fx-small { font-size: .8rem; color: var(--fx-muted); }
.fx-mono { font-family: var(--fx-mono) !important; }
code, pre, kbd { font-family: var(--fx-mono) !important; }
.fx-center { text-align: center; }

/* ── Tarjetas ────────────────────────────────────── */
.fx-card {
    background: var(--fx-bg-elev);
    border: 1px solid var(--fx-border);
    border-radius: 16px;
    padding: 1.05rem 1.2rem;
    margin-bottom: .9rem;
    position: relative;
    box-shadow: 0 1px 0 rgba(255,255,255,.02) inset;
}
.fx-card--accent { border-top: 2px solid var(--fx-primary); }
.fx-card--soft   { background: var(--fx-bg-2); border-style: dashed; }
.fx-card--dim    { background: transparent; }
.fx-card h3 { margin: 0 0 .25rem; font-size: .95rem; font-weight: 700; }
.fx-card p  { margin: .2rem 0; color: var(--fx-muted); font-size: .86rem; line-height: 1.5; }

/* ── Métricas y bandas ───────────────────────────── */
.fx-band {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: .8rem; margin: .2rem 0 1rem;
}
.fx-metric {
    background: var(--fx-bg-elev);
    border: 1px solid var(--fx-border);
    border-radius: 16px;
    padding: .95rem 1rem;
    text-align: center;
    animation: fx-rise .34s ease both;
}
.fx-metric:hover { border-color: var(--fx-border-2); transform: translateY(-1px); }
.fx-metric .l { color: var(--fx-muted); font-size: .7rem; text-transform: uppercase;
                letter-spacing: .08em; font-weight: 600; }
.fx-metric .v { font-size: 1.85rem; font-weight: 800; line-height: 1.05;
                letter-spacing: -.02em; }
.fx-metric .s { color: var(--fx-faint); font-size: .72rem; margin-top: .2rem; }
.fx-metric .ic { display: block; margin: 0 auto .3rem; }

/* ── Chips / badges ──────────────────────────────── */
.fx-chip { display: inline-flex; align-items: center; gap: .3rem;
           padding: .18rem .62rem; border-radius: 999px;
           font-size: .72rem; font-weight: 700; letter-spacing: .03em;
           white-space: nowrap; }

/* ── Alertas ─────────────────────────────────────── */
.fx-alert { display: flex; gap: .7rem; align-items: flex-start;
            padding: .85rem 1rem; border-radius: 14px; margin-bottom: .9rem;
            font-size: .88rem; line-height: 1.5; border: 1px solid; }
.fx-alert b { display: block; margin-bottom: .05rem; }
.fx-alert--danger { background: rgba(255,74,74,.09); border-color: rgba(255,74,74,.4); color: #FECACA; }
.fx-alert--warn   { background: rgba(245,185,68,.08); border-color: rgba(245,185,68,.38); color: #FBE3B0; }
.fx-alert--info   { background: rgba(61,156,255,.08); border-color: rgba(61,156,255,.35); color: #C9E0FF; }
.fx-alert--success{ background: rgba(63,211,154,.08); border-color: rgba(63,211,154,.35); color: #C4F2E1; }
.fx-alert--violet { background: rgba(167,139,250,.08); border-color: rgba(167,139,250,.35); color: #E2D8FF; }

/* ── Stepper ─────────────────────────────────────── */
.fx-stepper { display: flex; align-items: center; gap: .45rem; margin: .4rem 0 1.2rem; }
.fx-step { flex: 1; display: flex; align-items: center; justify-content: center; gap: .4rem;
           padding: .5rem .4rem; border-radius: 12px; background: var(--fx-bg-elev);
           border: 1px solid var(--fx-border); color: var(--fx-muted);
           font-size: .76rem; font-weight: 650; white-space: nowrap; }
.fx-step .n { width: 20px; height: 20px; border-radius: 50%; display: inline-flex;
              align-items: center; justify-content: center; font-size: .68rem;
              background: var(--fx-bg-3); color: var(--fx-muted); font-weight: 700; }
.fx-step.active { background: var(--fx-primary-soft); border-color: var(--fx-primary);
                  color: var(--fx-text); }
.fx-step.active .n { background: var(--fx-primary); color: #06251F; }
.fx-step.done { border-color: var(--fx-ok); color: var(--fx-ok); }
.fx-step.done .n { background: var(--fx-ok); color: #04281C; }
@media (max-width: 720px) { .fx-step span.lbl { display: none; } }

/* ── Barras de progreso / macros ─────────────────── */
.fx-track { height: 8px; border-radius: 99px; background: var(--fx-bg-3);
            overflow: hidden; margin-top: .45rem; }
.fx-fill { height: 100%; border-radius: 99px; background: var(--fx-primary);
           transition: width .7s cubic-bezier(.22,1,.36,1); }
.fx-macro { margin-bottom: .8rem; }
.fx-macro .row { display: flex; justify-content: space-between; font-size: .84rem; }
.fx-macro .row b { color: var(--fx-text); }

/* ── Tarjetas de regla / explicación ─────────────── */
.fx-rule { display: flex; gap: .9rem; background: var(--fx-bg-elev);
           border: 1px solid var(--fx-border); border-radius: 14px;
           padding: .9rem 1rem; margin-bottom: .7rem; animation: fx-rise .35s ease both; }
.fx-rule .bar { width: 4px; border-radius: 99px; flex: none; }
.fx-rule .rid { font-family: var(--fx-mono); font-size: .72rem; color: var(--fx-faint);
                margin-bottom: .2rem; }
.fx-rule .concl { color: var(--fx-text); font-weight: 650; font-size: .92rem;
                  line-height: 1.45; }
.fx-rule .exp  { color: var(--fx-muted); font-size: .85rem; line-height: 1.5;
                 margin-top: .3rem; }
.fx-rule .refs { color: var(--fx-faint); font-size: .74rem; margin-top: .35rem;
                 font-family: var(--fx-mono); }
.fx-rule .alt  { margin-top: .45rem; padding: .45rem .7rem; border-radius: 10px;
                 background: rgba(167,139,250,.07); border: 1px dashed rgba(167,139,250,.4);
                 color: #CBBEF7; font-size: .82rem; line-height: 1.45; }

/* ── Entrenamiento ───────────────────────────────── */
.fx-day { background: var(--fx-bg-elev); border: 1px solid var(--fx-border);
          border-radius: 16px; padding: .9rem 1.05rem; margin-bottom: .8rem; }
.fx-day .hd { display: flex; align-items: center; justify-content: space-between;
              margin-bottom: .55rem; }
.fx-day .dayname { font-weight: 800; font-size: .95rem; letter-spacing: .02em; }
.fx-day .grp { color: var(--fx-primary); font-weight: 650; font-size: .84rem; }
.fx-ex { display: flex; align-items: baseline; justify-content: space-between;
         padding: .34rem 0; border-top: 1px dashed var(--fx-border); font-size: .88rem; }
.fx-ex .nm { color: var(--fx-text); }
.fx-ex .dt { color: var(--fx-muted); font-variant-numeric: tabular-nums;
             font-size: .8rem; white-space: nowrap; }
.fx-rest { color: var(--fx-faint); font-size: .76rem; margin-top: .4rem; }

/* ── Tablas de historial ─────────────────────────── */
.fx-table { width: 100%; border-collapse: separate; border-spacing: 0 .4rem; }
.fx-table th { text-align: left; font-size: .68rem; text-transform: uppercase;
               letter-spacing: .1em; color: var(--fx-faint); padding: 0 .75rem; }
.fx-table td { background: var(--fx-bg-elev); border: 1px solid var(--fx-border);
               padding: .7rem .75rem; font-size: .87rem; }
.fx-table tr:first-of-type td { border-radius: 0; }
.fx-table th:first-of-type, .fx-table td:first-of-type { border-top-left-radius: 12px;
               border-bottom-left-radius: 12px; }
.fx-table th:last-of-type, .fx-table td:last-of-type { border-top-right-radius: 12px;
               border-bottom-right-radius: 12px; }

/* ── Estado vacío ────────────────────────────────── */
.fx-empty { text-align: center; padding: 2.6rem 1.4rem; border: 1px dashed var(--fx-border);
            border-radius: 16px; color: var(--fx-muted); background: var(--fx-bg-elev); }
.fx-empty .ic { margin: 0 auto .6rem; }

/* ── Auth / Landing ──────────────────────────────── */
.fx-auth-wrap { min-height: 92vh; display: flex; align-items: center; justify-content: center;
                padding: 1.4rem; }
.fx-auth { display: grid; grid-template-columns: 1.05fr .95fr; width: 100%; max-width: 1060px;
           min-height: 590px; border-radius: 22px; overflow: hidden;
           border: 1px solid var(--fx-border);
           background: var(--fx-bg-elev);
           box-shadow: 0 30px 80px -30px rgba(0,0,0,.75); }
.fx-auth-brand { padding: 2.6rem 2.4rem; display: flex; flex-direction: column;
                 background:
                    radial-gradient(600px 300px at 20% 0%, rgba(45,212,191,.16), transparent 60%),
                    radial-gradient(500px 300px at 100% 100%, rgba(61,156,255,.12), transparent 60%),
                    var(--fx-bg-2);
                 border-right: 1px solid var(--fx-border); }
.fx-auth-brand .tag { margin-top: 1.1rem; color: var(--fx-muted); font-size: 1.4rem;
                      font-weight: 700; letter-spacing: -.01em; line-height: 1.25; }
.fx-auth-brand .tag b { color: var(--fx-primary); }
.fx-auth-brand .desc { color: var(--fx-muted); font-size: .88rem; line-height: 1.6;
                       margin: .6rem 0 1.6rem; }
.fx-prop { display: flex; gap: .8rem; align-items: center; padding: .62rem 0;
           color: var(--fx-text); font-size: .9rem; }
.fx-prop .ic { width: 38px; height: 38px; border-radius: 12px; flex: none;
               display: inline-flex; align-items: center; justify-content: center;
               background: var(--fx-primary-soft); color: var(--fx-primary); }
.fx-auth-brand .foot { margin-top: auto; color: var(--fx-faint); font-size: .76rem;
                       line-height: 1.5; }
.fx-auth-form { padding: 2.4rem 2.6rem; display: flex; flex-direction: column; }
.fx-auth-form .title { font-size: 1.35rem; font-weight: 800; letter-spacing: -.01em;
                       margin-bottom: .25rem; }
.fx-auth-form .hint { color: var(--fx-muted); font-size: .86rem; margin-bottom: 1.3rem; }
.fx-auth-form .ok-note { color: var(--fx-faint); font-size: .76rem; text-align: center;
                         margin-top: .9rem; line-height: 1.5; }
@media (max-width: 920px) { .fx-auth { grid-template-columns: 1fr; }
                            .fx-auth-brand { display: none; } }

/* ── Sidebar ─────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: var(--fx-bg-elev);
    border-right: 1px solid var(--fx-border);
    width: 264px;
}
[data-testid="stSidebarContent"] { padding: 1rem .8rem 1.2rem; }
[data-testid="stSidebar"] .fx-brand { display: flex; align-items: center; gap: .65rem;
    padding: .2rem .4rem .9rem; border-bottom: 1px solid var(--fx-border); margin-bottom: .9rem; }
[data-testid="stSidebar"] .fx-user { display: flex; gap: .7rem; align-items: center;
    background: var(--fx-bg-2); border: 1px solid var(--fx-border);
    border-radius: 14px; padding: .6rem .7rem; margin-bottom: 1rem; }
.fx-avatar { width: 34px; height: 34px; border-radius: 10px; flex: none;
             display: inline-flex; align-items: center; justify-content: center;
             background: linear-gradient(135deg, var(--fx-primary), #0EA5E9);
             color: #06251F; font-weight: 800; font-size: .95rem; }
[data-testid="stSidebar"] .fx-uname { font-weight: 700; font-size: .88rem; }
[data-testid="stSidebar"] .fx-usub { color: var(--fx-faint); font-size: .72rem; }
.fx-nav-label { font-size: .64rem; font-weight: 700; letter-spacing: .16em;
                text-transform: uppercase; color: var(--fx-faint);
                margin: .95rem .4rem .35rem; }

/* Radio convertido en raíl de navegación */
[data-testid="stSidebar"] div[role="radiogroup"] { gap: .2rem; }
[data-testid="stSidebar"] div[role="radiogroup"] label {
    display: flex !important; align-items: center; gap: .6rem;
    background: transparent; border-radius: 11px; padding: .55rem .7rem;
    color: var(--fx-muted) !important; font-weight: 600; font-size: .9rem;
    border-left: 3px solid transparent; cursor: pointer;
    margin: 0; min-height: 40px; transition: all 140ms ease;
}
[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: var(--fx-bg-2); color: var(--fx-text) !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] label[aria-checked="true"] {
    background: var(--fx-primary-soft); color: var(--fx-text) !important;
    border-left: 3px solid var(--fx-primary);
}
[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child,
[data-testid="stSidebar"] div[role="radiogroup"] label p {
    display: none !important; }

/* ── Widgets nativos unificados ──────────────────── */
.stButton > button, .stDownloadButton > button,
[data-testid="stFormSubmitButton"] > button {
    border-radius: 12px; border: 1px solid var(--fx-border);
    background: var(--fx-bg-2); color: var(--fx-text);
    font-weight: 650; font-size: .9rem; padding: .62rem 1rem;
    box-shadow: none; min-height: 44px; transition: all 140ms ease; }
.stButton > button:hover, .stDownloadButton > button:hover {
    border-color: var(--fx-primary); color: var(--fx-text);
    background: var(--fx-bg-3); }
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--fx-primary), #19B8A4);
    border: none; color: #06251F; }
.stButton > button[kind="primary"]:hover {
    filter: brightness(1.08); box-shadow: 0 8px 26px -10px var(--fx-primary); }

.stTextInput input, .stNumberInput input, .stTextArea textarea,
.stDateInput input, [data-testid="stDateInput"] input,
[data-baseweb="select"] > div, [data-baseweb="base-input"],
.stTimeInput input {
    background: var(--fx-bg-2) !important;
    border: 1px solid var(--fx-border) !important;
    border-radius: 10px !important; color: var(--fx-text) !important;
    font-size: .9rem !important; }
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus,
[data-baseweb="select"] > div:focus, [data-testid="stDateInput"] input:focus {
    border-color: var(--fx-primary) !important;
    box-shadow: 0 0 0 3px var(--fx-primary-soft) !important; }
[data-baseweb="popover"] > div {
    background: var(--fx-bg-2) !important; border-color: var(--fx-border) !important;
    border-radius: 12px; }
[data-baseweb="menu"] li { color: var(--fx-text) !important; }
[data-baseweb="menu"] li:hover { background: var(--fx-bg-3) !important; }
[data-baseweb="tag"] { background: var(--fx-primary-soft) !important;
    border-radius: 999px !important; color: var(--fx-primary) !important;
    border-color: var(--fx-primary) !important; }

.stMultiSelect [data-baseweb="select"] > div,
.stSelectbox [data-baseweb="select"] > div { max-height: 44px; }

label[data-testid="stWidgetLabel"] { color: var(--fx-muted) !important;
    font-size: .76rem !important; font-weight: 600 !important; }
div[data-testid="stCaptionContainer"] p, .stCaption { color: var(--fx-faint) !important; }

/* Checkbox como switch */
[data-testid="stCheckbox"] { gap: .5rem; }
[data-testid="stCheckbox"] label { color: var(--fx-muted); font-size: .86rem; }
[data-testid="stCheckbox"] label span { border-radius: 6px; }

/* Tabs */
[data-testid="stTabs"] [data-baseweb="tab-list"] { gap: .45rem;
    border-bottom: 1px solid var(--fx-border); }
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent; border: none; border-radius: 10px;
    padding: .5rem 1.05rem; color: var(--fx-muted); font-weight: 650;
    border-bottom: 2px solid transparent; margin-bottom: -1px; }
[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
    color: var(--fx-primary); border-bottom-color: var(--fx-primary);
    background: var(--fx-primary-soft); }

/* Expander */
details { background: var(--fx-bg-elev) !important; border: 1px solid var(--fx-border) !important;
    border-radius: 14px !important; padding: .3rem 1rem; margin-bottom: .7rem; }
summary { color: var(--fx-text) !important; font-weight: 650; font-size: .9rem; }

/* Alertas nativas (st.error/warning/info/success) */
[data-testid="stAlert"] { border-radius: 14px; border: 1px solid var(--fx-border);
    background: var(--fx-bg-elev) !important; font-size: .88rem; }
[data-testid="stAlert"] [data-testid="stAlertContainer"] p { line-height: 1.5; }

/* Progreso / estado */
[data-testid="stProgress"] > div > div > div:first-child {
    background: var(--fx-bg-3) !important; border-radius: 99px; }
[data-testid="stProgress"] > div > div > div:first-child > div {
    background: var(--fx-primary) !important; border-radius: 99px; }
[data-testid="stStatusWidget"] { background: var(--fx-bg-elev) !important;
    border: 1px solid var(--fx-border); border-radius: 14px; }

.stSpinner { border-top-color: var(--fx-primary) !important; }

/* ── Animaciones ─────────────────────────────────── */
@keyframes fx-rise { from { opacity: 0; transform: translateY(9px); }
                     to   { opacity: 1; transform: translateY(0); } }
.fx-rise { animation: fx-rise .38s ease both; }
.fx-stagger > * { animation: fx-rise .4s ease both; }
.fx-stagger > *:nth-child(2) { animation-delay: .05s; }
.fx-stagger > *:nth-child(3) { animation-delay: .1s; }
.fx-stagger > *:nth-child(4) { animation-delay: .15s; }
.fx-stagger > *:nth-child(5) { animation-delay: .2s; }
.fx-stagger > *:nth-child(6) { animation-delay: .25s; }
@keyframes fx-glow { 0%,100% { box-shadow: 0 0 0 0 rgba(45,212,191,.35); }
                     50%    { box-shadow: 0 0 22px 2px rgba(45,212,191,.28); } }
.fx-pulse { animation: fx-glow 2.4s ease-in-out infinite; }

:focus-visible { outline: 2px solid var(--fx-primary) !important; outline-offset: 2px; }

@media (prefers-reduced-motion: reduce) {
    * { animation: none !important; transition: none !important; }
}

/* ── Responsive ──────────────────────────────────── */
@media (max-width: 900px) {
    .block-container { max-width: 100%; padding: .8rem 1rem 3rem; }
    .fx-hero { font-size: 1.6rem; }
    .fx-band { grid-template-columns: 1fr 1fr; }
}
"""

WEB_CSS = "<style>" + _CSS_ROOT + _CSS_BODY + "</style>"