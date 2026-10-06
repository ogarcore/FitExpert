"""
gui.py
======
Interfaz web de FitExpert (Streamlit) — v3.0 (auditoría completa)

Mejoras respecto a v2:
  - Formulario MULTI-PASO con validación por paso (validation.validate_evaluation).
  - Estados de carga con progreso visible durante el ciclo de inferencia.
  - Micro-interacciones definidas en design_system.WEB_CSS (stepper, tarjetas
    que entran en cascada, `prefers-reduced-motion` respetado).
  - Sin dependencias de red: se eliminó la imagen del sidebar desde CDN.
  - Corrección del KeyError: las sesiones de entrenamiento exponen `dia/grupo`,
    no `nombre` (contrato de training.generate_training_plan).
  - Estadísticas con las claves reales de db_stats (total_sesiones,
    usuarios_unicos, por_objetivo).
  - Transparencia del motor: reglas activadas/suprimidas/saltadas/errores,
    con su severidad, tier, referencias reales y alternativas.
  - Señales de alarma (red flags) y lesión aguda mostradas con máxima
    prominencia; el plan se suspende.
  - Combinación peso×estatura validada (IMC plausible) antes de ejecutar.
"""

import io

import pandas as pd
import streamlit as st

from user_profile import (
    UserProfile, OBJECTIVE_LABELS, ACTIVITY_LABELS, EXPERIENCE_LABELS,
    TRAINING_PLACE_LABELS, DIET_TYPES, ALLERGY_OPTIONS, INTOLERANCE_OPTIONS,
    PREFERENCE_OPTIONS, INJURY_OPTIONS, INJURY_SEVERITY_OPTIONS,
    INJURY_RED_FLAGS, EQUIPMENT_OPTIONS, SEX_OPTIONS, AGE_GROUP_LABELS,
)
from inference_engine import InferenceEngine
from nutrition import generate_nutrition_plan
from training import generate_training_plan, INJURY_MATRIX
from database import save_profile, list_users, db_stats
from knowledge_base import RULES, TIER_LABELS
from validation import validate_evaluation
from design_system import (
    WEB_CSS, badge_html, severity_style, tier_style, CATEGORY_ICON,
    summary_line, SEVERITY_STYLE,
)

st.set_page_config(
    page_title="FitExpert — Sistema Experto de Nutrición y Fitness",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(WEB_CSS, unsafe_allow_html=True)

# ──────────────────────────────────────────────
#  Estado de sesión web
# ──────────────────────────────────────────────
if "fx_step" not in st.session_state:
    st.session_state.fx_step = 1
if "fx" not in st.session_state:
    st.session_state.fx = {}
if "fx_result" not in st.session_state:
    st.session_state.fx_result = None
if "fx_error" not in st.session_state:
    st.session_state.fx_error = None


def _fx(key: str, default=None):
    """Lee una clave del formulario persistido entre pasos."""
    return st.session_state.fx.get(key, default)


def _fx_set(key: str, value):
    st.session_state.fx[key] = value


def _defaults(value, options: list) -> list:
    """Valores por defecto seguros para multiselect (solo los presentes en opciones)."""
    if not value:
        return []
    return [v for v in value if v in options]


SEVERITY_SORT = {k: v["order"] for k, v in SEVERITY_STYLE.items()}

# ──────────────────────────────────────────────
#  Marca + navegación lateral
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div style="display:flex;align-items:center;gap:0.7rem;margin:0.2rem 0 0.4rem;">'
        '<div style="width:44px;height:44px;border-radius:12px;background:linear-gradient(135deg,'
        ' #E94E4E, #B2183B);display:flex;align-items:center;justify-content:center;'
        'font-size:1.5rem;">💪</div>'
        '<div><div style="font-weight:800;font-size:1.25rem;letter-spacing:-0.01em;">FitExpert</div>'
        '<div style="color:#9AA8C0;font-size:0.78rem;">Sistema Experto de Nutrición y Fitness</div>'
        '</div></div>',
        unsafe_allow_html=True,
    )
    st.sidebar.divider()

    page = st.sidebar.radio(
        "Navegación",
        ["Nueva Consulta", "Historial de Consultas", "Acerca del Sistema"],
        label_visibility="collapsed",
    )
    st.sidebar.divider()
    st.sidebar.caption(
        f"Motor basado en reglas · **{len(RULES)}** reglas IF/THEN · "
        "Encadenamiento hacia adelante."
    )


def _render_header(title: str, subtitle: str):
    st.markdown(f'<div class="fx-hero">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="fx-sub">{subtitle}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════

def age_group_of(age: int) -> str:
    """Franja de edad canónica (misma lógica que user_profile)."""
    if 10 <= age <= 12:
        return "infantil"
    if 13 <= age <= 17:
        return "adolescente"
    if 18 <= age <= 29:
        return "adulto_joven"
    if 30 <= age <= 59:
        return "adulto"
    if 60 <= age <= 74:
        return "adulto_mayor"
    return "adulto_mayor_avanzado"


def _go_next(step_actual: int, n_pasos: int):
    st.session_state.fx_step = min(step_actual + 1, n_pasos)


def _go_back(step_actual: int):
    st.session_state.fx_step = max(step_actual - 1, 1)


def _run_evaluation(perfil: UserProfile, advertencias: list):
    """Ejecuta el motor y guarda el resultado en session_state."""
    motor = InferenceEngine()
    motor.run(perfil)
    save_profile(perfil)

    plan_nutricional = generate_nutrition_plan(perfil)
    rutina = generate_training_plan(perfil)

    st.session_state.fx_result = {
        "perfil": perfil,
        "motor": motor,
        "plan_nutricional": plan_nutricional,
        "rutina": rutina,
        "advertencias": advertencias,
    }


def _render_results(res: dict):
    perfil: UserProfile = res["perfil"]
    motor: InferenceEngine = res["motor"]
    plan_nutricional = res["plan_nutricional"]
    rutina = res["rutina"]
    advertencias = res["advertencias"]

    st.divider()
    st.markdown(
        f'<div class="fx-rise"><h3>📊 Resultados para <span style="color:#4EC9B0;">'
        f'{perfil.name}</span></h3>'
        f'<div style="color:#9AA8C0;">{summary_line({**motor.summary(), "suppressed": len(motor.suppressed_rules)})}</div></div>',
        unsafe_allow_html=True,
    )

    # ── Advertencias previas a todo ─────────────────────────────────────
    if advertencias:
        with st.expander("ℹ️ Consideraciones detectadas en tus datos", expanded=True):
            for w in advertencias:
                st.markdown(f"- {w}")

    if perfil.red_flags or perfil.injury_severity == "aguda":
        st.error(
            "**Suspensión de prescripción por seguridad.** Con señales de alarma "
            "o lesión aguda declarada, FitExpert no genera ejercicios. Consulta a "
            "un profesional de la salud antes de retomar la actividad física."
        )

    if perfil.engine_errors:
        with st.expander("🔧 Errores internos de evaluación (auditoría)", expanded=False):
            for e in perfil.engine_errors:
                st.code(f"[{e['id']}] {e['error']}")

    # ── Métricas base ───────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(
        f'<div class="fx-metric"><div class="v">{perfil.imc:.1f}</div>'
        f'<div class="l">IMC</div><div class="s">{perfil.imc_category}</div></div>',
        unsafe_allow_html=True,
    )
    m2.markdown(
        f'<div class="fx-metric"><div class="v">{perfil.tmb:.0f}</div>'
        f'<div class="l">TMB · reposo</div><div class="s">kcal/día</div></div>',
        unsafe_allow_html=True,
    )
    m3.markdown(
        f'<div class="fx-metric"><div class="v">{perfil.tdee:.0f}</div>'
        f'<div class="l">TDEE · gasto</div><div class="s">kcal/día</div></div>',
        unsafe_allow_html=True,
    )
    m4.markdown(
        f'<div class="fx-metric"><div class="v">{perfil.target_calories:.0f}</div>'
        f'<div class="l">Calorías objetivo</div>'
        f'<div class="s">{"↑ " if perfil.caloric_adjustment > 0 else "↓ " if perfil.caloric_adjustment < 0 else ""}'
        f'{perfil.caloric_adjustment:+.0f} kcal ajuste</div></div>',
        unsafe_allow_html=True,
    )
    if perfil.adjustment_capped:
        st.caption(f"🔒 El ajuste calórico fue limitado por seguridad: {perfil.adjustment_reason}")

    # ── Pestañas de contenido ────────────────────────────────────────────
    tab_nutricion, tab_entreno, tab_expert, tab_hechos = st.tabs([
        "🥗 Plan Nutricional",
        "🏋️ Plan de Entrenamiento",
        "💡 Módulo de Explicación",
        "🗂️ Base de Hechos (O-A-V)",
    ])

    with tab_nutricion:
        macros = plan_nutricional["macros"] or {}
        sk, h = st.columns([1, 2])
        with sk:
            st.subheader("Macronutrientes")
            if macros.get("proteinas"):
                st.metric("Proteínas", f"{macros['proteinas']:.0f} g", f"{macros.get('p_pct', 0):.0f}%")
            if macros.get("carbohidratos"):
                st.metric("Carbohidratos", f"{macros['carbohidratos']:.0f} g", f"{macros.get('c_pct', 0):.0f}%")
            if macros.get("grasas"):
                st.metric("Grasas", f"{macros['grasas']:.0f} g", f"{macros.get('g_pct', 0):.0f}%")
            if plan_nutricional.get("proteina_recomendada"):
                pr = plan_nutricional["proteina_recomendada"]
                if isinstance(pr, dict):
                    st.metric("Proteína objetivo", f"{pr.get('recomendada_g', pr.get('g', 0)):.0f} g/día")
                else:
                    st.caption(f"Proteína objetivo: {pr}")
            st.caption(
                f"{plan_nutricional['frecuencia']} comidas/día · "
                f"Dieta: {DIET_TYPES.get(plan_nutricional['tipo_dieta'])}"
            )
        with h:
            st.subheader("Sugerencias de comidas")
            plan = plan_nutricional["plan"]
            col_a, col_b = st.columns(2)
            with col_a:
                with st.expander("🌅 Desayuno", expanded=True):
                    for texto in plan["desayuno"]:
                        st.markdown(f"- {texto}")
                with st.expander("☀️ Almuerzo", expanded=True):
                    for texto in plan["almuerzo"]:
                        st.markdown(f"- {texto}")
            with col_b:
                with st.expander("🌙 Cena", expanded=True):
                    for texto in plan["cena"]:
                        st.markdown(f"- {texto}")
                with st.expander("🍎 Tentempiés", expanded=True):
                    for texto in plan["snacks"]:
                        st.markdown(f"- {texto}")
            st.info(f"💧 **Hidratación:** {plan['hidratacion']}")

        if plan_nutricional.get("sustituciones"):
            with st.expander("🔁 Sustituciones por alergias declaradas"):
                for s in plan_nutricional["sustituciones"]:
                    st.markdown(
                        f"**{ALLERGY_OPTIONS.get(s['alergeno'], s['alergeno'])}:** "
                        f"{s['substitucion']}"
                    )
                st.caption(
                    "⚠️ La seguridad frente a contaminación cruzada depende de la "
                    "lectura de etiquetas: ningún sistema puede garantizar «100 % seguro»."
                )
        st.caption(f"🩺 {plan_nutricional.get('derivacion', '')}")

    with tab_entreno:
        st.subheader(rutina["nombre"])
        st.caption(f"**Días:** {rutina['dias']} · **Tipo:** {rutina['tipo']}")

        # Rutina completa (incluye días de descanso) con 'grupo' (corrige KeyError de v2)
        for dia in rutina.get("semana", []):
            with st.expander(
                f"📋 {dia['dia']} · {dia['grupo']}",
                expanded=dia["dia"] in ("Lunes", "Martes"),
            ):
                if dia.get("descanso"):
                    st.info(dia.get("nota", "Descanso planificado."))
                    continue
                df_ejercicios = pd.DataFrame(
                    dia["ejercicios"], columns=["Ejercicio", "Series/Reps", "Músculo"]
                )
                st.dataframe(df_ejercicios, width="stretch", hide_index=True)
                st.caption(
                    f"⏱️ Descanso entre series: {dia.get('descanso_entre_series', '—')} · "
                    f"⌛ Duración: {dia.get('duracion', '—')}"
                )
                if dia.get("nota"):
                    st.markdown(f"💬 *{dia['nota']}*")

        if rutina.get("cardio_extra"):
            st.info(f"🏃 **Cardio adicional:** {rutina['cardio_extra']}")
        if rutina.get("notas"):
            st.warning(f"💡 **Nota del entrenador:** {rutina['notas']}")

        if rutina.get("lesiones_consideradas"):
            st.caption("🩹 Restricciones aplicadas por lesión: "
                       + ", ".join(rutina["lesiones_consideradas"]))
        if rutina.get("alternativas_aplicadas"):
            with st.expander("🔁 Ejercicios sustituidos por lesión"):
                for nota in rutina["alternativas_aplicadas"]:
                    st.markdown(f"- {nota}")

    with tab_expert:
        st.subheader("Módulo de Explicación")
        st.write(
            "El sistema experto dedujo las siguientes recomendaciones a partir de "
            "tus datos (encadenamiento hacia adelante). Se ordenan por severidad "
            "y jerarquía."
        )

        if perfil.conclusions:
            orden = sorted(
                perfil.conclusions,
                key=lambda c: (SEVERITY_SORT.get(c.get("severity", "info"), 9),
                               -(c.get("priority") or 0)),
            )
            for c in orden:
                explicacion = next(
                    (e["explanation"] for e in perfil.explanations if e["id"] == c["id"]),
                    "",
                )
                sev = severity_style(c.get("severity", "info"))
                cat_icon = CATEGORY_ICON.get(c.get("category", ""), "🩺")
                badge = badge_html(c.get("severity", "info"), c.get("tier", ""))
                refs = c.get("references") or []
                refs_txt = " · ".join(refs) if refs else "—"

                st.markdown(
                    f'<div class="fx-card fx-card--{c.get("severity", "info")} fx-rise">'
                    f'<div style="display:flex;justify-content:space-between;gap:0.5rem;flex-wrap:wrap;">'
                    f'<b>{cat_icon} [{c.get("id", "")}] {c.get("description", "")}</b>'
                    f'<span>{badge}</span></div>'
                    f'<p style="margin:0.4rem 0 0.15rem;">👉 <b>Recomendación:</b> {c.get("conclusion", "")}</p>'
                    f'<p style="color:#9AA8C0;font-size:0.9em;margin:0.15rem 0;">'
                    f'<i>Razonamiento:</i> {explicacion}</p>'
                    f'<p style="color:#4EC9B0;font-size:0.82em;margin:0.15rem 0;">'
                    f'📚 {refs_txt}</p>'
                    + (f'<p style="color:#B48CF2;font-size:0.85em;margin:0.15rem 0;">'
                       f'↪️ <b>Alternativa:</b> {c.get("alternative", "")}</p>' if c.get("alternative") else "")
                    + f'</div>',
                    unsafe_allow_html=True,
                )

            if perfil.suppressed:
                with st.expander("🚫 Reglas suprimidas por conflicto / jerarquía"):
                    for s in perfil.suppressed:
                        st.markdown(
                            f"- **[{s.get('id', '')}]** suprimida por"
                            f" **[{s.get('suppressed_by', '')}]** — {s.get('reason', '')}"
                        )
        else:
            st.info("No se activaron reglas específicas para este perfil.")

        st.caption(
            f"{summary_line({**motor.summary(), 'suppressed': len(motor.suppressed_rules)})} · "
            f"{len(RULES)} reglas evaluadas"
        )

    with tab_hechos:
        st.subheader("Base de Hechos (Representación Objeto-Atributo-Valor)")
        st.write("Cada hecho expresa un atributo del objeto evaluado:")
        st.json(perfil.facts)
        st.caption(
            "Los hechos son el snapshot de datos que el motor evaluó. La base de "
            "hechos no guarda contraseñas ni datos externos."
        )


# ══════════════════════════════════════════════
#  PÁGINA: NUEVA CONSULTA
# ══════════════════════════════════════════════
if page == "Nueva Consulta":
    _render_header(
        "Evaluación Física Personalizada",
        "Cuatro pasos. Cada paso se valida, y el motor explica cada recomendación.",
    )

    # ── Stepper ─────────────────────────────────────────────────────────
    pasos = ["Datos personales", "Entrenamiento", "Salud y lesiones", "Nutrición"]
    n_pasos = len(pasos)
    step = st.session_state.fx_step
    cols = st.columns(n_pasos, gap="small")
    for i, nombre in enumerate(pasos, start=1):
        cls = "fx-step active" if i == step else ("fx-step done" if i < step else "fx-step")
        cols[i - 1].markdown(
            f'<div class="{cls}"><span style="font-size:0.9em;">{i}</span> · {nombre}</div>',
            unsafe_allow_html=True,
        )

    st.session_state.fx_step = step  # asegurar tipo

    errores: dict = {}
    advertencias: list = []

    # ── PASO 1 · Datos personales ───────────────────────────────────────
    if step == 1:
        c1, c2 = st.columns(2)
        with c1:
            nombre = st.text_input(
                "Nombre *", value=_fx("name", "Usuario"),
                help="Como aparecerá en las recomendaciones y el historial.",
            )
            _fx_set("name", nombre.strip() or "Usuario")

            csex, cedad = st.columns(2)
            with csex:
                sexo = st.selectbox(
                    "Sexo biológico *",
                    list(SEX_OPTIONS.values()),
                    index=list(SEX_OPTIONS.values()).index(_fx("sex", "masculino")),
                )
            with cedad:
                edad = st.number_input(
                    "Edad (años) *", min_value=10, max_value=110,
                    value=_fx("age", 25),
                    help="El sistema opera de 10 a 110 años.",
                )
            _fx_set("sex", sexo)
            _fx_set("age", int(edad))
        with c2:
            cpeso, calt = st.columns(2)
            with cpeso:
                peso = st.number_input(
                    "Peso (kg) *", min_value=20.0, max_value=400.0,
                    value=float(_fx("weight", 70.0)), step=0.1,
                )
            with calt:
                altura = st.number_input(
                    "Estatura (cm) *", min_value=100.0, max_value=250.0,
                    value=float(_fx("height", 170.0)), step=0.1,
                )
            _fx_set("weight", peso)
            _fx_set("height", altura)

            grasa = st.number_input(
                "% de grasa corporal (opcional)",
                min_value=0.0, max_value=70.0,
                value=float(_fx("body_fat_pct", 0.0)), step=0.1,
                help="Deja en 0 si no lo conoces.",
            )
            _fx_set("body_fat_pct", grasa)

            edad_val = int(edad)
            st.caption(
                f"Franja de edad: "
                f"{AGE_GROUP_LABELS.get(age_group_of(edad_val), '—')}"
            )

        st.button(
            "Siguiente →", key="fx_next_1", width="stretch",
            on_click=lambda: _go_next(1, n_pasos),
        )

    # ── PASO 2 · Entrenamiento ──────────────────────────────────────────
    elif step == 2:
        c1, c2 = st.columns(2)
        with c1:
            obj_vals = list(OBJECTIVE_LABELS.values())
            objetivo = st.selectbox(
                "Objetivo corporal *", obj_vals,
                index=obj_vals.index(_fx("objective_label", obj_vals[0])),
            )
            _fx_set("objective", list(OBJECTIVE_LABELS.keys())[obj_vals.index(objetivo)])
            _fx_set("objective_label", objetivo)

            act_vals = list(ACTIVITY_LABELS.values())
            actividad = st.selectbox(
                "Nivel de actividad *", act_vals,
                index=act_vals.index(_fx("activity_label", act_vals[2])),
            )
            _fx_set("activity_level", list(ACTIVITY_LABELS.keys())[act_vals.index(actividad)])
            _fx_set("activity_label", actividad)
        with c2:
            exp_vals = list(EXPERIENCE_LABELS.values())
            experiencia = st.selectbox(
                "Experiencia *", exp_vals,
                index=exp_vals.index(_fx("experience_label", exp_vals[0])),
            )
            _fx_set("experience", list(EXPERIENCE_LABELS.keys())[exp_vals.index(experiencia)])
            _fx_set("experience_label", experiencia)

            lugar_vals = list(TRAINING_PLACE_LABELS.values())
            lugar = st.selectbox(
                "Lugar de entrenamiento *", lugar_vals,
                index=lugar_vals.index(_fx("place_label", lugar_vals[1])),
            )
            _fx_set("training_place", list(TRAINING_PLACE_LABELS.keys())[lugar_vals.index(lugar)])
            _fx_set("place_label", lugar)

        equipo = st.multiselect(
            "Equipamiento disponible (si entrenas en casa)",
            list(EQUIPMENT_OPTIONS.values()),
            default=_defaults(_fx("equipment_labels", []), list(EQUIPMENT_OPTIONS.values())),
            help="En gimnasio se asume máquinas, barras y mancuernas.",
        )
        _fx_set("equipment_labels", list(equipo))
        _fx_set("equipment", [list(EQUIPMENT_OPTIONS.keys())[list(EQUIPMENT_OPTIONS.values()).index(e)]
                              for e in equipo])

        nav1, nav2 = st.columns(2)
        nav1.button("← Anterior", key="fx_back_2", width="stretch",
                    on_click=lambda: _go_back(2))
        nav2.button("Siguiente →", key="fx_next_2", width="stretch",
                    on_click=lambda: _go_next(2, n_pasos))

    # ── PASO 3 · Salud y lesiones ───────────────────────────────────────
    elif step == 3:
        st.markdown('<p class="fx-section-title">Lesiones y limitaciones</p>',
                    unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            inj_labels = list(INJURY_OPTIONS.values())
            lesiones = st.multiselect(
                "Zonas con molestia o lesión",
                inj_labels,
                default=_defaults(_fx("injuries_labels", []), inj_labels),
            )
            _fx_set("injuries_labels", list(lesiones))
            _fx_set("injuries", [list(INJURY_OPTIONS.keys())[inj_labels.index(l)] for l in lesiones])

            sev_vals = list(INJURY_SEVERITY_OPTIONS.values())
            severidad = st.selectbox(
                "Intensidad de las molestias *",
                sev_vals,
                index=sev_vals.index(
                    INJURY_SEVERITY_OPTIONS.get(_fx("injury_severity", "ninguna"), sev_vals[0])
                ),
                help="«Dolor agudo actual» suspende la prescripción de ejercicio.",
            )
            _fx_set("injury_severity", list(INJURY_SEVERITY_OPTIONS.keys())[sev_vals.index(severidad)])
        with c2:
            balance = st.checkbox(
                "Problemas de equilibrio / historial de caídas",
                value=bool(_fx("balance_issues", False)),
            )
            _fx_set("balance_issues", balance)
            st.caption("Esta información reorienta la rutina hacia prevención de caídas.")

        st.markdown('<p class="fx-section-title">Señales de alarma</p>',
                    unsafe_allow_html=True)
        rf_labels = list(INJURY_RED_FLAGS.values())
        red_flags = st.multiselect(
            "¿Presentas alguno de estos síntomas?",
            rf_labels,
            default=_defaults(_fx("red_flags_labels", []), rf_labels),
            help="Si marcas cualquiera, el sistema NO prescribirá ejercicio.",
        )
        _fx_set("red_flags_labels", list(red_flags))
        _fx_set("red_flags", [list(INJURY_RED_FLAGS.keys())[rf_labels.index(r)] for r in red_flags])

        if _fx("red_flags"):
            st.error(
                "Detectadas señales de alarma: la rutina de entrenamiento se "
                "suspenderá y se recomendará evaluación médica antes de actividad física."
            )

        nav1, nav2 = st.columns(2)
        nav1.button("← Anterior", key="fx_back_3", width="stretch",
                    on_click=lambda: _go_back(3))
        nav2.button("Siguiente →", key="fx_next_3", width="stretch",
                    on_click=lambda: _go_next(3, n_pasos))

    # ── PASO 4 · Nutrición ──────────────────────────────────────────────
    elif step == 4:
        c1, c2 = st.columns(2)
        with c1:
            dieta_labels = list(DIET_TYPES.values())
            dieta = st.selectbox(
                "Tipo de dieta *", dieta_labels,
                index=dieta_labels.index(DIET_TYPES.get(_fx("diet_type", "omnivoro"))),
            )
            _fx_set("diet_type", list(DIET_TYPES.keys())[dieta_labels.index(dieta)])

            al_labels = list(ALLERGY_OPTIONS.values())
            alergias = st.multiselect(
                "Alergias alimentarias",
                al_labels,
                default=_defaults(_fx("allergies_labels", []), al_labels),
                help="Alergia = exclusión estricta del alimento y sus derivados.",
            )
            _fx_set("allergies_labels", list(alergias))
            _fx_set("allergies", [list(ALLERGY_OPTIONS.keys())[al_labels.index(a)] for a in alergias])

            if _fx("allergies"):
                st.caption(
                    "Las alergias excluyen el alimento completo. El sistema nunca "
                    "afirma «100 % seguro»: la contaminación cruzada depende de las etiquetas."
                )
        with c2:
            int_labels = list(INTOLERANCE_OPTIONS.values())
            intolerancias = st.multiselect(
                "Intolerancias digestivas",
                int_labels,
                default=_defaults(_fx("intolerances_labels", []), int_labels),
            )
            _fx_set("intolerances_labels", list(intolerancias))
            _fx_set("intolerances", [list(INTOLERANCE_OPTIONS.keys())[int_labels.index(i)]
                                     for i in intolerancias])

            pref_labels = list(PREFERENCE_OPTIONS.values())
            preferencias = st.multiselect(
                "Preferencias de consumo",
                pref_labels,
                default=_defaults(_fx("preferences_labels", []), pref_labels),
            )
            _fx_set("preferences_labels", list(preferencias))
            _fx_set("preferences", [list(PREFERENCE_OPTIONS.keys())[pref_labels.index(p)]
                                    for p in preferencias])

        with st.expander("Más opciones"):
            comidas = st.selectbox(
                "Comidas al día", [3, 4, 5], index=int(_fx("meal_frequency", 3)) - 3,
            )
            _fx_set("meal_frequency", int(comidas))
            notas = st.text_area(
                "Observaciones (opcional)", value=_fx("notes", ""),
                max_chars=300, help="Hasta 300 caracteres.",
            )
            _fx_set("notes", notas)

        if _fx("diet_type") == "vegano" and "soja" in _fx("allergies", []):
            st.warning(
                "Dieta vegana + alergia a la soja: la proteína se apoya en "
                "legumbres, quinoa y frutos secos (según tolerancia). Considera supervisión nutricional."
            )

        nav1, nav2 = st.columns(2)
        nav1.button("← Anterior", key="fx_back_4", width="stretch",
                    on_click=lambda: _go_back(4))
        generar = nav2.button(
            "Generar recomendaciones expertas 🚀",
            key="fx_generate", width="stretch",
        )

        if generar:
            # ── Validación cruzada completa ─────────────────────────────
            datos = {
                "name": _fx("name", "Usuario"),
                "age": _fx("age", 25),
                "sex": _fx("sex", "masculino"),
                "weight": _fx("weight", 70.0),
                "height": _fx("height", 170.0),
                "body_fat_pct": _fx("body_fat_pct", 0.0),
                "objective": _fx("objective", "mantenimiento"),
                "activity_level": _fx("activity_level", "moderado"),
                "experience": _fx("experience", "principiante"),
                "training_place": _fx("training_place", "gimnasio"),
                "diet_type": _fx("diet_type", "omnivoro"),
                "meal_frequency": _fx("meal_frequency", 3),
                "injuries": _fx("injuries", []),
                "equipment": _fx("equipment", []),
                "allergies": _fx("allergies", []),
                "intolerances": _fx("intolerances", []),
                "preferences": _fx("preferences", []),
                "red_flags": _fx("red_flags", []),
                "injury_severity": _fx("injury_severity", "ninguna"),
                "balance_issues": _fx("balance_issues", False),
                "notes": _fx("notes", ""),
            }
            values, errores, advertencias = validate_evaluation(datos)

            if errores:
                st.session_state.fx_error = errores
            else:
                st.session_state.fx_error = None
                perfil = UserProfile(**values)
                _run_evaluation(perfil, advertencias)

    # ── Resultados ──────────────────────────────────────────────────────
    if st.session_state.fx_error:
        st.markdown("### ⚠️ Antes de generar, revisa estos campos")
        for campo, msg in st.session_state.fx_error.items():
            st.error(f"**{campo.capitalize()}:** {msg}")

    if st.session_state.fx_result:
        _render_results(st.session_state.fx_result)

    st.divider()
    st.caption(
        "⚠️ Este sistema es una herramienta informativa y académica. No "
        "sustituye la evaluación ni el seguimiento de un profesional de la salud."
    )

# ──────────────────────────────────────────────
#  PÁGINA: HISTORIAL
# ──────────────────────────────────────────────
elif page == "Historial de Consultas":
    _render_header("Historial de Consultas", "Todas las evaluaciones registradas en la base de conocimiento.")

    stats = db_stats()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Consultas totales", stats.get("total_sesiones", stats.get("total_consultas", 0)))
    m2.metric("Usuarios únicos", stats.get("usuarios_unicos", 0))
    m3.metric("Reglas en la base", len(RULES))
    m4.metric("Tiers de conocimiento", len(TIER_LABELS))

    por_objetivo = stats.get("por_objetivo", {}) or {}
    if por_objetivo:
        st.subheader("Consultas por objetivo")
        odf = pd.DataFrame(
            {"Objetivo": [OBJECTIVE_LABELS.get(k, k) for k in por_objetivo],
             "Consultas": list(por_objetivo.values())}
        ).set_index("Objetivo")
        st.bar_chart(odf, height=280)

    users = list_users()
    st.subheader("Consultas registradas")
    if not users:
        st.info("No hay consultas registradas todavía.")
    else:
        df = pd.DataFrame(users)
        cols_show = [c for c in
                     ["name", "age", "sex", "imc", "imc_category", "objective", "created_at"]
                     if c in df.columns]
        if "objective" in df.columns:
            df["Objetivo"] = df["objective"].map(OBJECTIVE_LABELS).fillna(df["objective"])
        df_show = df[cols_show].rename(columns={
            "name": "Nombre", "age": "Edad", "sex": "Sexo", "imc": "IMC",
            "imc_category": "Categoría", "objective": "Objetivo",
            "created_at": "Fecha Consulta",
        })
        st.dataframe(df_show, width="stretch", hide_index=True)

        csv_data = df_show.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "⬇️ Descargar CSV", data=csv_data,
            file_name="fitexpert_historial.csv", mime="text/csv",
        )

    st.divider()
    st.caption(
        "Se registran datos agregados sin exponer información de otros usuarios. "
        "Este historial pertenece a este prototipo local de demostración."
    )

# ──────────────────────────────────────────────
#  PÁGINA: ACERCA DEL SISTEMA
# ──────────────────────────────────────────────
else:
    _render_header("Acerca del Sistema Experto", "Arquitectura, reglas y límites del sistema.")

    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown(
            f"""
FitExpert es un **Sistema Experto Basado en Reglas** para nutrición y
acondicionamiento físico. Conserva la esencia clásica de los sistemas expertos:

*   ⚙️ **Base de conocimiento:** **{len(RULES)} reglas** lógicas IF/THEN organizadas en
    **{len(TIER_LABELS)} jerarquías**, desde **Seguridad** hasta **Seguimiento**.
*   🔁 **Motor de inferencia:** **Encadenamiento hacia adelante** (*forward chaining*)
    que evalúa el perfil contra las reglas y resuelve conflictos por jerarquía.
*   🧩 **Representación del conocimiento:** paradigma **Objeto-Atributo-Valor (O-A-V)**.
*   💡 **Módulo de explicación:** cada recomendación expone su razonamiento,
    severidad, referencias reales y alternativa.
*   🛡️ **Seguridad:** jerarquía SEGURIDAD > CONTRAINDICACIONES > EDAD > condición
    física > objetivo > preferencias; las señales de alarma suspenden la prescripción.
"""
        )

        # Jerarquía explicada
        st.markdown("#### Jerarquía de reglas")
        for tier, label in TIER_LABELS.items():
            ts = tier_style(tier)
            n = sum(1 for r in RULES if r.tier == tier)
            st.markdown(
                f'<div class="fx-card fx-card--info">'
                f'<b style="color:{ts["color"]}">{ts["icon"]} {label}</b> '
                f'<span style="color:#9AA8C0;">· {n} reglas</span></div>',
                unsafe_allow_html=True,
            )

    with c2:
        st.markdown("#### Modo de evaluación")
        st.code(
            "IF condición(perfil) THEN\n"
            "    conclusión = regla\n"
            "    explicación = justificación\n"
            "    severidad = crítica|alta|media|baja\n"
            "    referencias = [WHO|CDC|ACSM|AAP ...]",
            language=None,
        )
        st.markdown("#### Fuentes citadas")
        st.markdown(
            "Las reglas referencian únicamente fuentes reales: **OMS (WHO)**, "
            "**CDC**, **AAP (Academia Americana de Pediatría)** y **ACSM** "
            "(American College of Sports Medicine), según el dominio."
        )
        st.markdown("#### Consideraciones")
        st.warning(
            "Software académico y demostrativo. Las recomendaciones no sustituyen "
            "el consejo, diagnóstico o tratamiento de un profesional de la salud certificado."
        )

    st.divider()
    st.caption(
        "Desarrollado en Python 🐍 · Motor: encadenamiento hacia adelante · Interfaz web: Streamlit · "
        f"Reglas activas: {len(RULES)}"
    )


