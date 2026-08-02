"""
ui.py
=====
Módulo de Interfaz de Usuario del Sistema Experto.

Responsabilidades:
  - Presentar menús y formularios en la consola usando `rich`.
  - Recopilar datos del usuario con validación.
  - Visualizar resultados, planes y explicaciones en tablas y paneles.
  - Mostrar el módulo de explicación del motor de inferencia.

Depende de: rich (pip install rich)
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
from rich.style import Style

from user_profile import (
    UserProfile, OBJECTIVES, OBJECTIVE_LABELS,
    ACTIVITY_LEVELS, ACTIVITY_LABELS,
    EXPERIENCE_LEVELS, TRAINING_PLACES, SEX_OPTIONS,
)
from calculations import calcular_macronutrientes


# ──────────────────────────────────────────────
#  Consola global
# ──────────────────────────────────────────────

console = Console()

# Paleta de colores del sistema
COLOR_PRIMARY   = "bold cyan"
COLOR_SECONDARY = "bold yellow"
COLOR_SUCCESS   = "bold green"
COLOR_WARNING   = "bold red"
COLOR_MUTED     = "dim white"
COLOR_HEADER    = "bold white on dark_cyan"
COLOR_ACCENT    = "bold magenta"


# ══════════════════════════════════════════════
#  PANTALLA: Banner principal
# ══════════════════════════════════════════════

def show_banner() -> None:
    """Muestra el banner de bienvenida del sistema."""
    console.clear()
    banner = Text(justify="center")
    banner.append("\n")
    banner.append("  ██╗     ██╗███████╗███████╗  \n", style="bold cyan")
    banner.append("  ██║     ██║██╔════╝██╔════╝  \n", style="bold cyan")
    banner.append("  ██║     ██║█████╗  █████╗    \n", style="bold cyan")
    banner.append("  ██║     ██║██╔══╝  ██╔══╝    \n", style="bold cyan")
    banner.append("  ███████╗██║██║     ███████╗  \n", style="bold cyan")
    banner.append("  ╚══════╝╚═╝╚═╝     ╚══════╝  \n", style="bold cyan")

    console.print(banner)
    console.print(
        Panel(
            Text.from_markup(
                "[bold white]Sistema Experto en Nutrición y Acondicionamiento Físico[/bold white]\n"
                "[dim]Asesoramiento personalizado basado en reglas de conocimiento especializado[/dim]\n"
                "[dim cyan]Universidad · Inteligencia Artificial · Sistemas Expertos[/dim cyan]"
            ),
            border_style="cyan",
            padding=(1, 4),
        )
    )


# ══════════════════════════════════════════════
#  PANTALLA: Menú principal
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
#  FORMULARIO: Datos del usuario
# ══════════════════════════════════════════════

def _show_options_table(title: str, options: dict, labels: dict) -> None:
    """Muestra una tabla de opciones numeradas para un campo."""
    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    t.add_column(style="bold cyan", no_wrap=True)
    t.add_column(style="white")
    for key, val in options.items():
        t.add_row(f"  [{key}]", labels.get(val, val))
    console.print(t)


def collect_user_data() -> UserProfile:
    """
    Guía al usuario a través del formulario de evaluación inicial.
    Retorna un UserProfile con todos los datos recopilados.
    """
    profile = UserProfile()

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

    # ── Datos personales ──────────────────────────────────────────────────

    console.print("[bold cyan]── Datos Personales ──────────────────────────────────[/bold cyan]")
    profile.name = Prompt.ask("[white]Nombre[/white]").strip() or "Usuario"

    # Edad
    while True:
        age = IntPrompt.ask("[white]Edad (años)[/white]")
        if 10 <= age <= 100:
            profile.age = age
            break
        console.print("[bold red]  ✗ Ingresa una edad válida (10–100).[/bold red]")

    # Sexo
    console.print("[white]Sexo:[/white]")
    _show_options_table("Sexo", SEX_OPTIONS, {v: v.capitalize() for v in SEX_OPTIONS.values()})
    sex_key = Prompt.ask("  Selecciona", choices=list(SEX_OPTIONS.keys()))
    profile.sex = SEX_OPTIONS[sex_key]

    # Peso
    while True:
        weight = FloatPrompt.ask("[white]Peso (kg)[/white]")
        if 30 <= weight <= 300:
            profile.weight = weight
            break
        console.print("[bold red]  ✗ Ingresa un peso válido (30–300 kg).[/bold red]")

    # Altura
    while True:
        height = FloatPrompt.ask("[white]Altura (cm)[/white]")
        if 100 <= height <= 250:
            profile.height = height
            break
        console.print("[bold red]  ✗ Ingresa una altura válida (100–250 cm).[/bold red]")

    # ── Objetivos y entrenamiento ─────────────────────────────────────────

    console.print()
    console.print("[bold cyan]── Objetivos y Entrenamiento ─────────────────────────[/bold cyan]")

    # Objetivo corporal
    console.print("[white]Objetivo corporal:[/white]")
    _show_options_table("Objetivo", OBJECTIVES, OBJECTIVE_LABELS)
    obj_key = Prompt.ask("  Selecciona", choices=list(OBJECTIVES.keys()))
    profile.objective = OBJECTIVES[obj_key]

    # Nivel de actividad
    console.print("[white]Nivel de actividad física actual:[/white]")
    _show_options_table("Actividad", ACTIVITY_LEVELS, ACTIVITY_LABELS)
    act_key = Prompt.ask("  Selecciona", choices=list(ACTIVITY_LEVELS.keys()))
    profile.activity_level = ACTIVITY_LEVELS[act_key]

    # Experiencia
    console.print("[white]Nivel de experiencia en entrenamiento:[/white]")
    exp_labels = {v: v.capitalize() for v in EXPERIENCE_LEVELS.values()}
    exp_descriptions = {
        "principiante": "Principiante (menos de 6 meses)",
        "intermedio":   "Intermedio (6 meses – 2 años)",
        "avanzado":     "Avanzado (más de 2 años)",
    }
    _show_options_table("Experiencia", EXPERIENCE_LEVELS, exp_descriptions)
    exp_key = Prompt.ask("  Selecciona", choices=list(EXPERIENCE_LEVELS.keys()))
    profile.experience = EXPERIENCE_LEVELS[exp_key]

    # Lugar de entrenamiento
    console.print("[white]Preferencia de lugar de entrenamiento:[/white]")
    place_labels = {"casa": "Entrenamiento en Casa", "gimnasio": "Gimnasio"}
    _show_options_table("Lugar", TRAINING_PLACES, place_labels)
    place_key = Prompt.ask("  Selecciona", choices=list(TRAINING_PLACES.keys()))
    profile.training_place = TRAINING_PLACES[place_key]

    console.print()
    console.print("[bold green]  ✓ Datos recopilados correctamente.[/bold green]")
    return profile


# ══════════════════════════════════════════════
#  PANTALLA: Resultados de cálculos
# ══════════════════════════════════════════════

def show_calculations(profile: UserProfile) -> None:
    """Muestra los resultados de IMC, TMB, TDEE y calorías objetivo."""
    console.print()
    console.print(RichRule("[bold cyan]RESULTADOS DE EVALUACIÓN FÍSICA[/bold cyan]", style="cyan"))

    # ── Tabla de métricas ──────────────────────────────────────────────────
    t = Table(
        title=f"Métricas de {profile.name}",
        box=box.ROUNDED,
        border_style="cyan",
        title_style="bold cyan",
        padding=(0, 2),
    )
    t.add_column("Indicador",   style="bold white",   min_width=28)
    t.add_column("Valor",       style="bold yellow",  min_width=16, justify="right")
    t.add_column("Referencia",  style="dim white",    min_width=24)

    # IMC con color según categoría
    imc_color = "green" if 18.5 <= profile.imc <= 24.9 else "yellow" if profile.imc < 18.5 else "red"
    t.add_row(
        "Índice de Masa Corporal (IMC)",
        f"[{imc_color}]{profile.imc:.2f} kg/m²[/{imc_color}]",
        f"[{imc_color}]{profile.imc_category}[/{imc_color}]",
    )
    t.add_row(
        "Tasa Metabólica Basal (TMB)",
        f"{profile.tmb:.0f} kcal/día",
        "Calorías en reposo total",
    )
    t.add_row(
        "Gasto Energético Diario (TDEE)",
        f"{profile.tdee:.0f} kcal/día",
        f"Nivel: {profile.activity_level}",
    )
    t.add_row(
        "Calorías Objetivo Diarias",
        f"[bold green]{profile.target_calories:.0f} kcal/día[/bold green]",
        f"Meta: {profile.objective_label()}",
    )

    console.print(t)

    # ── Macronutrientes ────────────────────────────────────────────────────
    macros = calcular_macronutrientes(profile.target_calories, profile.objective)

    macro_table = Table(
        title="Distribución de Macronutrientes",
        box=box.ROUNDED,
        border_style="magenta",
        title_style="bold magenta",
        padding=(0, 2),
    )
    macro_table.add_column("Macronutriente", style="bold white",   min_width=20)
    macro_table.add_column("Gramos/día",     style="bold yellow",  min_width=14, justify="right")
    macro_table.add_column("% Calorías",     style="bold cyan",    min_width=12, justify="center")
    macro_table.add_column("Calorías",       style="dim white",    min_width=12, justify="right")

    macro_table.add_row(
        "🥩 Proteínas",
        f"{macros['proteinas']} g",
        f"{macros['p_pct']}%",
        f"{macros['proteinas'] * 4:.0f} kcal",
    )
    macro_table.add_row(
        "🍚 Carbohidratos",
        f"{macros['carbohidratos']} g",
        f"{macros['c_pct']}%",
        f"{macros['carbohidratos'] * 4:.0f} kcal",
    )
    macro_table.add_row(
        "🥑 Grasas",
        f"{macros['grasas']} g",
        f"{macros['g_pct']}%",
        f"{macros['grasas'] * 9:.0f} kcal",
    )

    console.print(macro_table)


# ══════════════════════════════════════════════
#  PANTALLA: Plan Nutricional
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
            title=meal_name,
            box=box.SIMPLE_HEAD,
            title_style="bold yellow",
            border_style="dim yellow",
            padding=(0, 1),
            show_header=False,
        )
        t.add_column(style="white", no_wrap=False, max_width=70)
        for idx, option in enumerate(options, 1):
            t.add_row(f"  [dim cyan]{idx}.[/dim cyan]  {option}")
        console.print(t)

    # Hidratación
    console.print(
        Panel(
            f"[bold cyan]💧 Hidratación:[/bold cyan] {meal_data['hidratacion']}",
            border_style="cyan",
            padding=(0, 2),
        )
    )


# ══════════════════════════════════════════════
#  PANTALLA: Plan de Entrenamiento
# ══════════════════════════════════════════════

def show_training_plan(routine: dict) -> None:
    """Muestra la rutina de entrenamiento del usuario."""
    console.print()
    console.print(RichRule("[bold magenta]PLAN DE ENTRENAMIENTO[/bold magenta]", style="magenta"))

    # Encabezado de la rutina
    console.print(
        Panel(
            Text.from_markup(
                f"[bold white]{routine['nombre']}[/bold white]\n"
                f"[yellow]Días:[/yellow] {routine['dias']}\n"
                f"[yellow]Tipo:[/yellow] {routine['tipo']}"
            ),
            border_style="magenta",
            padding=(1, 2),
        )
    )

    # Sesiones
    for session in routine.get("sesiones", []):
        t = Table(
            title=session["nombre"],
            box=box.ROUNDED,
            border_style="dim magenta",
            title_style="bold white",
            padding=(0, 1),
        )
        t.add_column("Ejercicio",    style="bold white",  min_width=32)
        t.add_column("Series/Reps",  style="bold yellow", min_width=22, justify="center")
        t.add_column("Músculo",      style="cyan",        min_width=22)

        for ejercicio, series, musculo in session.get("ejercicios", []):
            t.add_row(ejercicio, series, musculo)

        console.print(t)
        console.print(
            f"  [dim]⏱ Descanso:[/dim] {session.get('descanso', '–')}   "
            f"[dim]⌛ Duración aprox.:[/dim] {session.get('duracion', '–')}"
        )
        console.print()

    # Cardio extra y notas
    if routine.get("cardio_extra"):
        console.print(
            f"  [bold cyan]🏃 Cardio adicional:[/bold cyan] {routine['cardio_extra']}"
        )
    if routine.get("notas"):
        console.print(
            Panel(
                f"[dim white]💡 {routine['notas']}[/dim white]",
                border_style="dim cyan",
                padding=(0, 2),
                title="[bold dim]Nota del entrenador[/bold dim]",
            )
        )


# ══════════════════════════════════════════════
#  PANTALLA: Conclusiones del Motor de Inferencia
# ══════════════════════════════════════════════

def show_conclusions(profile: UserProfile) -> None:
    """Muestra las conclusiones generadas por el motor de inferencia."""
    console.print()
    console.print(RichRule("[bold yellow]RECOMENDACIONES DEL SISTEMA EXPERTO[/bold yellow]", style="yellow"))

    CATEGORY_ICONS = {
        "nutricion":     ("🥗", "green"),
        "entrenamiento": ("🏋️", "magenta"),
        "seguimiento":   ("📊", "cyan"),
        "alerta":        ("⚠️",  "red"),
    }

    # Agrupar por categoría
    by_cat: dict[str, list] = {}
    for c in profile.conclusions:
        by_cat.setdefault(c["category"], []).append(c)

    for cat, conclusions in by_cat.items():
        icon, color = CATEGORY_ICONS.get(cat, ("•", "white"))
        console.print(f"\n  [{color}]{icon}  {cat.upper()}[/{color}]")

        t = Table(
            box=box.SIMPLE,
            show_header=True,
            padding=(0, 1),
            border_style=f"dim {color}",
        )
        t.add_column("ID",              style=f"dim {color}",   no_wrap=True, min_width=10)
        t.add_column("Recomendación",   style="white",          no_wrap=False)

        for c in conclusions:
            t.add_row(c["id"], c["conclusion"])

        console.print(t)


# ══════════════════════════════════════════════
#  PANTALLA: Módulo de Explicación
# ══════════════════════════════════════════════

def show_explanations(profile: UserProfile) -> None:
    """
    Módulo de explicación: muestra el razonamiento detrás de cada conclusión.
    Característica clave de los Sistemas Expertos.
    """
    console.print()
    console.print(RichRule("[bold white]MÓDULO DE EXPLICACIÓN[/bold white]", style="white"))
    console.print(
        Panel(
            "[dim]Este módulo muestra el razonamiento del motor de inferencia.\n"
            "Explica POR QUÉ se generó cada recomendación, como lo haría un experto humano.[/dim]",
            border_style="dim white",
        )
    )

    if not profile.explanations:
        console.print("[dim]No hay explicaciones disponibles.[/dim]")
        return

    for i, exp in enumerate(profile.explanations, 1):
        rule_id = exp["id"]
        # Buscar conclusión correspondiente
        conclusion = next(
            (c["conclusion"] for c in profile.conclusions if c["id"] == rule_id),
            "–"
        )
        console.print(
            Panel(
                Text.from_markup(
                    f"[bold cyan]Regla {rule_id}[/bold cyan]\n"
                    f"[bold white]Conclusión:[/bold white] {conclusion}\n\n"
                    f"[dim white]{exp['explanation']}[/dim white]"
                ),
                border_style="dim cyan",
                padding=(1, 2),
            )
        )


# ══════════════════════════════════════════════
#  PANTALLA: Hechos (Facts — OAV)
# ══════════════════════════════════════════════

def show_facts(profile: UserProfile) -> None:
    """Muestra los hechos del sistema en formato Objeto-Atributo-Valor."""
    console.print()
    console.print(RichRule("[bold dim]BASE DE HECHOS (Objeto-Atributo-Valor)[/bold dim]", style="dim"))

    for objeto, atributos in profile.facts.items():
        t = Table(
            title=objeto,
            box=box.SIMPLE_HEAD,
            title_style="bold white",
            border_style="dim",
            padding=(0, 2),
        )
        t.add_column("Atributo", style="cyan",   min_width=26)
        t.add_column("Valor",    style="yellow",  min_width=20)

        for attr, val in atributos.items():
            t.add_row(attr, str(val))

        console.print(t)


# ══════════════════════════════════════════════
#  PANTALLA: Historial de usuarios
# ══════════════════════════════════════════════

def show_user_history(users: list[dict]) -> None:
    """Muestra el historial de usuarios guardados en la base de datos."""
    console.print()
    console.print(RichRule("[bold cyan]HISTORIAL DE CONSULTAS[/bold cyan]", style="cyan"))

    if not users:
        console.print(
            Panel("[dim]No hay usuarios registrados aún.[/dim]", border_style="dim")
        )
        return

    t = Table(
        box=box.ROUNDED,
        border_style="cyan",
        padding=(0, 1),
    )
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
#  PANTALLA: Estadísticas del sistema
# ══════════════════════════════════════════════

def show_stats(stats: dict, engine_summary: dict | None = None) -> None:
    """Muestra estadísticas del sistema y de la base de datos."""
    console.print()
    console.print(RichRule("[bold cyan]ESTADÍSTICAS DEL SISTEMA[/bold cyan]", style="cyan"))

    # Stats de usuarios
    t = Table(box=box.ROUNDED, border_style="cyan", padding=(0, 2))
    t.add_column("Indicador",  style="bold white",  min_width=30)
    t.add_column("Valor",      style="bold yellow",  min_width=14, justify="right")

    t.add_row("Total de consultas registradas", str(stats.get("total_usuarios", 0)))
    for obj, count in stats.get("por_objetivo", {}).items():
        label = OBJECTIVE_LABELS.get(obj, obj)
        t.add_row(f"  └─ {label}", str(count))

    console.print(t)

    # Stats del motor de inferencia
    if engine_summary:
        t2 = Table(box=box.ROUNDED, border_style="magenta", padding=(0, 2),
                   title="Motor de Inferencia — Última Sesión", title_style="bold magenta")
        t2.add_column("Métrica",           style="bold white",  min_width=30)
        t2.add_column("Valor",             style="bold yellow", min_width=14, justify="right")
        t2.add_row("Total de reglas en la base",   str(engine_summary.get("total_rules", 0)))
        t2.add_row("Reglas activadas (FIRED)",     str(engine_summary.get("fired", 0)))
        t2.add_row("Reglas no aplicadas",          str(engine_summary.get("skipped", 0)))
        t2.add_row("IDs de reglas activadas",      ", ".join(engine_summary.get("fired_ids", [])))
        console.print(t2)


# ══════════════════════════════════════════════
#  PANTALLA: Acerca del sistema
# ══════════════════════════════════════════════

def show_about() -> None:
    """Muestra información sobre el sistema experto."""
    console.print()
    console.print(RichRule("[bold white]ACERCA DEL SISTEMA[/bold white]", style="white"))
    console.print(
        Panel(
            Text.from_markup(
                "[bold cyan]Sistema Experto en Nutrición y Acondicionamiento Físico[/bold cyan]\n\n"
                "[bold white]Arquitectura:[/bold white]\n"
                "  [cyan]•[/cyan] Base de Conocimiento  — Reglas de producción IF-THEN (knowledge_base.py)\n"
                "  [cyan]•[/cyan] Motor de Inferencia   — Encadenamiento hacia adelante (inference_engine.py)\n"
                "  [cyan]•[/cyan] Módulo de Cálculos    — IMC, TMB, TDEE (calculations.py)\n"
                "  [cyan]•[/cyan] Planes Nutricionales  — Catálogo por objetivo (nutrition.py)\n"
                "  [cyan]•[/cyan] Planes de Entreno     — Rutinas por nivel y lugar (training.py)\n"
                "  [cyan]•[/cyan] Base de Datos         — Persistencia JSON (database.py)\n"
                "  [cyan]•[/cyan] Interfaz de Usuario   — Consola enriquecida (ui.py)\n\n"
                "[bold white]Representación del conocimiento:[/bold white] Objeto-Atributo-Valor\n"
                "[bold white]Estrategia de inferencia:[/bold white]      Forward Chaining\n"
                "[bold white]Fórmula nutricional:[/bold white]           Mifflin-St Jeor (Harris-Benedict revisada)\n\n"
                "[bold yellow]⚠  Limitaciones del sistema:[/bold yellow]\n"
                "  Este sistema es una herramienta de orientación general.\n"
                "  No reemplaza la consulta con nutricionistas, médicos ni\n"
                "  entrenadores certificados, especialmente en casos de\n"
                "  enfermedades crónicas o condiciones médicas especiales.\n\n"
                "[dim]Desarrollado como proyecto académico — Sistemas Expertos[/dim]"
            ),
            border_style="cyan",
            padding=(1, 3),
        )
    )


# ══════════════════════════════════════════════
#  UTILIDADES
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
    console.print(
        Panel(f"[bold red]✗ Error:[/bold red] {message}", border_style="red")
    )


def show_section_header(title: str, subtitle: str = "") -> None:
    """Muestra un encabezado de sección."""
    console.print()
    console.print(Panel(
        Text.from_markup(f"[bold white]{title}[/bold white]\n[dim]{subtitle}[/dim]" if subtitle else f"[bold white]{title}[/bold white]"),
        border_style="cyan",
        padding=(0, 2),
    ))
