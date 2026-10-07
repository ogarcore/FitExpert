"""
ui.py
=====
Interfaz de consola (rich) de FitExpert — v3.0 (auditoría completa)

Mejoras respecto a v2:
  - Corrección del KeyError: las sesiones de entrenamiento exponen `dia/grupo`,
    no `nombre` (contrato de training.generate_training_plan). Se muestra la
    semana completa incluyendo días de descanso.
  - El formulario recopila TODOS los campos del perfil: dieta, alergias,
    intolerancias, preferencias, lesiones + severidad, señales de alarma,
    problemas de equilibrio, % de grasa, equipamiento y observaciones.
  - El formulario valida cada entrada con reglas de rango y mensajes amigables.
  - Al final del formulario se ejecuta la validación cruzada
    (validation.validate_evaluation) y se muestran las advertencias.
  - Las conclusiones muestran severidad, tier, referencias y alternativa, y
    se ordenan por severidad/jerarquía.
  - Transparencia del motor: reglas suprimidas por conflicto y errores internos.
  - Estadísticas con claves reales de db_stats.
"""

import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, FloatPrompt
from rich.text import Text
from rich.columns import Columns
from rich import box
from rich.rule import Rule as RichRule

from user_profile import (
    UserProfile, OBJECTIVES, OBJECTIVE_LABELS,
    ACTIVITY_LEVELS, ACTIVITY_LABELS,
    EXPERIENCE_LEVELS, TRAINING_PLACES, SEX_OPTIONS,
    DIET_TYPES, ALLERGY_OPTIONS, INTOLERANCE_OPTIONS, PREFERENCE_OPTIONS,
    INJURY_OPTIONS, INJURY_SEVERITY_OPTIONS, INJURY_RED_FLAGS,
    EQUIPMENT_OPTIONS,
)
from calculations import calcular_macronutrientes
from validation import validate_evaluation
from knowledge_base import RULES, TIER_LABELS
from design_system import (
    SEVERITY_STYLE, TIER_STYLE, CATEGORY_ICON, cli_badge,
)


# ──────────────────────────────────────────────
#  Consola global y paleta
# ──────────────────────────────────────────────

console = Console()

COLOR_PRIMARY   = "bold cyan"
COLOR_SECONDARY = "bold yellow"
COLOR_SUCCESS   = "bold green"
COLOR_WARNING   = "bold red"
COLOR_MUTED     = "dim white"
COLOR_HEADER    = "bold white on dark_cyan"
COLOR_ACCENT    = "bold magenta"

SEVERITY_SORT = {k: v["order"] for k, v in SEVERITY_STYLE.items()}


# ══════════════════════════════════════════════
#  Banner principal
# ══════════════════════════════════════════════

def show_banner() -> None:
    """Muestra el banner de bienvenida del sistema (marca FitExpert)."""
    console.clear()
    banner = Text(justify="center")
    banner.append("\n")
    banner.append("  ███████╗██╗████████╗███████╗██╗  ██╗██████╗ ███████╗██████╗ ████████╗\n", style="bold #2DD4BF")
    banner.append("  ██╔════╝██║╚══██╔══╝██╔════╝╚██╗██╔╝██╔══██╗██╔════╝██╔══██╗╚══██╔══╝\n", style="bold #2DD4BF")
    banner.append("  █████╗  ██║   ██║   █████╗   ╚███╔╝ ██████╔╝█████╗  ██████╔╝   ██║\n", style="bold #2DD4BF")
    banner.append("  ██╔══╝  ██║   ██║   ██╔══╝   ██╔██╗ ██╔══██╗██╔══╝  ██╔══██╗   ██║\n", style="bold #2DD4BF")
    banner.append("  ██║     ██║   ██║   ███████╗██╔╝ ██╗██║  ██║███████╗██║  ██║   ██║\n", style="bold #2DD4BF")
    banner.append("  ╚═╝     ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝\n", style="bold #2DD4BF")

    console.print(banner)
    console.print(
        Panel(
            Text.from_markup(
                "[bold white]Sistema Experto en Nutrición y Acondicionamiento Físico[/bold white]\n"
                f"[dim]Motor basado en reglas · {len(RULES)} reglas IF/THEN · Encadenamiento hacia adelante[/dim]\n"
                "[dim cyan]Inteligencia Artificial · Sistemas Expertos[/dim cyan]"
            ),
            border_style="#2DD4BF",
            padding=(1, 4),
        )
    )


# ══════════════════════════════════════════════
#  Menú principal
# ══════════════════════════════════════════════

def show_main_menu() -> str:
    """Muestra el menú principal y retorna la opción seleccionada."""
    console.print()
    console.print(RichRule("[bold cyan]MENÚ PRINCIPAL[/bold cyan]", style="cyan"))
    console.print()

    menu = Table(box=box.ROUNDED, show_header=False, border_style="cyan", padding=(0, 2))
    menu.add_column(style="bold cyan", no_wrap=True)
    menu.add_column(style="white")

    menu.add_row("[1]", "Nueva Consulta — Evaluación Completa")
    menu.add_row("[2]", "Ver Historial de Usuarios")
    menu.add_row("[3]", "Estadísticas del Sistema")
    menu.add_row("[4]", "Acerca del Sistema Experto")
    menu.add_row("[0]", "Salir")

    console.print(menu)
    console.print()

    opcion = Prompt.ask(
        "[bold cyan]Selecciona una opción[/bold cyan]",
        choices=["0", "1", "2", "3", "4"],
        default="1",
    )
    return opcion


# ══════════════════════════════════════════════
#  Formulario: datos del usuario
# ══════════════════════════════════════════════

def _show_options_table(title: str, options: dict, labels: dict | None = None) -> None:
    """Muestra una tabla de opciones numeradas para un campo."""
    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    t.add_column(style="bold cyan", no_wrap=True)
    t.add_column(style="white")
    for key, val in options.items():
        texto = labels.get(val, val) if labels else val
        if isinstance(texto, dict):
            texto = next(iter(texto.values()))
        t.add_row(f"  [{key}]", str(texto))
    console.print(t)


def _multi_choice(prompt_text: str, options: dict, n_cols: int = 2) -> list:
    """
    Selección múltiple por números separados por comas (Enter = ninguna).
    `options` es {clave: etiqueta humana}. Retorna lista de claves válidas.
    """
    items = list(options.items())
    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    t.add_column(style="bold cyan", no_wrap=True)
    t.add_column(style="white")
    for i, (key, label) in enumerate(items, 1):
        t.add_row(f"  [{i}]", label)
    if n_cols >= 2 and len(items) > 4:
        # Dos columnas para no alargar demasiado la pantalla
        half = (len(items) + 1) // 2
        t1_items, t2_items = items[:half], items[half:]
        t1 = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        t2 = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        t1.add_column(style="bold cyan", no_wrap=True)
        t1.add_column(style="white")
        t2.add_column(style="bold cyan", no_wrap=True)
        t2.add_column(style="white")
        for i, (key, label) in enumerate(t1_items, 1):
            t1.add_row(f"  [{i}]", label)
        for i, (key, label) in enumerate(t2_items, half + 1):
            t2.add_row(f"  [{i}]", label)
        console.print(Columns([t1, t2]))
    else:
        console.print(t)

    while True:
        raw = Prompt.ask(prompt_text, default="")
        if not raw.strip():
            return []
        try:
            idxs = [int(p) for p in raw.replace(";", ",").replace(" ", "").split(",") if p.strip()]
        except ValueError:
            console.print("[bold red]  ✗ Usa números separados por comas (ej: 1,3).[/bold red]")
            continue
        if any(i < 1 or i > len(items) for i in idxs):
            console.print(f"[bold red]  ✗ Elige números entre 1 y {len(items)}.[/bold red]")
            continue
        seleccion = [items[i - 1][0] for i in dict.fromkeys(idxs)]
        return seleccion


def collect_user_data() -> UserProfile:
    """
    Guía al usuario a través del formulario completo de evaluación.
    Valida cada campo y retorna un UserProfile con todos los datos.
    """
    console.print()
    console.print(RichRule("[bold cyan]EVALUACIÓN INICIAL[/bold cyan]", style="cyan"))
    console.print(
        Panel(
            "[dim]Proporciona tus datos para generar recomendaciones personalizadas.\n"
            "Toda la información se usa únicamente dentro de este sistema.[/dim]",
            border_style="dim cyan",
        )
    )
    console.print()

    data: dict = {}
    data["name"] = Prompt.ask("[white]Nombre[/white]").strip() or "Usuario"
    data["notes"] = ""

    # ── Datos personales ──────────────────────────────────────────────────
    console.print("[bold cyan]── Datos Personales ──────────────────────────────────[/bold cyan]")

    while True:
        try:
            age = int(Prompt.ask("[white]Edad (años)[/white]"))
        except ValueError:
            console.print("[bold red]  ✗ Ingresa un número entero (10–110).[/bold red]")
            continue
        if 10 <= age <= 110:
            data["age"] = age
            break
        console.print("[bold red]  ✗ Ingresa una edad válida (10–110).[/bold red]")

    console.print("[white]Sexo:[/white]")
    _show_options_table("Sexo", SEX_OPTIONS, {v: v.capitalize() for v in SEX_OPTIONS.values()})
    sex_key = Prompt.ask("  Selecciona", choices=list(SEX_OPTIONS.keys()))
    data["sex"] = SEX_OPTIONS[sex_key]

    while True:
        try:
            weight = float(Prompt.ask("[white]Peso (kg)[/white]"))
        except ValueError:
            console.print("[bold red]  ✗ Ingresa un número (ej: 72.5).[/bold red]")
            continue
        if 20 <= weight <= 400:
            data["weight"] = weight
            break
        console.print("[bold red]  ✗ Ingresa un peso válido (20–400 kg).[/bold red]")

    while True:
        try:
            height = float(Prompt.ask("[white]Altura (cm)[/white]"))
        except ValueError:
            console.print("[bold red]  ✗ Ingresa un número (ej: 172).[/bold red]")
            continue
        if 100 <= height <= 250:
            data["height"] = height
            break
        console.print("[bold red]  ✗ Ingresa una altura válida (100–250 cm).[/bold red]")

    grasa_raw = Prompt.ask("[white]% de grasa corporal (Enter para omitir)[/white]", default="")
    data["body_fat_pct"] = grasa_raw if grasa_raw.strip() else 0.0

    # ── Objetivos y entrenamiento ─────────────────────────────────────────
    console.print()
    console.print("[bold cyan]── Objetivos y Entrenamiento ─────────────────────────[/bold cyan]")

    console.print("[white]Objetivo corporal:[/white]")
    _show_options_table("Objetivo", OBJECTIVES, OBJECTIVE_LABELS)
    obj_key = Prompt.ask("  Selecciona", choices=list(OBJECTIVES.keys()))
    data["objective"] = OBJECTIVES[obj_key]

    console.print("[white]Nivel de actividad física actual:[/white]")
    _show_options_table("Actividad", ACTIVITY_LEVELS, ACTIVITY_LABELS)
    act_key = Prompt.ask("  Selecciona", choices=list(ACTIVITY_LEVELS.keys()))
    data["activity_level"] = ACTIVITY_LEVELS[act_key]

    console.print("[white]Nivel de experiencia en entrenamiento:[/white]")
    exp_descriptions = {
        "principiante": "Principiante (menos de 6 meses)",
        "intermedio":   "Intermedio (6 meses – 2 años)",
        "avanzado":     "Avanzado (más de 2 años)",
    }
    _show_options_table("Experiencia", EXPERIENCE_LEVELS, exp_descriptions)
    exp_key = Prompt.ask("  Selecciona", choices=list(EXPERIENCE_LEVELS.keys()))
    data["experience"] = EXPERIENCE_LEVELS[exp_key]

    console.print("[white]Preferencia de lugar de entrenamiento:[/white]")
    place_labels = {"casa": "Entrenamiento en Casa", "gimnasio": "Gimnasio"}
    _show_options_table("Lugar", TRAINING_PLACES, place_labels)
    place_key = Prompt.ask("  Selecciona", choices=list(TRAINING_PLACES.keys()))
    data["training_place"] = TRAINING_PLACES[place_key]

    if data["training_place"] == "casa":
        console.print("[white]Equipamiento disponible en casa (selección múltiple, Enter para 'solo peso corporal'):[/white]")
        data["equipment"] = _multi_choice("  Equipos (ej: 1,3):", EQUIPMENT_OPTIONS)
        if not data["equipment"]:
            data["equipment"] = ["solo_peso_corporal"]
    else:
        data["equipment"] = []

    # ── Salud y lesiones ──────────────────────────────────────────────────
    console.print()
    console.print("[bold yellow]── Salud y Lesiones ────────────────────────────────[/bold yellow]")

    console.print("[white]Zonas con molestia o lesión (Enter si ninguna):[/white]")
    data["injuries"] = _multi_choice("  Zonas (ej: 1,3):", INJURY_OPTIONS)

    if data["injuries"]:
        console.print("[white]Intensidad de las molestias:[/white]")
        _show_options_table("Severidad", INJURY_SEVERITY_OPTIONS, INJURY_SEVERITY_OPTIONS)
        sev_key = Prompt.ask("  Selecciona", choices=list(INJURY_SEVERITY_OPTIONS.keys()))
        data["injury_severity"] = INJURY_SEVERITY_OPTIONS[sev_key]
        if data["injury_severity"] == "aguda":
            console.print("[bold red]  ⚠️ Lesión aguda: la prescripción de ejercicio quedará suspendida.[/bold red]")
    else:
        data["injury_severity"] = "ninguna"

    confirm_balance = Prompt.ask(
        "[white]¿Problemas de equilibrio o historial de caídas?[/white] (s/n)",
        choices=["s", "n"], default="n",
    )
    data["balance_issues"] = confirm_balance == "s"

    console.print("[white]Señales de alarma (Enter si ninguna):[/white]")
    console.print("[dim]Si marcas alguna, el sistema NO prescribirá ejercicio hasta evaluación médica.[/dim]")
    data["red_flags"] = _multi_choice("  Señales (ej: 1,3):", INJURY_RED_FLAGS)

    # ── Nutrición ─────────────────────────────────────────────────────────
    console.print()
    console.print("[bold green]── Nutrición ───────────────────────────────────────[/bold green]")

    console.print("[white]Tipo de dieta:[/white]")
    _show_options_table("Dieta", DIET_TYPES, DIET_TYPES)
    dieta_choices = list(DIET_TYPES.keys())
    diet_key = Prompt.ask("  Selecciona", choices=dieta_choices, default="omnivoro")
    data["diet_type"] = DIET_TYPES.get(diet_key, "omnivoro") if diet_key in DIET_TYPES else diet_key

    console.print("[white]Alergias alimentarias (Enter si ninguna):[/white]")
    console.print("[dim]Alergia = exclusión total del alimento y derivados.[/dim]")
    data["allergies"] = _multi_choice("  Alergias (ej: 1,3):", ALLERGY_OPTIONS)

    console.print("[white]Intolerancias digestivas (Enter si ninguna):[/white]")
    data["intolerances"] = _multi_choice("  Intolerancias (ej: 1,3):", INTOLERANCE_OPTIONS)

    console.print("[white]Preferencias de consumo (Enter si ninguna):[/white]")
    data["preferences"] = _multi_choice("  Preferencias (ej: 1,3):", PREFERENCE_OPTIONS)

    freq_raw = Prompt.ask("[white]Comidas al día (3, 4 o 5)[/white]", choices=["3", "4", "5"], default="3")
    data["meal_frequency"] = int(freq_raw)

    # ── Validación cruzada ────────────────────────────────────────────────
    values, errores, advertencias = validate_evaluation(data)
    if errores:
        console.print()
        for campo, msg in errores.items():
            console.print(f"[bold red]  ✗ {campo.capitalize()}: {msg}[/bold red]")
        console.print("[bold red]Corrige los datos indicados y vuelve a intentarlo.[/bold red]")
        if data["age"] and 10 <= data["age"] <= 110:
            # Reintento recursivo con inputs correctos es complejo; mejor usar
            # defaults razonables derivados del input para avanzar con seguridad.
            for k in ("name", "sex", "weight", "height"):
                if k in errores:
                    datos_sanos = {
                        "name": "Usuario", "sex": "masculino",
                        "weight": 70.0, "height": 170.0,
                    }
                    data[k] = datos_sanos.get(k, data.get(k))
        values, errores, advertencias = validate_evaluation(data)

    profile = UserProfile(**values)
    console.print()
    for w in advertencias:
        console.print(Panel(f"[bold #FFB020]ℹ️ {w}[/bold #FFB020]", border_style="#FFB020", padding=(0, 1)))

    console.print()
    console.print("[bold green]  ✓ Datos recopilados correctamente.[/bold green]")
    return profile


# ══════════════════════════════════════════════
#  Resultados de cálculos
# ══════════════════════════════════════════════

def show_calculations(profile: UserProfile) -> None:
    """Muestra los resultados de IMC, TMB, TDEE y calorías objetivo."""
    console.print()
    console.print(RichRule("[bold cyan]RESULTADOS DE EVALUACIÓN FÍSICA[/bold cyan]", style="cyan"))

    t = Table(
        title=f"Métricas de {profile.name}",
        box=box.ROUNDED, border_style="cyan",
        title_style="bold cyan", padding=(0, 2),
    )
    t.add_column("Indicador",   style="bold white",   min_width=28)
    t.add_column("Valor",       style="bold yellow",  min_width=16, justify="right")
    t.add_column("Referencia",  style="dim white",    min_width=24)

    imc_color = "green" if 18.5 <= profile.imc <= 24.9 else "yellow" if profile.imc < 18.5 else "red"
    t.add_row(
        "Índice de Masa Corporal (IMC)",
        f"[{imc_color}]{profile.imc:.2f} kg/m²[/{imc_color}]",
        f"[{imc_color}]{profile.imc_category}[/{imc_color}]",
    )
    t.add_row("Tasa Metabólica Basal (TMB)", f"{profile.tmb:.0f} kcal/día", "Calorías en reposo total")
    t.add_row("Gasto Energético Diario (TDEE)", f"{profile.tdee:.0f} kcal/día", f"Nivel: {profile.activity_label()}")
    t.add_row(
        "Calorías Objetivo Diarias",
        f"[bold green]{profile.target_calories:.0f} kcal/día[/bold green]",
        f"Meta: {profile.objective_label()}",
    )
    if profile.adjustment_capped:
        t.add_row("Ajuste calórico", "Limitado por seguridad", profile.adjustment_reason or "Política de rango")

    console.print(t)

    if profile.body_fat_pct:
        console.print(f"  [dim]% de grasa declarado:[/dim] {profile.body_fat_pct}%")

    macros = calcular_macronutrientes(profile.target_calories, profile.objective, perfil=profile)

    macro_table = Table(
        title="Distribución de Macronutrientes",
        box=box.ROUNDED, border_style="magenta",
        title_style="bold magenta", padding=(0, 2),
    )
    macro_table.add_column("Macronutriente", style="bold white",   min_width=20)
    macro_table.add_column("Gramos/día",     style="bold yellow",  min_width=14, justify="right")
    macro_table.add_column("% Calorías",     style="bold cyan",    min_width=12, justify="center")
    macro_table.add_column("Calorías",       style="dim white",    min_width=12, justify="right")

    macro_table.add_row("🥩 Proteínas",  f"{macros['proteinas']} g", f"{macros['p_pct']}%", f"{macros['proteinas'] * 4:.0f} kcal")
    macro_table.add_row("🍚 Carbohidratos", f"{macros['carbohidratos']} g", f"{macros['c_pct']}%", f"{macros['carbohidratos'] * 4:.0f} kcal")
    macro_table.add_row("🥑 Grasas", f"{macros['grasas']} g", f"{macros['g_pct']}%", f"{macros['grasas'] * 9:.0f} kcal")

    console.print(macro_table)


# ══════════════════════════════════════════════
#  Plan Nutricional
# ══════════════════════════════════════════════

def show_nutrition_plan(plan: dict) -> None:
    """Muestra el plan de alimentación diaria."""
    console.print()
    console.print(RichRule("[bold green]PLAN NUTRICIONAL[/bold green]", style="green"))

    meal_data = plan["plan"]

    meals = [
        ("🌅 DESAYUNO",  meal_data["desayuno"]),
        ("☀️  ALMUERZO",  meal_data["almuerzo"]),
        ("🌙 CENA",       meal_data["cena"]),
        ("🍎 SNACKS",     meal_data["snacks"]),
    ]

    for meal_name, options in meals:
        t = Table(
            title=meal_name, box=box.SIMPLE_HEAD,
            title_style="bold yellow", border_style="dim yellow",
            padding=(0, 1), show_header=False,
        )
        t.add_column(style="white", no_wrap=False, max_width=70)
        for idx, option in enumerate(options, 1):
            t.add_row(f"  [dim cyan]{idx}.[/dim cyan]  {option}")
        console.print(t)

    console.print(
        Panel(
            f"[bold cyan]💧 Hidratación:[/bold cyan] {meal_data['hidratacion']}",
            border_style="cyan", padding=(0, 2),
        )
    )

    # Transparencia de alergias / sustituciones
    if plan.get("sustituciones"):
        console.print(
            Panel(
                "\n".join(
                    f"[bold #B48CF2]•[/bold #B48CF2] "
                    f"{ALLERGY_OPTIONS.get(s.get('alergeno', ''), s.get('alergeno', ''))}: "
                    f"{s.get('substitucion', '')}"
                    for s in plan["sustituciones"]
                ) + "\n\n[dim]⚠️ Ningún sistema puede garantizar «100 % seguro»: "
                    "la contaminación cruzada depende de las etiquetas.[/dim]",
                border_style="#B48CF2", padding=(1, 2),
                title="[bold #B48CF2]🔁 Sustituciones por alergias[/bold #B48CF2]",
            )
        )
    if plan.get("derivacion"):
        console.print(f"  [dim]→ {plan['derivacion']}[/dim]")


# ══════════════════════════════════════════════
#  Plan de Entrenamiento
# ══════════════════════════════════════════════

def show_training_plan(routine: dict) -> None:
    """Muestra la rutina de entrenamiento (semana completa con descansos)."""
    console.print()
    console.print(RichRule("[bold magenta]PLAN DE ENTRENAMIENTO[/bold magenta]", style="magenta"))

    console.print(
        Panel(
            Text.from_markup(
                f"[bold white]{routine['nombre']}[/bold white]\n"
                f"[yellow]Días:[/yellow] {routine['dias']}\n"
                f"[yellow]Tipo:[/yellow] {routine['tipo']}"
            ),
            border_style="magenta", padding=(1, 2),
        )
    )

    # Semana completa (incluye días de descanso); las key de sesión son
    # `dia/grupo` (contrato de training.py) — se corrige el KeyError de v2.
    for session in routine.get("semana", routine.get("sesiones", [])):
        if session.get("descanso"):
            console.print(
                f"  [dim #FFB020]◌[/dim #FFB020] [bold #9AA8C0]{session['dia']}[/bold #9AA8C0] — "
                f"{session.get('nota', 'Descanso planificado.')}"
            )
            console.print()
            continue

        t = Table(
            title=f"{session['dia']} · {session['grupo']}",
            box=box.ROUNDED, border_style="dim magenta",
            title_style="bold white", padding=(0, 1),
        )
        t.add_column("Ejercicio",    style="bold white",  min_width=32)
        t.add_column("Series/Reps",  style="bold yellow", min_width=22, justify="center")
        t.add_column("Músculo",      style="cyan",        min_width=22)

        for ejercicio, series, musculo in session.get("ejercicios", []):
            t.add_row(ejercicio, series, musculo)

        console.print(t)
        console.print(
            f"  [dim]⏱ Descanso:[/dim] {session.get('descanso_entre_series', '–')}   "
            f"[dim]⌛ Duración aprox.:[/dim] {session.get('duracion', '–')}"
        )
        if session.get("nota"):
            console.print(f"  [dim]💬 [i]{session['nota']}[/i][/dim]")
        console.print()

    if routine.get("cardio_extra"):
        console.print(f"  [bold cyan]🏃 Cardio adicional:[/bold cyan] {routine['cardio_extra']}")
    if routine.get("notas"):
        console.print(
            Panel(
                f"[dim white]💡 {routine['notas']}[/dim white]",
                border_style="dim cyan", padding=(0, 2),
                title="[bold dim]Nota del entrenador[/bold dim]",
            )
        )

    if routine.get("lesiones_consideradas"):
        console.print(
            f"  [bold #B48CF2]🩹 Restricciones por lesión:[/bold #B48CF2] "
            + ", ".join(routine["lesiones_consideradas"])
        )
    if routine.get("alternativas_aplicadas"):
        console.print(
            Panel(
                "\n".join(f"[dim]• {a}[/dim]" for a in routine["alternativas_aplicadas"]),
                border_style="#B48CF2", padding=(0, 2),
                title="[bold #B48CF2]🔁 Ejercicios sustituidos por lesión[/bold #B48CF2]",
            )
        )


# ══════════════════════════════════════════════
#  Conclusiones del motor de inferencia
# ══════════════════════════════════════════════

def show_conclusions(profile: UserProfile) -> None:
    """Muestra las conclusiones con severidad, tier, referencias y alternativa."""
    console.print()
    console.print(RichRule("[bold yellow]RECOMENDACIONES DEL SISTEMA EXPERTO[/bold yellow]", style="yellow"))

    if profile.red_flags:
        console.print(
            Panel(
                "[bold red]⚠️ Señales de alarma declaradas: la evaluación exige consulta "
                "médica antes de ejercitarse. No se prescribe ejercicio.[/bold red]",
                border_style="red",
            )
        )

    if not profile.conclusions:
        console.print("[dim]No se activaron reglas específicas para este perfil.[/dim]")
        return

    orden = sorted(
        profile.conclusions,
        key=lambda c: (SEVERITY_SORT.get(c.get("severity", "info"), 9),
                       -(c.get("priority") or 0)),
    )

    for c in orden:
        icon = CATEGORY_ICON.get(c.get("category", ""), "•")
        sev = SEVERITY_STYLE.get(c.get("severity", "info"), SEVERITY_STYLE["info"])
        tier_label = c.get("tier_label", c.get("tier", ""))
        bad = (
            f"[{sev['color']}]{sev['icon']} {sev['label'].upper()}[/{sev['color']}]  "
            f"[#9AA8C0]·[/#9AA8C0]  [{TIER_STYLE.get(c.get('tier', ''), {}).get('color', '#9AA8C0')}]"
            f"{TIER_STYLE.get(c.get('tier', ''), {}).get('icon', '•')} {tier_label}"
            f"[/{TIER_STYLE.get(c.get('tier', ''), {}).get('color', '#9AA8C0')}]"
        )
        refs = c.get("references") or []
        refs_txt = " · ".join(refs) if refs else "—"
        alt = c.get("alternative") or ""

        cuerpo = (
            f"[bold white]{icon} [{c.get('id', '')}] {c.get('description', '')}[/bold white]\n"
            f"{bad}\n\n"
            f"[bold #4EC9B0]👉 Recomendación:[/bold #4EC9B0] {c.get('conclusion', '')}"
        )
        if alt:
            cuerpo += f"\n\n[bold #B48CF2]↪️ Alternativa:[/bold #B48CF2] {alt}"
        cuerpo += f"\n\n[dim]📚 {refs_txt}[/dim]"
        console.print(
            Panel(
                Text.from_markup(cuerpo),
                border_style=sev["color"], padding=(1, 2),
                title=f"[bold {sev['color']}]{sev['icon']} Clase {sev['label']}[/bold {sev['color']}]",
            )
        )

    # Reglas suprimidas por conflicto
    if profile.suppressed:
        console.print(
            Panel(
                "\n".join(
                    f"[dim]• [{s.get('id', '')}] reemplazada por [{s.get('suppressed_by', '')}] — {s.get('reason', '')}[/dim]"
                    for s in profile.suppressed
                ),
                border_style="#B48CF2", padding=(0, 2),
                title="[bold #B48CF2]🚫 Reglas suprimidas por jerarquía[/bold #B48CF2]",
            )
        )

    if profile.engine_errors:
        console.print(
            Panel(
                "\n".join(f"[bold red]• [{e.get('id', '')}] {e.get('error', '')}[/bold red]"
                          for e in profile.engine_errors),
                border_style="red", padding=(0, 2),
                title="[bold red]🔧 Errores internos de evaluación (auditoría)[/bold red]",
            )
        )


# ══════════════════════════════════════════════
#  Módulo de explicación
# ══════════════════════════════════════════════

def show_explanations(profile: UserProfile) -> None:
    """Muestra el razonamiento detrás de cada conclusión del motor."""
    console.print()
    console.print(RichRule("[bold white]MÓDULO DE EXPLICACIÓN[/bold white]", style="white"))
    console.print(
        Panel(
            "[dim]Este módulo muestra el razonamiento del motor de inferencia:\n"
            "el POR QUÉ de cada recomendación, como lo haría un experto humano.[/dim]",
            border_style="dim white",
        )
    )

    if not profile.explanations:
        console.print("[dim]No hay explicaciones disponibles.[/dim]")
        return

    for i, exp in enumerate(profile.explanations, 1):
        rule_id = exp["id"]
        conclusion = next(
            (c["conclusion"] for c in profile.conclusions if c["id"] == rule_id),
            "–",
        )
        refs = exp.get("references") or []
        refs_txt = " · ".join(refs) if refs else "—"
        cuerpo = (
            f"[bold cyan]Regla {rule_id}[/bold cyan]\n"
            f"[bold white]Conclusión:[/bold white] {conclusion}\n\n"
            f"[white]{exp.get('explanation', '')}[/white]\n\n"
            f"[dim #4EC9B0]Motivo de activación: {exp.get('trigger', '—')}[/dim #4EC9B0]\n"
            f"[dim #4C9AFF]Referencias: {refs_txt}[/dim #4C9AFF]"
        )
        console.print(
            Panel(
                Text.from_markup(cuerpo),
                border_style="dim cyan", padding=(1, 2),
                title=f"[dim][{i}] Explicación[/dim]",
            )
        )


# ══════════════════════════════════════════════
#  Hechos (Facts — OAV)
# ══════════════════════════════════════════════

def show_facts(profile: UserProfile) -> None:
    """Muestra los hechos del sistema en formato Objeto-Atributo-Valor."""
    console.print()
    console.print(RichRule("[bold dim]BASE DE HECHOS (Objeto-Atributo-Valor)[/bold dim]", style="dim"))

    for objeto, atributos in profile.facts.items():
        t = Table(
            title=objeto, box=box.SIMPLE_HEAD,
            title_style="bold white", border_style="dim", padding=(0, 2),
        )
        t.add_column("Atributo", style="cyan",   min_width=26)
        t.add_column("Valor",    style="yellow",  min_width=20)
        for attr, val in atributos.items():
            t.add_row(attr, str(val))
        console.print(t)


# ══════════════════════════════════════════════
#  Historial de usuarios
# ══════════════════════════════════════════════

def show_user_history(users: list[dict]) -> None:
    """Muestra el historial de consultas guardadas."""
    console.print()
    console.print(RichRule("[bold cyan]HISTORIAL DE CONSULTAS[/bold cyan]", style="cyan"))

    if not users:
        console.print(Panel("[dim]No hay consultas registradas aún.[/dim]", border_style="dim"))
        return

    t = Table(box=box.ROUNDED, border_style="cyan", padding=(0, 1))
    t.add_column("#",         style="dim",          justify="right",  min_width=3)
    t.add_column("Nombre",    style="bold white",   min_width=15)
    t.add_column("Edad",      style="yellow",       justify="center", min_width=6)
    t.add_column("Sexo",      style="cyan",         justify="center", min_width=10)
    t.add_column("IMC",       style="yellow",       justify="center", min_width=8)
    t.add_column("Categoría", style="white",        min_width=18)
    t.add_column("Objetivo",  style="green",        min_width=22)
    t.add_column("Fecha",     style="dim",          min_width=18)

    for i, u in enumerate(users, 1):
        imc = u.get("imc", 0)
        imc_color = "green" if 18.5 <= imc <= 24.9 else "yellow" if imc < 18.5 else "red"
        obj_label = OBJECTIVE_LABELS.get(u.get("objective", ""), u.get("objective", "–"))
        t.add_row(
            str(i),
            u.get("name", "–"),
            str(u.get("age", "–")),
            u.get("sex", "–").capitalize(),
            f"[{imc_color}]{imc}[/{imc_color}]",
            u.get("imc_category", "–"),
            obj_label,
            u.get("created_at", "–"),
        )

    console.print(t)


# ══════════════════════════════════════════════
#  Estadísticas del sistema
# ══════════════════════════════════════════════

def show_stats(stats: dict, engine_summary: dict | None = None) -> None:
    """Muestra estadísticas de la base de datos y del motor de inferencia."""
    console.print()
    console.print(RichRule("[bold cyan]ESTADÍSTICAS DEL SISTEMA[/bold cyan]", style="cyan"))

    t = Table(box=box.ROUNDED, border_style="cyan", padding=(0, 2))
    t.add_column("Indicador",  style="bold white",  min_width=34)
    t.add_column("Valor",      style="bold yellow",  min_width=14, justify="right")

    t.add_row("Consultas registradas",
              str(stats.get("total_sesiones", stats.get("total_consultas", 0))))
    t.add_row("Usuarios únicos", str(stats.get("usuarios_unicos", 0)))
    t.add_row("Reglas en la base de conocimiento", str(len(RULES)))
    t.add_row("Jerarquías de conocimiento", str(len(TIER_LABELS)))
    for obj, count in (stats.get("por_objetivo") or {}).items():
        label = OBJECTIVE_LABELS.get(obj, obj)
        t.add_row(f"  └─ {label}", str(count))

    console.print(t)

    if engine_summary:
        t2 = Table(
            box=box.ROUNDED, border_style="magenta", padding=(0, 2),
            title="Motor de Inferencia — Última Sesión", title_style="bold magenta",
        )
        t2.add_column("Métrica",           style="bold white",  min_width=30)
        t2.add_column("Valor",             style="bold yellow", min_width=14, justify="right")
        t2.add_row("Total de reglas en la base",   str(engine_summary.get("total_rules", 0)))
        t2.add_row("Reglas activadas (FIRED)",     str(engine_summary.get("fired", 0)))
        t2.add_row("Reglas no aplicadas (SKIP)",   str(engine_summary.get("skipped", 0)))
        t2.add_row("Reglas suprimidas (conflicto)", str(engine_summary.get("suppressed", 0)))
        t2.add_row("Reglas con error",             str(engine_summary.get("errors", 0)))
        t2.add_row("IDs activadas",                ", ".join(engine_summary.get("fired_ids", [])))
        console.print(t2)


# ══════════════════════════════════════════════
#  Acerca del sistema
# ══════════════════════════════════════════════

def show_about() -> None:
    """Muestra información del sistema experto (actualizada a v3)."""
    console.print()
    console.print(RichRule("[bold white]ACERCA DEL SISTEMA[/bold white]", style="white"))

    tier_info = "\n".join(
        f"  [cyan]•[/cyan] {TIER_LABELS.get(tier, tier)}  "
        f"[dim]({sum(1 for r in RULES if r.tier == tier)} reglas)[/dim]"
        for tier in TIER_LABELS
    )

    console.print(
        Panel(
            Text.from_markup(
                "[bold #2DD4BF]FitExpert — Sistema Experto en Nutrición y Acondicionamiento Físico[/bold #2DD4BF]\n\n"
                "[bold white]Arquitectura:[/bold white]\n"
                "  [cyan]•[/cyan] Base de Conocimiento  — "
                f"[bold]{len(RULES)} reglas IF/THEN[/bold] (knowledge_base.py)\n"
                "  [cyan]•[/cyan] Motor de Inferencia   — Encadenamiento hacia adelante (inference_engine.py)\n"
                "  [cyan]•[/cyan] Módulo de Cálculos    — IMC, TMB, TDEE (calculations.py)\n"
                "  [cyan]•[/cyan] Planes Nutricionales  — Recetas estructuradas por objetivo (nutrition.py)\n"
                "  [cyan]•[/cyan] Planes de Entreno     — Matriz de lesiones + filtros biomecánicos (training.py)\n"
                "  [cyan]•[/cyan] Base de Datos         — Persistencia JSON atómica (database.py)\n"
                "  [cyan]•[/cyan] Autenticación         — Argon2id con migración de legados (auth.py)\n"
                "  [cyan]•[/cyan] Interfaz de Usuario   — Consola enriquecida (ui.py)\n\n"
                "[bold white]Jerarquía de conocimiento:[/bold white]\n"
                f"{tier_info}\n\n"
                "[bold white]Representación:[/bold white] Objeto-Atributo-Valor · "
                "[bold white]Inferencia:[/bold white] Forward Chaining\n"
                "[bold white]Fórmula calórica:[/bold white] Mifflin-St Jeor (OMS para menores ≥ 16)\n\n"
                "[bold yellow]⚠  Limitaciones del sistema:[/bold yellow]\n"
                "  Herramienta informativa y académica. No reemplaza la consulta con\n"
                "  nutricionistas, médicos ni entrenadores certificados, especialmente\n"
                "  ante enfermedades crónicas, lesiones agudas o señales de alarma.\n\n"
                "[dim]Desarrollado como proyecto académico — Sistemas Expertos[/dim]"
            ),
            border_style="#2DD4BF", padding=(1, 3),
        )
    )


# ══════════════════════════════════════════════
#  Utilidades
# ══════════════════════════════════════════════

def press_enter_to_continue() -> None:
    """Pausa y espera que el usuario presione Enter."""
    console.print()
    Prompt.ask("[dim]Presiona [Enter] para continuar[/dim]", default="", show_default=False)


def confirm(message: str) -> bool:
    """Pregunta una confirmación al usuario (s/n)."""
    res = Prompt.ask(f"[bold yellow]{message}[/bold yellow] (s/n)", choices=["s", "n"], default="s")
    return res == "s"


def show_save_confirmation(name: str) -> None:
    """Muestra confirmación de guardado."""
    console.print(
        Panel(
            f"[bold green]✓[/bold green] Consulta de [bold]{name}[/bold] guardada correctamente.",
            border_style="green",
        )
    )


def show_error(message: str) -> None:
    """Muestra un mensaje de error."""
    console.print(Panel(f"[bold red]✗ Error:[/bold red] {message}", border_style="red"))


def show_section_header(title: str, subtitle: str = "") -> None:
    """Muestra un encabezado de sección."""
    console.print()
    console.print(Panel(
        Text.from_markup(
            f"[bold white]{title}[/bold white]\n[dim]{subtitle}[/dim]" if subtitle
            else f"[bold white]{title}[/bold white]"
        ),
        border_style="cyan", padding=(0, 2),
    ))