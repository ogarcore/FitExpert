"""
gui.py
======
FitExpert — Plataforma Web (Streamlit) · v4.0

Producto web completo y conectado de principio a fin:

  Landing / Login / Registro → Sesión → Resumen → Evaluación guiada →
  Plan (nutrición + entrenamiento + explicabilidad) → Historial →
  Evolución → Perfil (cambio de contraseña) → Cerrar sesión.

Un solo sistema de identidad (`design_system`), la misma lógica, reglas,
validaciones, motor, nutrición, entrenamiento y persistencia que la app de
escritorio — y aislamiento real por usuario (cada cuenta ve solo su historial).

Seguridad heredada del núcleo: Argon2id (con migración SHA-256 legada),
rate limiting anti fuerza bruta y mensajes de error humanos (nunca
Tracebacks).
"""

import os
import io
import tempfile
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import streamlit as st

from auth import login, register, change_password
from database import (
    save_profile, get_user_history, get_progress_summary, get_last_session,
    db_stats,
)
from user_profile import (
    UserProfile, OBJECTIVE_LABELS, ACTIVITY_LABELS, EXPERIENCE_LABELS,
    TRAINING_PLACE_LABELS, DIET_TYPES, ALLERGY_OPTIONS, INTOLERANCE_OPTIONS,
    PREFERENCE_OPTIONS, INJURY_OPTIONS, INJURY_SEVERITY_OPTIONS,
    INJURY_RED_FLAGS, EQUIPMENT_OPTIONS,
)
from validation import validate_evaluation, validate_credentials
from knowledge_base import RULES, TIER_LABELS
from inference_engine import InferenceEngine
from nutrition import generate_nutrition_plan
from training import generate_training_plan
from pdf_exporter import export_pdf
import design_system as DS
import exercise_info as EI
import ui_state as US


_ASSETS = Path(__file__).resolve().parent / "assets"
_ICON_FAVICON = str(_ASSETS / "favicon.svg")

_APP_NAME = "FitExpert"
_APP_TAG = "Nutrición y entrenamiento que se explican"
_VERSION = "4.0"

# Fuentes científicas del conocimiento
_SOURCES = ("OMS (WHO)", "CDC", "AAP (Academia Americana de Pediatría)",
            "ACSM (American College of Sports Medicine)")

# ──────────────────────────────────────────────────────────────
#  Estado de sesión
# ──────────────────────────────────────────────────────────────

_WIZARD_STEPS = [
    ("tú",          "Datos personales"),
    ("tu plan",     "Objetivo y nivel"),
    ("tu salud",    "Salud y seguridad"),
    ("tu comida",   "Nutrición"),
    ("revisión",    "Revisión final"),
]


def _defaults() -> None:
    st.session_state.setdefault("fx_user", None)          # {"user_id","username"}
    st.session_state.setdefault("fx_page", "inicio")
    st.session_state.setdefault("fx_step", 1)             # paso del wizard
    st.session_state.setdefault("fx_step_error", None)
    st.session_state.setdefault("fx_results", None)       # {"perfil","plan","rutina","warnings"}
    st.session_state.setdefault("fx_auth_mode", "login")
    st.session_state.setdefault("fx_hist_sel", 0)
    st.session_state.setdefault("fx_note_ok", None)
    st.session_state.setdefault("fx_hi", None)            # mensaje de bienvenida temporal
    st.session_state.setdefault("fx_exercise", None)      # slug del ejercicio elegido (abre ficha)


# ──────────────────────────────────────────────────────────────
#  Utilidades de presentación
# ──────────────────────────────────────────────────────────────

def _css(extra: str = "") -> None:
    st.markdown(DS.WEB_CSS + ("<style>" + extra + "</style>" if extra else ""),
                unsafe_allow_html=True)


def _auth_css() -> None:
    # Ocultar sidebar/header mientras no hay sesión: pantalla de acceso limpia.
    _css("""
    [data-testid="stSidebar"] { display: none; }
    header[data-testid="stHeader"] { display: none; }
    """)


def _top(icon: str, title: str, sub: str) -> None:
    st.markdown(
        f'<div class="fx-top-bar"><span class="fx-top-ic">{DS.icon_svg(icon, 22)}</span>'
        f'<div><div class="fx-h1">{title}</div>'
        f'<div class="fx-sub" style="margin:0">{sub}</div></div></div>',
        unsafe_allow_html=True,
    )


def _chip(text: str, kind: str = "muted") -> str:
    return DS.chip_html(text, kind)


def _empty(icon: str, title: str, body: str, cta_label: str | None = None,
           cta_page: str | None = None) -> None:
    html = (f'<div class="fx-empty"><div class="ic">{DS.icon_svg(icon, 34)}</div>'
            f'<div class="fx-h2">{title}</div><p>{body}</p></div>')
    st.markdown(html, unsafe_allow_html=True)
    if cta_label and cta_page:
        if st.button(cta_label, key=f"cta_{cta_page}", use_container_width=True):
            st.session_state.fx_page = cta_page
            st.rerun()


def _metric(icon: str, label: str, value: str, sub: str, color: str) -> str:
    return (f'<div class="fx-metric"><span class="ic">{DS.icon_svg(icon, 18, color)}</span>'
            f'<div class="l">{label}</div><div class="v" style="color:{color}">{value}</div>'
            f'<div class="s">{sub}</div></div>')


def _imc_color(imc: float) -> str:
    if imc <= 0:
        return DS.TEXT_MUTED
    if imc < 18.5:
        return DS.ACCENT
    if imc < 25:
        return DS.PRIMARY
    if imc < 30:
        return DS.GOLD
    return DS.CRITICAL


def _sev_color(sev: str) -> str:
    return DS.severity_style(sev)["color"]


def _fmt_fecha(ts: str) -> str:
    try:
        return datetime.strptime(ts[:19], "%Y-%m-%d %H:%M:%S").strftime("%d %b %Y")
    except Exception:
        return ts or "—"


def _foot() -> str:
    return (f'<div class="fx-footer" style="margin-top:2.2rem;color:var(--fx-faint);'
            f'font-size:.72rem;line-height:1.6;text-align:center;">'
            f'FitExpert · Motor basado en reglas ({len(RULES)} reglas) · '
            f'Fuentes: {", ".join(_SOURCES)}<br>'
            f'Esto es información orientativa, no sustituye el consejo de un '
            f'profesional de la salud.</div>')


# ──────────────────────────────────────────────────────────────
#  Gráficas (estilo del sistema)
# ──────────────────────────────────────────────────────────────

def _style_ax(ax) -> None:
    ax.set_facecolor(DS.BG_ELEV)
    ax.tick_params(colors=DS.TEXT_MUTED, labelsize=9)
    for spine in ax.spines.values():
        spine.set_color(DS.BORDER)
    ax.yaxis.grid(True, color=DS.BORDER, linewidth=.7, alpha=.6)
    ax.xaxis.grid(False)


def _fig_evolucion(history: list) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(7.4, 3.0), dpi=110)
    fig.patch.set_facecolor(DS.BG_ELEV)
    _style_ax(ax)
    fechas = [_fmt_fecha(h.get("saved_at", "")) for h in history]
    pesos = [h.get("weight", 0) for h in history]
    ax.plot(fechas, pesos, color=DS.PRIMARY, marker="o", linewidth=2.2,
            markersize=5.5, markerfacecolor=DS.BG_ELEV, markeredgewidth=1.6)
    ax.set_ylabel("Peso (kg)", color=DS.TEXT_MUTED, fontsize=9)
    ax.set_ylim(min(pesos) - 3, max(pesos) + 3)
    for lbl in ax.get_xticklabels():
        lbl.set_rotation(18)
    fig.tight_layout(pad=1.2)
    return fig


def _fig_calorias(history: list) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(7.4, 2.7), dpi=110)
    fig.patch.set_facecolor(DS.BG_ELEV)
    _style_ax(ax)
    fechas = [_fmt_fecha(h.get("saved_at", "")) for h in history]
    kcal = [h.get("target_calories", 0) for h in history]
    ax.plot(fechas, kcal, color=DS.ACCENT, marker="o", linewidth=2.2,
            markersize=5.5, markerfacecolor=DS.BG_ELEV, markeredgewidth=1.6)
    ax.set_ylabel("kcal objetivo", color=DS.TEXT_MUTED, fontsize=9)
    for lbl in ax.get_xticklabels():
        lbl.set_rotation(18)
    fig.tight_layout(pad=1.2)
    return fig


# ──────────────────────────────────────────────────────────────
#  Motor / persistencia
# ──────────────────────────────────────────────────────────────

def _run_evaluation(values: dict, warnings: list) -> dict:
    """Ejecuta motor + nutrición + entrenamiento y guarda la sesión."""
    perfil = UserProfile(**values)
    perfil.user_id = st.session_state.fx_user["user_id"]
    perfil.name = st.session_state.fx_user["username"]

    motor = InferenceEngine()
    with st.status("Analizando tu perfil con el motor de reglas…",
                   expanded=True) as sts:
        st.write("Validando 69 reglas IF/THEN de la base de conocimiento…")
        motor.run(perfil)
        st.write("Reglas activadas: %d · Suprimidas: %d"
                 % (len(perfil.conclusions), len(perfil.suppressed)))

        st.write("Construyendo plan nutricional…")
        plan = generate_nutrition_plan(perfil)
        st.write("Montando microciclo semanal de entrenamiento…")
        rutina = generate_training_plan(perfil)
        sts.update(label="Plan generado. Guardando tu historial…", state="complete")

    resultados = {
        "perfil": perfil,
        "plan": plan,
        "rutina": rutina,
        "warnings": warnings or [],
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    # Se persiste también el plan, la rutina y las advertencias para que el
    # plan activo siga disponible tras cerrar/reabrir sesión.
    save_profile(perfil, extra={
        "resultados": {
            "plan": plan,
            "rutina": rutina,
            "warnings": warnings or [],
            "ts": resultados["ts"],
        },
    })
    st.session_state.fx_results = resultados
    st.session_state.fx_step = 1
    # El borrador se considera consumido: la próxima "Nueva evaluación"
    # se vuelve a sembrar desde la última sesión guardada.
    st.session_state.pop("fx_ev", None)
    return resultados


# ──────────────────────────────────────────────────────────────
#  Autenticación
# ──────────────────────────────────────────────────────────────

def _auth_brand_html() -> str:
    props = [
        ("inicio", "Un plan único, construido desde tus datos y objetivos"),
        ("escudo", "Reglas clínicas de fuentes oficiales (OMS, CDC, AAP, ACSM)"),
        ("explicacion", "Cada decisión del motor se muestra y se explica"),
    ]
    items = "".join(
        f'<div class="fx-prop"><span class="ic">{DS.icon_svg(ic, 18, DS.PRIMARY)}</span>'
        f'<span>{t}</span></div>' for ic, t in props)
    return (
        f'<div class="fx-auth-wrap"><div class="fx-auth">'
        f'<div class="fx-auth-brand">'
        f'<div>{DS.brand_svg(46)}</div>'
        f'<div class="tag">Precisión que<br><b>se explica</b></div>'
        f'<div class="desc">FitExpert es un sistema experto de nutrición y '
        f'entrenamiento que genera y explica decisiones personalizadas '
        f'basadas en reglas clínicas.</div>'
        f'{items}'
        f'<div class="foot">Motor de conocimiento: {len(RULES)} reglas IF/THEN · '
        f'7 jerarquías de severidad · Evaluación guiada en 5 pasos.<br>'
        f'Fuentes: {", ".join(_SOURCES)}.</div>'
        f'</div><div class="fx-auth-form">')


def _auth_actions() -> str:
    return "</div></div></div>"


def _render_auth() -> None:
    _auth_css()
    st.markdown(_auth_brand_html(), unsafe_allow_html=True)

    mode = st.session_state.fx_auth_mode
    c1, c2 = st.columns(2)
    with c1:
        st.button("Entrar", key="am_login", use_container_width=True,
                  type="primary" if mode == "login" else "secondary",
                  on_click=lambda: st.session_state.update(fx_auth_mode="login"))
    with c2:
        st.button("Crear cuenta", key="am_register", use_container_width=True,
                  type="primary" if mode == "register" else "secondary",
                  on_click=lambda: st.session_state.update(fx_auth_mode="register"))

    st.markdown('<div style="height:.6rem"></div>', unsafe_allow_html=True)

    if mode == "login":
        st.markdown('<div class="title">Bienvenido de nuevo</div>'
                    '<div class="hint">Accede a tu panel y reevalúa tu plan cuando quieras.</div>',
                    unsafe_allow_html=True)
        u = st.text_input("Usuario", key="au_user", placeholder="Tu nombre de usuario")
        show = st.checkbox("Mostrar contraseña", key="au_show")
        p = st.text_input("Contraseña", key="au_pass", type="password" if not show else "default",
                          placeholder="Tu contraseña")
        st.markdown('<div style="height:.5rem"></div>', unsafe_allow_html=True)
        if st.button("Acceder al panel", key="au_go", use_container_width=True,
                     type="primary"):
            _do_login(u, p)
    else:
        st.markdown('<div class="title">Crea tu cuenta</div>'
                    '<div class="hint">Empieza con tu primera evaluación guiada (10 minutos).</div>',
                    unsafe_allow_html=True)
        u = st.text_input("Nombre de usuario", key="ru_user",
                          placeholder="Sin espacios · mínimo 3 caracteres")
        show1 = st.checkbox("Mostrar contraseñas", key="ru_show")
        p = st.text_input("Contraseña", key="ru_pass", type="password" if not show1 else "default",
                          placeholder="Mínimo 8 caracteres")
        p2 = st.text_input("Confirmar contraseña", key="ru_pass2",
                           type="password" if not show1 else "default",
                           placeholder="Repite tu contraseña")
        st.markdown('<div style="height:.5rem"></div>', unsafe_allow_html=True)
        if st.button("Crear cuenta e iniciar", key="ru_go", use_container_width=True,
                     type="primary"):
            _do_register(u, p, p2)

    st.markdown('<div class="ok-note">Tus datos se almacenan solo en este equipo · '
                'Autenticación con Argon2id · Contraseñas nunca en texto plano.</div>',
                unsafe_allow_html=True)
    st.markdown(_auth_actions(), unsafe_allow_html=True)


def _do_login(u: str, p: str) -> None:
    checked = validate_credentials(u, p)
    if not checked["ok"]:
        st.error(checked["error"])
        return
    res = login(checked["username"], checked["password"])
    if res["ok"]:
        st.session_state.fx_user = {"user_id": res["user_id"],
                                    "username": res["username"]}
        st.session_state.fx_hi = f"Te damos la bienvenida, {res['username']}."
        st.session_state.fx_page = "inicio"
        st.rerun()
    else:
        st.error(res["error"])


def _do_register(u: str, p: str, p2: str) -> None:
    if p != p2:
        st.error("Las contraseñas no coinciden.")
        return
    checked = validate_credentials(u, p, for_register=True)
    if not checked["ok"]:
        st.error(checked["error"])
        return
    res = register(checked["username"], checked["password"])
    if res["ok"]:
        st.session_state.fx_user = {"user_id": res["user_id"],
                                    "username": res["username"]}
        st.session_state.fx_hi = f"Cuenta creada. ¡Bienvenido, {res['username']}!"
        st.session_state.fx_page = "inicio"
        st.rerun()
    else:
        st.error(res["error"])


def _logout() -> None:
    for k in ("fx_user", "fx_results", "fx_page", "fx_hi", "fx_ev"):
        st.session_state.pop(k, None)
    st.session_state.fx_page = "inicio"
    st.session_state.fx_auth_mode = "login"  # tras salir, la pantalla de acceso abre en "Entrar"
    st.rerun()


# ──────────────────────────────────────────────────────────────
#  Navegación lateral (post-login)
# ──────────────────────────────────────────────────────────────

_NAV = [
    ("Resumen", [
        ("inicio", "inicio", "Inicio", "Panel general con tu estado y accesos rápidos"),
    ]),
    ("Planificación", [
        ("evaluacion", "nueva", "Nueva evaluación", "Crea o actualiza tu plan en 5 pasos"),
        ("plan", "plan", "Plan actual", "Nutrición, entrenamiento y decisiones del motor"),
    ]),
    ("Seguimiento", [
        ("historial", "historial", "Historial", "Tus evaluaciones guardadas"),
        ("progreso", "progreso", "Evolución", "Progreso de peso y calorías en el tiempo"),
        ("explicacion", "explicacion", "Lógica del experto", "Por qué se tomaron las decisiones"),
    ]),
    ("Cuenta", [
        ("perfil", "perfil", "Perfil", "Datos de tu cuenta y contraseña"),
        ("libro", "acerca", "Acerca de", "El sistema experto: reglas, fuentes y alcance"),
    ]),
]


def _sidebar(user: dict) -> None:
    with st.sidebar:
        st.markdown(
            f'<div class="fx-brand">{DS.brand_svg(34, with_name=False)}'
            f'<div><div style="font-weight:800;font-size:1.02rem;">Fit'
            f'<span style="color:var(--fx-primary)">Expert</span></div>'
            f'<div style="color:var(--fx-faint);font-size:.66rem;">Nutrición y entrenamiento</div></div></div>',
            unsafe_allow_html=True)
        st.markdown(
            f'<div class="fx-user"><span class="fx-avatar">{user["username"][:1].upper()}</span>'
            f'<div style="min-width:0"><div class="fx-uname">{user["username"]}</div>'
            f'<div class="fx-usub">Sesión activa</div></div></div>',
            unsafe_allow_html=True)

        current = st.session_state.fx_page

        for group, items in _NAV:
            st.markdown(f'<div class="fx-nav-label">{group}</div>',
                        unsafe_allow_html=True)
            for icon, page, label, help_text in items:
                c_ic, c_bt = st.columns([0.82, 5.0])
                active = page == current
                with c_ic:
                    st.markdown(
                        f'<div style="padding-top:.66rem;display:flex;justify-content:center;">'
                        f'{DS.icon_svg(icon, 17, DS.PRIMARY if active else DS.TEXT_MUTED)}</div>',
                        unsafe_allow_html=True)
                with c_bt:
                    st.button(label, key=f"nav_{page}", use_container_width=True,
                              type="primary" if active else "secondary",
                              help=help_text,
                              on_click=lambda p=page: st.session_state.update(fx_page=p),
                              disabled=False)

        st.markdown('<div style="height:.4rem"></div>', unsafe_allow_html=True)
        if st.button("Cerrar sesión", key="nav_salir", use_container_width=True):
            _logout()
        st.markdown('<div style="color:var(--fx-faint);font-size:.66rem;'
                    'text-align:center;margin-top:1rem;">FitExpert v%s</div>' % _VERSION,
                    unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
#  Página: Resumen
# ──────────────────────────────────────────────────────────────

def _load_latest_results(user_id: str) -> dict | None:
    """Reconstruye el plan activo desde la sesión guardada más reciente.

    Tras cerrar/reabrir sesión, `fx_results` ya no está en memoria: se
    recupera el plan persistido (o, para sesiones antiguas sin resultados
    guardados, se regenera de forma determinista desde el perfil).
    """
    last = get_last_session(user_id)
    if not last:
        return None
    perfil = UserProfile.from_dict(last)
    saved = last.get("resultados") or {}
    if saved.get("plan"):
        return {
            "perfil": perfil,
            "plan": saved["plan"],
            "rutina": saved.get("rutina"),
            "warnings": saved.get("warnings") or [],
            "ts": saved.get("ts") or last.get("saved_at", ""),
        }
    return {
        "perfil": perfil,
        "plan": generate_nutrition_plan(perfil),
        "rutina": generate_training_plan(perfil),
        "warnings": [],
        "ts": last.get("saved_at", ""),
    }


def _page_inicio(user: dict) -> None:
    _top("inicio", "Resumen",
         "El estado de tu plan y tu progreso, de un vistazo.")

    if st.session_state.fx_hi:
        st.markdown(DS.alert_html("success", st.session_state.fx_hi, ""),
                    unsafe_allow_html=True)
        st.session_state.fx_hi = None

    resultado = st.session_state.fx_results or _load_latest_results(user["user_id"])
    last = get_last_session(user["user_id"])
    progress = get_progress_summary(user["user_id"])

    # Acceso rápido
    st.markdown(f'<div class="fx-card fx-card--accent fx-rise">'
                f'<h3>{DS.icon_svg("evaluacion", 17, DS.PRIMARY)}&nbsp; Tu evaluación</h3>'
                f'<p>{"Tienes un plan activo generado el " + _fmt_fecha(resultado["perfil"].created_at) if resultado else "Aún no tienes un plan. Tu primera evaluación te dará nutrición, entrenamiento y la explicación de cada decisión."}</p>'
                f'</div>', unsafe_allow_html=True)

    if not last:
        _empty("evaluacion", "Comienza tu transformación",
               "Crea tu primera evaluación guiada: en 5 pasos tendrás un plan "
               "personalizado de nutrición y entrenamiento.",
               "Empezar mi primera evaluación", "nueva")
        st.markdown(_foot(), unsafe_allow_html=True)
        return

    objetivo = OBJECTIVE_LABELS.get(last.get("objective", ""), last.get("objective", "—"))
    st.markdown(
        f'<div class="fx-card fx-card--accent fx-rise"><div class="fx-h2">Tu objetivo actual</div>'
        f'<p>{DS.icon_svg("objetivo", 16, DS.GOLD)}&nbsp; <b>{objetivo}</b> · '
        f'última evaluación {_fmt_fecha(last.get("saved_at", ""))}</p></div>',
        unsafe_allow_html=True)

    delta_p = progress.get("delta_peso_kg", 0.0)
    delta_c = progress.get("delta_calorias", 0.0)
    band = "".join([
        _metric("historial", "Evaluaciones", str(progress.get("sesiones", 0)),
                "sesiones guardadas", DS.ACCENT),
        _metric("progreso", "Variación de peso",
                f"{'+' if delta_p > 0 else ''}{delta_p:.1f} kg",
                "entre primera y última", DS.DANGER if delta_p > 0 else DS.SUCCESS),
        _metric("calendario", "Ajuste calórico",
                f"{'+' if delta_c > 0 else ''}{delta_c:.0f} kcal",
                "objetivo medio", DS.VIOLET),
    ])
    st.markdown(f'<div class="fx-band">{band}</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns([1.4, 1])
    with col_a:
        st.markdown(f'<div class="fx-h2">Tu plan actual</div>', unsafe_allow_html=True)
        if resultado:
            pp = resultado["perfil"]
            pn = resultado["plan"]
            rt = resultado["rutina"]
            macros = pn.get("macros", {})
            imc_cat = _imc_color(pp.imc)
            st.markdown(
                f'<div class="fx-card"><div class="fx-muted" style="font-size:.74rem;">'
                f'Resumen del plan</div>'
                f'<div class="fx-h2" style="margin:.2rem 0 .6rem;">{OBJECTIVE_LABELS.get(pp.objective, pp.objective)}</div>'
                f'<div style="display:flex;gap:.5rem;flex-wrap:wrap;">'
                f'{_chip(f"IMC {pp.imc:.1f}", "primary")}'
                f'{_chip(f"{pp.tdee:.0f} kcal/día", "info")}'
                f'{_chip(rt.get("nombre", "Rutina"), "ok")}'
                f'{_chip(f"{DIET_TYPES.get(pp.diet_type, pp.diet_type)}", "muted")}'
                f'</div>'
                f'<div class="fx-track"><div class="fx-fill" style="width:30%"></div></div>'
                f'<p style="margin-top:.5rem;">Proteínas {macros.get("proteinas", 0)} g · '
                f'Carbohidratos {macros.get("carbohidratos", 0)} g · '
                f'Grasas {macros.get("grasas", 0)} g</p></div>',
                unsafe_allow_html=True)
            if st.button("Ver mi plan completo", key="ds_plan",
                         use_container_width=True):
                st.session_state.fx_page = "plan"
                st.rerun()
        else:
            _empty("plan", "Sin plan activo",
                   "Genera una evaluación para ver aquí tu resumen.",
                   "Crear evaluación", "nueva")

    with col_b:
        st.markdown('<div class="fx-h2">Evolución de peso</div>', unsafe_allow_html=True)
        history = get_user_history(user["user_id"])
        if len(history) >= 2:
            st.pyplot(_fig_evolucion(history), clear_figure=True)
        else:
            _empty("progreso", "Aún no hay curva",
                   "Necesitas al menos 2 evaluaciones para ver tu evolución.")

    if resultado and (resultado["perfil"].red_flags
                      or resultado["perfil"].injury_severity == "aguda"):
        st.markdown(DS.alert_html(
            "danger", "Suspensión de prescripción de ejercicio",
            "Se detectaron señales de alarma o una lesión aguda. FitExpert no "
            "prescribe ejercicio: consulta a un profesional de la salud antes "
            "de retomar la actividad física."), unsafe_allow_html=True)

    st.markdown(_foot(), unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
#  Página: Nueva evaluación (wizard de 5 pasos)
# ──────────────────────────────────────────────────────────────

def _ev_defs(user: dict) -> dict:
    """Valores por defecto del formulario, prellenados con la última sesión."""
    last = get_last_session(user["user_id"]) or {}
    return {
        "ev_name": user["username"],
        "ev_age": last.get("age", 25),
        "ev_sex": "Femenino" if last.get("sex") == "femenino" else "Masculino",
        "ev_weight": float(last.get("weight", 70.0)),
        "ev_height": float(last.get("height", 172.0)),
        "ev_bodyfat": float(last.get("body_fat_pct", 0) or 0.0),
        "ev_objective": OBJECTIVE_LABELS.get(last.get("objective", "mantenimiento"),
                                             list(OBJECTIVE_LABELS.values())[4]),
        "ev_activity": ACTIVITY_LABELS.get(last.get("activity_level", "ligero"),
                                           list(ACTIVITY_LABELS.values())[1]),
        "ev_exp": EXPERIENCE_LABELS.get(last.get("experience", "principiante"),
                                        list(EXPERIENCE_LABELS.values())[0]),
        "ev_place": TRAINING_PLACE_LABELS.get(last.get("training_place", "casa")),
        "ev_equip": [EQUIPMENT_OPTIONS.get(k) for k in (last.get("equipment", []) or [])
                     if k in EQUIPMENT_OPTIONS],
        "ev_freq": f"{last.get('meal_frequency', 3)} comidas",
        "ev_inj": [INJURY_OPTIONS.get(x, x) for x in (last.get("injuries", []) or [])],
        "ev_sev": INJURY_SEVERITY_OPTIONS.get(last.get("injury_severity", "ninguna"),
                                              list(INJURY_SEVERITY_OPTIONS.values())[0]),
        "ev_bal": bool(last.get("balance_issues", False)),
        "ev_rf": [INJURY_RED_FLAGS.get(x, x) for x in (last.get("red_flags", []) or [])],
        "ev_notes": last.get("notes", ""),
        "ev_diet": DIET_TYPES.get(last.get("diet_type", "omnivoro"),
                                  list(DIET_TYPES.values())[0]),
        "ev_alg": [ALLERGY_OPTIONS.get(x, x) for x in (last.get("allergies", []) or [])],
        "ev_int": [INTOLERANCE_OPTIONS.get(x, x) for x in (last.get("intolerances", []) or [])],
        "ev_pref": [PREFERENCE_OPTIONS.get(x, x) for x in (last.get("preferences", []) or [])],
    }


def _stepper_html(step: int) -> str:
    total = len(_WIZARD_STEPS)
    parts = []
    for i, (_, label) in enumerate(_WIZARD_STEPS, 1):
        if i < step:
            inner = DS.icon_svg("check", 11, DS.SUCCESS, 2.6)
            cls = "done"
        elif i == step:
            inner = f'<span class="n">{i}</span>'
            cls = "active"
        else:
            inner = f'<span class="n">{i}</span>'
            cls = ""
        parts.append(f'<div class="fx-step {cls}">{inner}<span class="lbl">{label}</span></div>')
        if i < total:
            parts.append('<div style="width:12px;height:1px;background:var(--fx-border);flex:none;"></div>')
    return '<div class="fx-stepper">' + "".join(parts) + "</div>"


# Claves de widget del asistente por paso. Los widgets con clave se limpian
# de session_state en cuanto dejan de renderizarse, así que antes de cambiar de
# paso absorbemos sus valores al dict durable "fx_ev".
_WIZARD_KEYS = {
    1: ["ev_age", "ev_sex", "ev_weight", "ev_height", "ev_bodyfat"],
    2: ["ev_objective", "ev_exp", "ev_freq", "ev_activity", "ev_place",
        "ev_equip"],
    3: ["ev_inj", "ev_sev", "ev_bal", "ev_rf", "ev_notes"],
    4: ["ev_diet", "ev_alg", "ev_int", "ev_pref"],
    5: ["ev_notes2"],
}


def _ensure_ev(user: dict) -> None:
    """Crea el borrador durable del asistente (fx_ev) y lo siembra una sola vez."""
    fx = st.session_state.setdefault("fx_ev", {})
    if "ev_name" not in fx:
        fx.update(_ev_defs(user))


def _absorb_step(step: int) -> None:
    """Copia los widgets del paso actual a fx_ev antes de abandonarlo."""
    fx = st.session_state.setdefault("fx_ev", {})
    for key in _WIZARD_KEYS.get(step, []):
        if key in st.session_state:
            fx[key] = st.session_state[key]


def _field_source() -> dict:
    """Instancia coherente de los valores del asistente (borrador durable)."""
    return dict(st.session_state.get("fx_ev", {}))


def _page_nueva(user: dict) -> None:
    _top("evaluacion", "Nueva evaluación",
         "Cinco pasos guiados con validación en cada uno. Nada se pierde si cambias de página.")

    # Borrador durable: siembra una sola vez, sobrevive a cambios de página
    _ensure_ev(user)
    fx = st.session_state.fx_ev

    step = st.session_state.fx_step
    st.markdown(_stepper_html(step), unsafe_allow_html=True)

    if st.session_state.fx_step_error:
        st.error(st.session_state.fx_step_error)
        st.session_state.fx_step_error = None

    if step == 1:
        st.markdown('<div class="fx-h2">Datos personales</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.number_input("Edad (años)", 10, 100, step=1, key="ev_age",
                            value=int(fx.get("ev_age", 25)))
            st.number_input("Peso (kg)", 30.0, 300.0, step=0.1, key="ev_weight",
                            value=float(fx.get("ev_weight", 70.0)))
        with c2:
            st.selectbox("Sexo", ["Masculino", "Femenino"], key="ev_sex",
                         index=_opt_index(["Masculino", "Femenino"],
                                          fx.get("ev_sex", "Masculino")))
            st.number_input("Estatura (cm)", 100.0, 250.0, step=0.5, key="ev_height",
                            value=float(fx.get("ev_height", 172.0)))
        st.number_input("Porcentaje de grasa corporal (opcional — 0 si lo desconoces)",
                        0.0, 70.0, step=0.1, key="ev_bodyfat",
                        value=float(fx.get("ev_bodyfat", 0.0) or 0.0))

    elif step == 2:
        st.markdown('<div class="fx-h2">Objetivo y preparación</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.selectbox("Objetivo principal", list(OBJECTIVE_LABELS.values()),
                         key="ev_objective",
                         index=_opt_index(list(OBJECTIVE_LABELS.values()),
                                          fx.get("ev_objective",
                                          list(OBJECTIVE_LABELS.values())[4])))
            st.selectbox("Experiencia", list(EXPERIENCE_LABELS.values()), key="ev_exp",
                         index=_opt_index(list(EXPERIENCE_LABELS.values()),
                                          fx.get("ev_exp",
                                          list(EXPERIENCE_LABELS.values())[0])))
            st.selectbox("Comidas al día", ["3 comidas", "4 comidas", "5 comidas"],
                         key="ev_freq",
                         index=_opt_index(["3 comidas", "4 comidas", "5 comidas"],
                                          fx.get("ev_freq", "3 comidas")))
        with c2:
            st.selectbox("Nivel de actividad diaria", list(ACTIVITY_LABELS.values()),
                         key="ev_activity",
                         index=_opt_index(list(ACTIVITY_LABELS.values()),
                                          fx.get("ev_activity",
                                          list(ACTIVITY_LABELS.values())[1])))
            st.selectbox("Lugar de entrenamiento", list(TRAINING_PLACE_LABELS.values()),
                         key="ev_place",
                         index=_opt_index(list(TRAINING_PLACE_LABELS.values()),
                                          fx.get("ev_place",
                                          TRAINING_PLACE_LABELS["casa"])))
        if st.session_state.get("ev_place") == TRAINING_PLACE_LABELS["casa"]:
            st.multiselect(
                "Equipo disponible en casa",
                list(EQUIPMENT_OPTIONS.values()), key="ev_equip",
                default=_defaults_in(fx.get("ev_equip", []),
                                     list(EQUIPMENT_OPTIONS.values())),
                format_func=lambda x: x)
        else:
            st.session_state.pop("ev_equip", None)
            fx["ev_equip"] = []
            st.caption("Entrenarás en gimnasio: no se requiere listar equipo propio.")

    elif step == 3:
        st.markdown('<div class="fx-h2">Salud y seguridad</div>', unsafe_allow_html=True)
        inj_labels = list(INJURY_OPTIONS.values())
        st.multiselect("Zonas con molestia o lesión", inj_labels, key="ev_inj",
                       default=_defaults_in(fx.get("ev_inj", []), inj_labels))
        st.selectbox("Intensidad de las molestias", list(INJURY_SEVERITY_OPTIONS.values()),
                     key="ev_sev",
                     index=_opt_index(list(INJURY_SEVERITY_OPTIONS.values()),
                                      fx.get("ev_sev",
                                      list(INJURY_SEVERITY_OPTIONS.values())[0])))
        st.checkbox("Problemas de equilibrio / historial de caídas", key="ev_bal",
                    value=bool(fx.get("ev_bal", False)))

        st.markdown(DS.alert_html(
            "danger",
            "Señales de alarma (suspenden la prescripción de ejercicio)",
            "Selecciona cualquiera de estas señales si está presente: el sistema "
            "no generará rutina y te pedirá evaluación profesional."),
            unsafe_allow_html=True)
        st.multiselect("Señales de alarma", list(INJURY_RED_FLAGS.values()), key="ev_rf",
                       default=_defaults_in(fx.get("ev_rf", []),
                                            list(INJURY_RED_FLAGS.values())))
        st.text_area("Observaciones (opcional)", key="ev_notes",
                     max_chars=300, value=str(fx.get("ev_notes", "") or ""),
                     placeholder="Cualquier detalle que quieras que el plan considere…")

    elif step == 4:
        st.markdown('<div class="fx-h2">Nutrición</div>', unsafe_allow_html=True)
        st.selectbox("Tipo de dieta", list(DIET_TYPES.values()), key="ev_diet",
                     index=_opt_index(list(DIET_TYPES.values()),
                                      fx.get("ev_diet", list(DIET_TYPES.values())[0])))
        c1, c2 = st.columns(2)
        with c1:
            st.multiselect("Alergias (exclusión estricta)",
                           list(ALLERGY_OPTIONS.values()), key="ev_alg",
                           default=_defaults_in(fx.get("ev_alg", []),
                                                list(ALLERGY_OPTIONS.values())))
        with c2:
            st.multiselect("Intolerancias (se evitan fuentes principales)",
                           list(INTOLERANCE_OPTIONS.values()), key="ev_int",
                           default=_defaults_in(fx.get("ev_int", []),
                                                list(INTOLERANCE_OPTIONS.values())))
        st.multiselect("Preferencias de consumo",
                       list(PREFERENCE_OPTIONS.values()), key="ev_pref",
                       default=_defaults_in(fx.get("ev_pref", []),
                                            list(PREFERENCE_OPTIONS.values())))

    else:  # paso 5 — revisión
        st.markdown('<div class="fx-h2">Revisión final</div>', unsafe_allow_html=True)
        _review_summary(_field_source())
        st.text_area("Observaciones finales (opcional)", key="ev_notes2",
                     max_chars=300, value=str(fx.get("ev_notes2", "") or ""))

    # Navegación del asistente
    st.markdown('<div style="height:.6rem"></div>', unsafe_allow_html=True)
    c_prev, c_next = st.columns([1, 2])
    with c_prev:
        if step > 1 and st.button("Volver", key="wz_back", use_container_width=True):
            st.session_state.fx_step = max(1, step - 1)
            st.rerun()
    with c_next:
        if step < 5:
            if st.button("Continuar", key="wz_next", use_container_width=True,
                         type="primary"):
                _advance_step(step, user)
        else:
            if st.button("Generar mi plan", key="wz_gen", use_container_width=True,
                         type="primary"):
                _generate(user)


def _defaults_in(raw, options) -> list:
    """Filtra candidatos de default contra las opciones válidas del widget.

    Protección de doble vía: aunque en `fx_ev` llegue una clave canónica o un
    valor rejugado desde el cliente (compatibilidad legada), el multiselect
    nunca recibe un default fuera de sus opciones (evita StreamlitAPIException).
    """
    opts = set(options)
    return [v for v in (raw or []) if v in opts]


def _review_summary(s: dict) -> None:
    def rev(icon, label, value):
        return (f'<div style="display:flex;justify-content:space-between;align-items:baseline;'
                f'padding:.42rem 0;border-bottom:1px dashed var(--fx-border);font-size:.87rem;">'
                f'<span style="color:var(--fx-muted);display:inline-flex;gap:.4rem;">'
                f'{DS.icon_svg(icon, 15, DS.TEXT_MUTED)} {label}</span>'
                f'<b>{value}</b></div>')
    st.markdown(
        '<div class="fx-card">' 
        + rev("perfil", "Edad / Sexo", f'{s.get("ev_age")} años · {s.get("ev_sex")}')
        + rev("perfil", "Peso / Estatura", f'{s.get("ev_weight")} kg · {s.get("ev_height")} cm')
        + rev("objetivo", "Objetivo", s.get("ev_objective"))
        + rev("progreso", "Actividad", s.get("ev_activity"))
        + rev("entrenamiento", "Experiencia", s.get("ev_exp"))
        + rev("inicio", "Lugar", s.get("ev_place"))
        + rev("nutricion", "Dieta", s.get("ev_diet"))
        + rev("nutricion", "Comidas / día", s.get("ev_freq"))
        + rev("salud", "Lesiones", ", ".join(s.get("ev_inj") or ["Ninguna"]) or "Ninguna")
        + rev("salud", "Alergias", ", ".join(s.get("ev_alg") or ["Ninguna"]) or "Ninguna")
        + rev("salud", "Intolerancias", ", ".join(s.get("ev_int") or ["Ninguna"]) or "Ninguna")
        + '</div>', unsafe_allow_html=True)


def _map_selection(x: str, domain: dict) -> str | None:
    """Traduce la etiqueta humana elegida a la clave canónica del dominio."""
    for key, human in domain.items():
        if human == x:
            return key
    for key, human in domain.items():
        if isinstance(human, str) and human.lower() == str(x).lower():
            return key
    return None


def _opt_index(options: list, value) -> int:
    """Índice del valor guardado dentro de las opciones de un selectbox."""
    try:
        return options.index(value)
    except (ValueError, TypeError):
        return 0


def _advance_step(step: int, user: dict) -> None:
    _absorb_step(step)  # persiste el paso actual antes de abandonarlo
    if step == 1:
        checks = ["ev_age", "ev_weight", "ev_height", "ev_bodyfat"]
    elif step == 2:
        checks = ["ev_freq"]
    else:
        st.session_state.fx_step = step + 1
        st.rerun()
        return

    from validation import (validate_age, validate_weight, validate_height,
                            validate_body_fat, validate_meal_frequency)
    labels = {"ev_age": "edad", "ev_weight": "peso", "ev_height": "estatura",
              "ev_bodyfat": "% de grasa", "ev_freq": "frecuencia de comidas"}
    validators = {"ev_age": validate_age, "ev_weight": validate_weight,
                  "ev_height": validate_height, "ev_bodyfat": validate_body_fat,
                  "ev_freq": validate_meal_frequency}

    errors = []
    for key in checks:
        raw = st.session_state.get(key)
        if key == "ev_freq":
            try:
                raw = int(str(raw or "3")[0])
            except (TypeError, ValueError):
                raw = None
        res = validators[key](raw)
        if not res.ok:
            errors.append(f"• {labels.get(key, key)}: {res.error}")
    if errors:
        st.session_state.fx_step_error = "Revisa los siguientes campos:\n" + "\n".join(errors)
        st.rerun()
        return
    st.session_state.fx_step = step + 1
    st.rerun()


def _generate(user: dict) -> None:
    _absorb_step(st.session_state.fx_step)  # captura observaciones finales
    s = _field_source()

    def canon(labels: list, domain: dict) -> list:
        out = []
        for lab in labels:
            k = _map_selection(lab, domain)
            if k:
                out.append(k)
        return out

    token = {k: v for k, v in INJURY_SEVERITY_OPTIONS.items()}
    severidad = _map_selection(s.get("ev_sev", ""), INJURY_SEVERITY_OPTIONS) or "ninguna"

    # Dominios invertidos etiqueta → clave
    inj_dom = {v: k for k, v in INJURY_OPTIONS.items()}
    rf_dom = {v: k for k, v in INJURY_RED_FLAGS.items()}
    eq_dom = {v: k for k, v in EQUIPMENT_OPTIONS.items()}
    alg_dom = {v: k for k, v in ALLERGY_OPTIONS.items()}
    int_dom = {v: k for k, v in INTOLERANCE_OPTIONS.items()}
    pref_dom = {v: k for k, v in PREFERENCE_OPTIONS.items()}

    data = {
        "name": s.get("ev_name", user["username"]),
        "age": s.get("ev_age"),
        "sex": "femenino" if s.get("ev_sex") == "Femenino" else "masculino",
        "weight": s.get("ev_weight"),
        "height": s.get("ev_height"),
        "body_fat_pct": s.get("ev_bodyfat", 0),
        "objective": _map_selection(s.get("ev_objective"), OBJECTIVE_LABELS),
        "activity_level": _map_selection(s.get("ev_activity"), ACTIVITY_LABELS),
        "experience": _map_selection(s.get("ev_exp"), EXPERIENCE_LABELS),
        "training_place": _map_selection(s.get("ev_place"), TRAINING_PLACE_LABELS),
        "diet_type": _map_selection(s.get("ev_diet"), DIET_TYPES),
        "meal_frequency": int(str(s.get("ev_freq"))[0]),
        "injuries": [inj_dom.get(l) for l in (s.get("ev_inj") or []) if inj_dom.get(l)],
        "injury_severity": severidad,
        "balance_issues": bool(s.get("ev_bal")),
        "red_flags": [rf_dom.get(l) for l in (s.get("ev_rf") or []) if rf_dom.get(l)],
        "equipment": [eq_dom.get(l) for l in (s.get("ev_equip") or []) if eq_dom.get(l)],
        "allergies": [alg_dom.get(l) for l in (s.get("ev_alg") or []) if alg_dom.get(l)],
        "intolerances": [int_dom.get(l) for l in (s.get("ev_int") or []) if int_dom.get(l)],
        "preferences": [pref_dom.get(l) for l in (s.get("ev_pref") or []) if pref_dom.get(l)],
        "notes": s.get("ev_notes2") or s.get("ev_notes") or "",
    }

    # La casa sin equipo declarado siempre tiene peso corporal disponible
    if not data["equipment"]:
        data["equipment"] = ["solo_peso_corporal"]

    values, errores, warnings = validate_evaluation(data)
    if errores:
        cuerpo = "\n".join(f"• {campo}: {msg}" for campo, msg in errores.items())
        st.session_state.fx_step_error = "Datos incompletos — revisa:\n\n" + cuerpo
        st.session_state.fx_step = 1
        st.rerun()
        return

    resultados = _run_evaluation(values, warnings)
    st.session_state.fx_page = "plan"
    st.rerun()


# ──────────────────────────────────────────────────────────────
#  Página: Plan actual (resultados)
# ──────────────────────────────────────────────────────────────

def _macros_bars(macros: dict, kcal: float) -> str:
    total = max(float(macros.get("proteinas", 0)) * 4 +
                float(macros.get("carbohidratos", 0)) * 4 +
                float(macros.get("grasas", 0)) * 9, 1)
    p = float(macros.get("proteinas", 0))
    c = float(macros.get("carbohidratos", 0))
    g = float(macros.get("grasas", 0))
    pw, cw, gw = p * 4 / total * 100, c * 4 / total * 100, g * 9 / total * 100

    def bar(label, grams, pct, color):
        return (f'<div class="fx-macro"><div class="row"><span>{label}</span>'
                f'<b>{grams:.0f} g · {pct:.0f}%</b></div>'
                f'<div class="fx-track"><div class="fx-fill" style="width:{min(pct,100):.0f}%;'
                f'background:{color};"></div></div></div>')
    return bar("Proteínas", p, pw, DS.PRIMARY) + bar("Carbohidratos", c, cw, DS.ACCENT) \
        + bar("Grasas", g, gw, DS.GOLD)


def _meal_card(name: str, items: list) -> str:
    lis = "".join(f'<div class="fx-ex"><span class="nm">{it}</span></div>' for it in items)
    return (f'<div class="fx-day"><div class="hd"><span class="dayname">{name}</span>'
            f'</div>{lis}</div>')


@st.dialog("Ficha del ejercicio", width="large")
def _exercise_dialog(slug: str, perfil=None) -> None:
    """Modal con la ficha informativa de un ejercicio (catálogo EI)."""
    ficha = EI.get_ficha(slug)
    import html as _html
    esc = lambda s: _html.escape(str(s))

    st.markdown(f'<div class="fx-h2">{esc(ficha.get("nombre", "Ejercicio"))}</div>',
                unsafe_allow_html=True)

    chips = _chip(ficha.get("categoria", "—"), "primary") + " " + \
        _chip(ficha.get("grupo_muscular", "—"), "info")
    for sec in ficha.get("secundarios", []) or []:
        chips += " " + _chip(esc(sec), "muted")
    st.markdown(chips, unsafe_allow_html=True)

    # Slot de imagen (lienzo 4:3) — nunca lanza excepción
    ruta = EI.resolve_exercise_image(ficha.get("slug", slug))
    if ruta is not None:
        st.image(str(ruta), use_container_width=True)
    else:
        st.markdown(
            '<div class="fx-eximg fx-eximg--empty">'
            f'{DS.icon_svg("imagen", 34, "currentColor", 1.6)}'
            f'<div class="t">Imagen del ejercicio próximamente</div>'
            f'<div class="s">{esc(ficha.get("nombre", ""))}</div>'
            '</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="fx-rule"><div><div class="exp">{esc(ficha.get("descripcion", ""))}</div></div></div>',
                unsafe_allow_html=True)

    def _bloque(titulo, items):
        if items:
            cuerpo = "".join(f"• {esc(x)}<br>" for x in items)
            st.markdown(DS.alert_html("info", titulo, cuerpo), unsafe_allow_html=True)

    _bloque("Ejecución paso a paso", ficha.get("pasos"))
    _bloque("Errores comunes", ficha.get("errores"))
    _bloque("Consejos y seguridad", ficha.get("consejos"))

    extra = []
    if ficha.get("respiracion"):
        extra.append(f"<b>Respiración:</b> {esc(ficha['respiracion'])}")
    if ficha.get("tempo"):
        extra.append(f"<b>Tempo:</b> {esc(ficha['tempo'])}")
    if ficha.get("regresion"):
        extra.append(f"<b>Regresión:</b> {esc(ficha['regresion'])}")
    if ficha.get("progresion"):
        extra.append(f"<b>Progresión:</b> {esc(ficha['progresion'])}")
    if extra:
        st.markdown(DS.alert_html("violet", "Técnica", "<br>".join(extra)),
                    unsafe_allow_html=True)

    # Precauciones enlazadas a la matriz de lesiones y al perfil activo
    zonas = EI.lesion_labels(ficha.get("lesiones"))
    if zonas:
        cuerpo = "Contraindicado o requiere precaución en: " + ", ".join(esc(z) for z in zonas) + "."
        if perfil is not None and getattr(perfil, "injuries", None):
            activas = [INJURY_OPTIONS.get(i, i) for i in perfil.injuries]
            cuerpo += f"<br>Tu perfil registra: {esc(', '.join(activas))}. " \
                      "Considera la regresión o consulta a un profesional."
        st.markdown(DS.alert_html("warn", "Precauciones", cuerpo),
                    unsafe_allow_html=True)

    if st.button("Cerrar", key=f"exclose_{slug}", use_container_width=True):
        st.rerun()


def _toggle_dia(slug_dia: str) -> None:
    clave = f"dia_abierto_{slug_dia}"
    st.session_state[clave] = not st.session_state.get(clave, False)


def _page_plan(user: dict) -> None:
    _top("plan", "Plan actual", "Tu nutrición, tu entrenamiento y el razonamiento del experto.")
    res = st.session_state.fx_results or _load_latest_results(user["user_id"])
    if res is not None and st.session_state.get("fx_results") is None:
        # Cachea en sesión: evita releer usuarios.json (y regenerar el plan
        # en sesiones antiguas) en cada rerun de esta página.
        st.session_state.fx_results = res

    if not res:
        _empty("plan", "Sin plan activo",
               "Genera una nueva evaluación para construir tu plan personalizado.",
               "Crear evaluación", "nueva")
        st.markdown(_foot(), unsafe_allow_html=True)
        return

    perfil = res["perfil"]
    plan = res["plan"]
    rutina = res["rutina"]
    warnings = res["warnings"]

    # Acciones de cabecera
    c1, c2, c3 = st.columns([2.4, 1, 1])
    with c1:
        st.markdown(f'<div class="fx-muted" style="font-size:.78rem;">'
                    f'{perfil.name} · generado el {_fmt_fecha(perfil.created_at)}'
                    f'</div>', unsafe_allow_html=True)
    with c2:
        _btn_pdf(perfil, plan, rutina)
    with c3:
        if st.button("Nueva evaluación", key="pl_nueva",
                     use_container_width=True):
            st.session_state.fx_page = "nueva"
            st.rerun()

    if perfil.red_flags or perfil.injury_severity == "aguda":
        st.markdown(DS.alert_html(
            "danger", "Suspensión de prescripción de ejercicio",
            "Por señales de alarma o lesión aguda, FitExpert no prescribe rutina. "
            "La parte nutricional puede consultarse; antes de entrenar, acude a "
            "un profesional de la salud."), unsafe_allow_html=True)

    if warnings:
        cuerpo = "<br>".join("• " + w for w in warnings[:6])
        st.markdown(DS.alert_html("warn", "Consideraciones de seguridad",
                                  cuerpo), unsafe_allow_html=True)

    # Bandas de métricas
    band = "".join([
        _metric("salud", "IMC", f"{perfil.imc:.1f}", perfil.imc_category,
                _imc_color(perfil.imc)),
        _metric("cronometro", "TMB", f"{perfil.tmb:.0f}", "kcal en reposo", DS.ACCENT),
        _metric("progreso", "TDEE", f"{perfil.tdee:.0f}", "gasto total estimado", DS.PRIMARY),
        _metric("objetivo", "Meta diaria", f"{perfil.target_calories:.0f}",
                "kcal objetivo", DS.GOLD),
    ])
    st.markdown(f'<div class="fx-band">{band}</div>', unsafe_allow_html=True)

    tab_nut, tab_trn, tab_exp = st.tabs(
        ["Nutrición", "Entrenamiento", "Decisiones del experto"])

    # ── Nutrición ──────────────────────────────────────────────
    with tab_nut:
        c_mac, c_meals = st.columns([1, 1.7])
        with c_mac:
            st.markdown(
                f'<div class="fx-card fx-card--accent"><div class="fx-h2">Distribución de macronutrientes</div>'
                f'{_macros_bars(plan.get("macros", {}), perfil.target_calories)}'
                f'<p>Meta diaria: <b>{perfil.target_calories:.0f} kcal</b> · '
                f'Hidratación recomendada: <b>{plan.get("plan", {}).get("hidratacion", "—")}</b></p>'
                f'</div>', unsafe_allow_html=True)
        with c_meals:
            st.markdown('<div class="fx-h2">Menú recomendado</div>', unsafe_allow_html=True)
            _plan = plan.get("plan", {})
            for name, key in (("Desayuno", "desayuno"), ("Almuerzo", "almuerzo"),
                              ("Cena", "cena"), ("Snacks", "snacks")):
                items = _plan.get(key) or []
                if items:
                    st.markdown(_meal_card(name, items), unsafe_allow_html=True)

        sustituciones = plan.get("sustituciones") or []
        if sustituciones:
            st.markdown('<div class="fx-h2">Sustituciones por alergias / intolerancias</div>',
                        unsafe_allow_html=True)
            for su in sustituciones:
                al = ALLERGY_OPTIONS.get(su.get("alergeno", ""), su.get("alergeno", "—"))
                st.markdown(DS.alert_html(
                    "violet", f"Alergia a {al}",
                    str(su.get("substitucion", ""))), unsafe_allow_html=True)
            st.markdown(
                '<div class="fx-small">La seguridad frente a contaminación cruzada '
                'depende de leer siempre las etiquetas de los productos.</div>',
                unsafe_allow_html=True)

    # ── Entrenamiento ──────────────────────────────────────────
    with tab_trn:
        dias = rutina.get("semana", [])
        activos = [d for d in dias if not d.get("descanso")]
        chip_dias = _chip(f"{rutina.get('dias', '')} sesiones/semana", "info")
        st.markdown(
            f'<div class="fx-card fx-card--accent"><div class="fx-h2">{rutina.get("nombre", "Rutina").upper()}</div>'
            f'<p>{rutina.get("tipo", "")} · {len(activos)} días de entrenamiento de {len(dias)} '
            f'de la semana · {chip_dias}</p>'
            f'</div>', unsafe_allow_html=True)

        # ── Acordeón de días: estado inicial SOLO una vez por plan ──
        plan_key = US.plan_key_de(perfil, rutina)
        if st.session_state.get("fx_plan_key") != plan_key:
            st.session_state.fx_plan_key = plan_key
            abiertos_ini = US.dias_abiertos_iniciales(dias)
            for _d in dias:
                _nom = US.nombre_de_dia(_d)
                st.session_state[f"dia_abierto_{EI.slugify(_nom)}"] = (
                    EI.slugify(_nom) in abiertos_ini)

        _hoy = ["lunes", "martes", "miércoles", "jueves", "viernes",
                "sábado", "domingo"][datetime.now().weekday()]

        for i, day in enumerate(dias):
            nombre_dia = day.get("dia", "")
            _slug_dia = EI.slugify(nombre_dia)
            abierto = bool(st.session_state.get(f"dia_abierto_{_slug_dia}", False))
            es_descanso = US.es_descanso(day)
            n_ej = US.conteo_ejercicios(day)
            chip_kind = "neutral" if (es_descanso or "descanso" in US._norm(day.get("grupo", ""))) else ""
            etiqueta_foco = "Descanso" if es_descanso else (day.get("grupo", "") or "—")

            with st.container(key=f"{'dia_rest_' if es_descanso else 'dia_'}{_slug_dia}"):
                if abierto:
                    st.markdown('<span class="fx-day-open-marker" style="display:none"></span>',
                                unsafe_allow_html=True)
                _sub = US.texto_secundario_dia(day)
                if es_descanso:
                    _sub = f'{DS.icon_svg("luna", 12)} {_sub}'
                with st.container(key=f"hd_{_slug_dia}"):
                    st.markdown(
                        f'<div class="fx-dayhd">'
                        f'<div class="fx-dayhd-txt">'
                        f'<div class="fx-dayhd-name">{nombre_dia}'
                        f'{"<span class=\"fx-day-chip hoy\">Hoy</span>" if EI.slugify(nombre_dia) == EI.slugify(_hoy) else ""}'
                        f'</div>'
                        f'<div class="fx-dayhd-sub">{_sub}</div>'
                        f'</div>'
                        f'<span class="fx-day-chip {chip_kind}">{etiqueta_foco}</span>'
                        f'<span class="fx-dayhd-chev fx-chev {"open" if abierto else ""}">'
                        f'{DS.icon_svg("flecha_der", 16)}</span>'
                        '</div>',
                        unsafe_allow_html=True)
                    st.button(f"{nombre_dia} — {US.texto_secundario_dia(day)}",
                              key=f"hdbtn_{_slug_dia}",
                              type="tertiary", use_container_width=True,
                              on_click=_toggle_dia, args=(_slug_dia,))

                if not abierto:
                    continue

                st.markdown('<div class="fx-day-sep"></div>', unsafe_allow_html=True)

                if es_descanso:
                    st.markdown(
                        '<div class="fx-day-rest">Día de recuperación: sin ejercicios '
                        'programados. Si te apetece, un paseo suave o movilidad ligera.</div>',
                        unsafe_allow_html=True)
                    continue

                for ei_idx, e in enumerate(day.get("ejercicios", [])):
                    nombre = e[0] if len(e) > 0 else ""
                    slug = EI.slugify(nombre)
                    detalle = f'{e[1] if len(e) > 1 else ""}{" · " + e[2] if len(e) > 2 else ""}'
                    with st.container(key=f"ex_{i}_{ei_idx}_{slug}"):
                        st.markdown(
                            f'<div class="fx-exrow">'
                            f'<span class="fx-exrow-name">{nombre}</span>'
                            f'<span class="fx-exrow-detail">{detalle}</span>'
                            '</div>', unsafe_allow_html=True)
                        if st.button(f"{nombre} — {detalle}",
                                     key=f"exbtn_{i}_{ei_idx}_{slug}",
                                     type="tertiary", use_container_width=True):
                            st.session_state.fx_exercise = slug
                if not day.get("ejercicios"):
                    st.markdown(
                        '<div class="fx-day-rest">Sin ejercicios programados para este día.</div>',
                        unsafe_allow_html=True)
                st.markdown(
                    f'<div class="fx-day-rest">Descanso entre series: '
                    f'{day.get("descanso_entre_series", "—")}</div>',
                    unsafe_allow_html=True)

        if rutina.get("lesiones_consideradas"):
            st.markdown(DS.alert_html(
                "violet", "Restricciones por lesión consideradas",
                ", ".join(rutina.get("lesiones_consideradas", []))), unsafe_allow_html=True)
        if rutina.get("alternativas_aplicadas"):
            cuerpo = "<br>".join("• " + a for a in rutina.get("alternativas_aplicadas", []))
            st.markdown(DS.alert_html("violet", "Ejercicios sustituidos por lesión",
                                      cuerpo), unsafe_allow_html=True)
        if rutina.get("cardio_extra"):
            st.markdown(DS.alert_html("success", "Cardio complementario",
                                      rutina.get("cardio_extra", "")), unsafe_allow_html=True)

    # ── Explicación ────────────────────────────────────────────
    with tab_exp:
        _render_explicacion(perfil)

    # ── Apertura de ficha de ejercicio (modal) ─────
    slug_sel = st.session_state.get("fx_exercise")
    if slug_sel:
        st.session_state.fx_exercise = None  # evita reaperturas en reruns
        _exercise_dialog(slug_sel, perfil)

    st.markdown(_foot(), unsafe_allow_html=True)


def _btn_pdf(perfil, plan, rutina) -> None:
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name
        export_pdf(perfil, plan, rutina, tmp_path)
        with open(tmp_path, "rb") as fh:
            data = fh.read()
        os.unlink(tmp_path)
        st.download_button(
            "Descargar PDF",
            data=data,
            file_name=f"Plan_FitExpert_{perfil.name.replace(' ', '_')}.pdf",
            mime="application/pdf",
            key="pl_pdf", use_container_width=True)
    except Exception as exc:  # nunca romper la página por un PDF
        st.caption(f"No se pudo generar el PDF: {exc}")


# ──────────────────────────────────────────────────────────────
#  Página: Historial
# ──────────────────────────────────────────────────────────────

def _page_historial(user: dict) -> None:
    _top("historial", "Historial",
         "Tus evaluaciones guardadas. Selecciona una para ver el detalle.")
    history = get_user_history(user["user_id"])

    if not history:
        _empty("historial", "Aún no hay evaluaciones",
               "Cada evaluación que generes quedará guardada aquí.",
               "Crear mi primera evaluación", "nueva")
        st.markdown(_foot(), unsafe_allow_html=True)
        return

    opciones = [f'{_fmt_fecha(h.get("saved_at", ""))} — '
                f'Peso {h.get("weight", 0):.1f} kg · '
                f'IMC {h.get("imc", 0):.1f}   ({OBJECTIVE_LABELS.get(h.get("objective", ""), "—")})'
                for h in history]
    sel = st.selectbox("Sesión para ver en detalle", range(len(history)),
                       format_func=lambda i: opciones[i],
                       key="fx_hist_sel")

    entry = history[sel]
    m_imc = _metric("salud", "IMC", f"{entry.get('imc', 0):.1f}",
                    entry.get("imc_category", ""), _imc_color(entry.get("imc", 0)))
    m_tmb = _metric("cronometro", "TMB", f"{entry.get('tmb', 0):.0f}",
                    "kcal reposo", DS.ACCENT)
    m_kcal = _metric("objetivo", "Meta diaria", f"{entry.get('target_calories', 0):.0f}",
                     "kcal", DS.GOLD)
    m_age = _metric("perfil", "Edad", f"{entry.get('age', 0)}", "años", DS.TEXT_MUTED)
    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.markdown(
            f'<div class="fx-card fx-card--accent"><div class="fx-h2">Métricas guardadas</div>'
            f'<div class="fx-band">{m_imc}{m_tmb}{m_kcal}{m_age}</div>'
            f'<p class="fx-small">Confirmado: {"femenino" if entry.get("sex") == "femenino" else "masculino"} · '
            f'Dieta {DIET_TYPES.get(entry.get("diet_type", ""), entry.get("diet_type", "—"))} · '
            f'{entry.get("meal_frequency", 3)} comidas/día</p></div>',
            unsafe_allow_html=True)

    with c2:
        bf_txt = ("—" if not entry.get("body_fat_pct")
                  else f"{entry.get('body_fat_pct', 0):.1f}%")
        st.markdown(
            f'<div class="fx-card"><div class="fx-h2">Resumen de la evaluación</div>'
            f'<p>Peso {entry.get("weight", 0):.1f} kg · Estatura {entry.get("height", 0):.0f} cm · '
            f'Grasa {bf_txt}</p>'
            f'<p>Lesiones: {", ".join(INJURY_OPTIONS.get(x, x) for x in entry.get("injuries", [])) or "Ninguna"}</p>'
            f'<p>Alergias: {", ".join(ALLERGY_OPTIONS.get(x, x) for x in entry.get("allergies", [])) or "Ninguna"}</p>'
            f'</div>', unsafe_allow_html=True)

    if st.button("Usar estos datos como base para una nueva evaluación",
                 key="hs_reuse", use_container_width=True):
        _prefill_from(entry, user)
        st.session_state.fx_page = "nueva"
        st.rerun()

    concl = entry.get("conclusions") or []
    if concl:
        st.markdown('<div class="fx-h2" style="margin-top:.8rem;">Conclusiones del motor</div>',
                    unsafe_allow_html=True)
        for c in concl[:5]:
            rid = c.get("id", "")
            exp = next((e.get("explanation", "") for e in (entry.get("explanations") or [])
                        if e.get("id") == rid), "")
            color = _sev_color(c.get("severity", "info"))
            st.markdown(
                f'<div class="fx-rule"><span class="bar" style="background:{color};"></span>'
                f'<div><div class="rid">{rid}</div>'
                f'<div class="concl">{c.get("conclusion", "")}</div>'
                f'<div class="exp">{exp}</div></div></div>',
                unsafe_allow_html=True)

    st.markdown(_foot(), unsafe_allow_html=True)


def _prefill_from(entry: dict, user: dict) -> None:
    """Vuelca una sesión guardada en el borrador del asistente (fx_ev)."""
    fx = st.session_state.setdefault("fx_ev", {})
    fx["ev_name"] = user["username"]
    fx["ev_age"] = entry.get("age", 25)
    fx["ev_sex"] = "Femenino" if entry.get("sex") == "femenino" else "Masculino"
    fx["ev_weight"] = float(entry.get("weight", 70))
    fx["ev_height"] = float(entry.get("height", 172))
    fx["ev_bodyfat"] = float(entry.get("body_fat_pct", 0) or 0.0)
    fx["ev_objective"] = OBJECTIVE_LABELS.get(entry.get("objective", "mantenimiento"),
                                              list(OBJECTIVE_LABELS.values())[4])
    fx["ev_activity"] = ACTIVITY_LABELS.get(entry.get("activity_level", "ligero"),
                                            list(ACTIVITY_LABELS.values())[1])
    fx["ev_exp"] = EXPERIENCE_LABELS.get(entry.get("experience", "principiante"),
                                         list(EXPERIENCE_LABELS.values())[0])
    fx["ev_place"] = TRAINING_PLACE_LABELS.get(entry.get("training_place", "casa"))
    fx["ev_freq"] = f"{entry.get('meal_frequency', 3)} comidas"
    fx["ev_equip"] = [EQUIPMENT_OPTIONS.get(k) for k in (entry.get("equipment", []) or [])
                      if k in EQUIPMENT_OPTIONS]
    fx["ev_inj"] = [INJURY_OPTIONS.get(x, x) for x in entry.get("injuries", [])]
    fx["ev_sev"] = INJURY_SEVERITY_OPTIONS.get(entry.get("injury_severity", "ninguna"),
                                               list(INJURY_SEVERITY_OPTIONS.values())[0])
    fx["ev_bal"] = bool(entry.get("balance_issues", False))
    fx["ev_rf"] = [INJURY_RED_FLAGS.get(x, x) for x in entry.get("red_flags", [])]
    fx["ev_notes"] = entry.get("notes", "")
    fx["ev_diet"] = DIET_TYPES.get(entry.get("diet_type", "omnivoro"),
                                   list(DIET_TYPES.values())[0])
    fx["ev_alg"] = [ALLERGY_OPTIONS.get(x, x) for x in entry.get("allergies", [])]
    fx["ev_int"] = [INTOLERANCE_OPTIONS.get(x, x) for x in entry.get("intolerances", [])]
    fx["ev_pref"] = [PREFERENCE_OPTIONS.get(x, x) for x in entry.get("preferences", [])]
    st.session_state.fx_step = 1


# ──────────────────────────────────────────────────────────────
#  Página: Evolución
# ──────────────────────────────────────────────────────────────

def _page_progreso(user: dict) -> None:
    _top("progreso", "Evolución",
         "Sigue tu progreso entre evaluaciones: peso, calorías y sesiones.")
    history = get_user_history(user["user_id"])
    progress = get_progress_summary(user["user_id"])

    if len(history) < 2:
        _empty("progreso", "Necesitas más datos",
               "Con al menos 2 evaluaciones podrás visualizar tu evolución.")
        st.markdown(_foot(), unsafe_allow_html=True)
        return

    band = "".join([
        _metric("historial", "Evaluaciones", str(progress.get("sesiones", 0)),
                "registradas", DS.ACCENT),
        _metric("progreso", "Δ Peso",
                f"{'+' if progress.get('delta_peso_kg', 0) > 0 else ''}"
                f"{progress.get('delta_peso_kg', 0):.1f} kg",
                "desde la primera", DS.SUCCESS if progress.get("delta_peso_kg", 0) <= 0 else DS.DANGER),
        _metric("calendario", "Periodo",
                f"{len(history)} sesiones",
                f"{_fmt_fecha(progress.get('primera_sesion', ''))} → {_fmt_fecha(progress.get('ultima_sesion', ''))}",
                DS.PRIMARY),
    ])
    st.markdown(f'<div class="fx-band">{band}</div>', unsafe_allow_html=True)

    st.markdown('<div class="fx-h2">Evolución del peso</div>', unsafe_allow_html=True)
    st.pyplot(_fig_evolucion(history), clear_figure=True)
    st.markdown('<div class="fx-h2" style="margin-top:1.1rem;">Ajuste calórico</div>',
                unsafe_allow_html=True)
    st.pyplot(_fig_calorias(history), clear_figure=True)
    st.markdown(_foot(), unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
#  Página: Lógica del experto
# ──────────────────────────────────────────────────────────────

def _render_explicacion(perfil) -> None:
    conclusions = list(perfil.conclusions or [])
    suppressed = list(perfil.suppressed or [])
    errors = list(perfil.engine_errors or [])

    st.markdown(
        f'<div class="fx-card fx-card--accent"><div class="fx-h2">Transparencia del motor</div>'
        f'<p>{len(conclusions)} reglas activadas · {len(suppressed)} suprimidas por jerarquía · '
        f'{len(errors)} errores internos · sobre {len(RULES)} reglas evaluadas.</p>'
        f'<p class="fx-small">Cada conclusión explica qué dato tuyo activó la regla, '
        f'con qué referencia y qué alternativa consideró el sistema.</p></div>',
        unsafe_allow_html=True)

    _sev_order = {"critica": 0, "alta": 1, "media": 2, "baja": 3, "info": 4}

    if not conclusions and not suppressed:
        _empty("explicacion", "Sin conclusiones específicas",
               "Ninguna regla de la base de conocimiento se activó para este perfil, "
               "más allá de los cálculos generales.", None)

    def _rule_card(c: dict) -> str:
        rid = c.get("id", "")
        sev = c.get("severity", "info")
        sev_style = DS.severity_style(sev)
        tier = c.get("tier", "")
        tier_label = TIER_LABELS.get(tier, tier)
        exp = next((e.get("explanation", "") for e in (perfil.explanations or [])
                    if e.get("id") == rid), "")
        refs = c.get("references")
        alternative = c.get("alternative")
        chips = (DS.badge_html(sev, tier) + "&nbsp;")
        alt_html = (f'<div class="alt">Alternativa considerada: {alternative}</div>'
                    if alternative else "")
        refs_html = (f'<div class="refs">{refs}</div>' if refs else "")
        return (f'<div class="fx-rule"><span class="bar" style="background:{sev_style["color"]};"></span>'
                f'<div style="flex:1;min-width:0;">'
                f'<div class="rid">{rid} · {tier_label}</div>'
                f'{chips}'
                f'<div class="concl">{c.get("conclusion", "")}</div>'
                f'<div class="exp">{exp}</div>'
                f'{refs_html}{alt_html}</div></div>')

    for c in sorted(conclusions, key=lambda c: _sev_order.get(c.get("severity", "info"), 9)):
        st.markdown(_rule_card(c), unsafe_allow_html=True)

    if suppressed:
        st.markdown('<div class="fx-h2" style="margin-top:1rem;">Reglas suprimidas por jerarquía</div>',
                    unsafe_allow_html=True)
        for s in suppressed:
            st.markdown(
                f'<div class="fx-rule"><span class="bar" style="background:{DS.TEXT_FAINT};"></span>'
                f'<div><div class="rid">[{s.get("id", "")}] suprimida por [{s.get("suppressed_by", "")}]</div>'
                f'<div class="exp">{s.get("reason", "")}</div></div></div>',
                unsafe_allow_html=True)

    if errors:
        st.markdown('<div class="fx-h2" style="margin-top:1rem;">Errores internos de evaluación</div>',
                    unsafe_allow_html=True)
        for e in errors:
            st.markdown(DS.alert_html("danger", f"Regla [{e.get('id', '')}]",
                                      str(e.get("error", ""))), unsafe_allow_html=True)


def _page_explicacion(user: dict) -> None:
    _top("explicacion", "Lógica del experto",
         "Recorre el razonamiento del motor: qué regla, qué dato tuyo la activó y con qué fuente.")
    res = st.session_state.fx_results or _load_latest_results(user["user_id"])
    if not res:
        _empty("explicacion", "Sin plan activo",
               "Genera una evaluación para poder explicarte sus decisiones.",
               "Crear evaluación", "nueva")
    else:
        _render_explicacion(res["perfil"])
    st.markdown(_foot(), unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
#  Página: Perfil
# ──────────────────────────────────────────────────────────────

def _page_perfil(user: dict) -> None:
    _top("perfil", "Perfil", "Datos de tu cuenta, tu progreso y seguridad.")
    history = get_user_history(user["user_id"])
    progress = get_progress_summary(user["user_id"])

    band = "".join([
        _metric("historial", "Evaluaciones", str(progress.get("sesiones", 0)),
                "guardadas", DS.ACCENT),
        _metric("progreso", "Δ Peso",
                f"{'+' if progress.get('delta_peso_kg', 0) > 0 else ''}"
                f"{progress.get('delta_peso_kg', 0):.1f} kg",
                "desde la primera", DS.PRIMARY),
        _metric("inicio", "Plan activo",
                "Sí" if (st.session_state.fx_results
                         or _load_latest_results(user["user_id"])) else "No",
                "evaluación actual", DS.GOLD),
    ])
    st.markdown(f'<div class="fx-band">{band}</div>', unsafe_allow_html=True)

    c_acc, c_pwd = st.columns([1, 1])
    with c_acc:
        st.markdown(
            f'<div class="fx-card"><div class="fx-h2">Cuenta</div>'
            f'<div style="display:flex;gap:.6rem;align-items:center;margin-top:.4rem;">'
            f'<span class="fx-avatar" style="width:44px;height:44px;font-size:1.1rem;">'
            f'{user["username"][:1].upper()}</span>'
            f'<div><div style="font-weight:700;">{user["username"]}</div>'
            f'<div class="fx-small">ID {user["user_id"][:8]}…</div></div></div>'
            f'<p class="fx-small" style="margin-top:.6rem;">Sesión local del navegador. '
            f'Los datos viven en este equipo con autenticación Argon2id.</p></div>',
            unsafe_allow_html=True)

    with c_pwd:
        st.markdown('<div class="fx-card"><div class="fx-h2">Cambiar contraseña</div>',
                    unsafe_allow_html=True)
        with st.form("pf_cambio"):
            old = st.text_input("Contraseña actual", type="password", key="pf_old")
            nw = st.text_input("Nueva contraseña", type="password", key="pf_new",
                               help="Mínimo 8 caracteres")
            nw2 = st.text_input("Confirmar nueva contraseña", type="password", key="pf_new2")
            submitted = st.form_submit_button("Actualizar contraseña",
                                              use_container_width=True, type="primary")
            if submitted:
                if nw != nw2:
                    st.error("Las nuevas contraseñas no coinciden.")
                else:
                    res = change_password(user["username"], old, nw)
                    if res.get("ok"):
                        st.success("Contraseña actualizada.")
                    else:
                        st.error(res.get("error", "No se pudo actualizar."))
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(_foot(), unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
#  Página: Acerca
# ──────────────────────────────────────────────────────────────

def _page_acerca(user: dict) -> None:
    _top("libro", "Acerca de FitExpert",
         "El sistema experto: conocimiento, jerarquía de seguridad y alcance.")

    # Conteo de reglas por tier
    por_tier: dict = {}
    for r in RULES:
        tier = getattr(r, "tier", "OBJETIVO") or "OBJETIVO"
        por_tier[tier] = por_tier.get(tier, 0) + 1

    tiers_html = "".join(
        f'<div class="fx-macro"><div class="row"><span>'
        f'{DS.TIER_STYLE.get(t, {}).get("icon", "•")}&nbsp; '
        f'{TIER_LABELS.get(t, t)}</span><b>{n} reglas</b></div>'
        f'<div class="fx-track"><div class="fx-fill" style="width:{n / len(RULES) * 100:.0f}%;'
        f'background:{DS.TIER_STYLE.get(t, {}).get("color", DS.TEXT_MUTED)};"></div></div></div>'
        for t, n in sorted(por_tier.items(),
                           key=lambda kv: DS.TIER_STYLE.get(kv[0], {}).get("color", "")))

    stats = db_stats()
    st.markdown(
        f'<div class="fx-card fx-card--accent"><div class="fx-h2">Motor de conocimiento</div>'
        f'<p>Encadenamiento hacia adelante sobre una base de <b>{len(RULES)} reglas</b> '
        f'IF/THEN con 7 jerarquías de severidad. La jerarquía decide qué hacer cuando '
        f'dos reglas compiten: seguridad y contraindicaciones mandan sobre el resto.</p>'
        f'{tiers_html}</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f'<div class="fx-card"><div class="fx-h2">Actividad del sistema</div>'
            f'<p>{stats.get("total_sesiones", 0)} evaluaciones · '
            f'{stats.get("usuarios_unicos", 0)} usuarios · '
            f'{len(RULES)} reglas en la base de conocimiento.</p></div>',
            unsafe_allow_html=True)
    with c2:
        st.markdown(
            f'<div class="fx-card"><div class="fx-h2">Fuentes de referencia</div>'
            f'<p>{" · ".join(_SOURCES)}</p>'
            f'<p class="fx-small">El contenido es orientativo y educativo; no sustituye '
            f'al consejo, diagnóstico ni tratamiento de un profesional de la salud.</p></div>',
            unsafe_allow_html=True)

    st.markdown(
        f'<div class="fx-card fx-card--dim"><div class="fx-h2">Límites del sistema</div>'
        f'<p class="fx-small">Edad 10–100 · Peso 30–300 kg · Estatura 100–250 cm · '
        f'Grasa 3–70%. Fuera de rango, el formulario pide revisión antes de calcular. '
        f'Ante señales de alarma, el sistema suspende la prescripción de ejercicio.</p></div>',
        unsafe_allow_html=True)
    st.markdown(_foot(), unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
#  Punto de entrada
# ──────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title=f"{_APP_NAME} — Nutrición y entrenamiento que se explican",
        page_icon=_ICON_FAVICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _defaults()

    user = st.session_state.fx_user
    if not user:
        _render_auth()
        return

    _css()
    _sidebar(user)

    page = st.session_state.fx_page
    if page == "nueva":
        _page_nueva(user)
    elif page == "plan":
        _page_plan(user)
    elif page == "historial":
        _page_historial(user)
    elif page == "progreso":
        _page_progreso(user)
    elif page == "explicacion":
        _page_explicacion(user)
    elif page == "perfil":
        _page_perfil(user)
    elif page == "acerca":
        _page_acerca(user)
    else:
        st.session_state.fx_page = "inicio"
        _page_inicio(user)


main()