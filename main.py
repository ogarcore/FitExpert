"""
main.py
=======
Punto de entrada del Sistema Experto en Nutrición y Acondicionamiento Físico.

Orquesta el flujo principal de la aplicación:
  1. Banner de bienvenida
  2. Menú principal
  3. Evaluación del usuario (recopilación de datos)
  4. Ejecución del motor de inferencia
  5. Presentación de resultados:
     - Cálculos (IMC, TMB, TDEE)
     - Plan nutricional
     - Plan de entrenamiento
     - Conclusiones del SE
     - Módulo de explicación
  6. Persistencia en base de datos
  7. Historial y estadísticas

Dependencias: rich  →  pip install rich
"""

import sys

# Verificar dependencia `rich` antes de iniciar
try:
    from rich.console import Console
except ImportError:
    print("\n[ERROR] La librería 'rich' no está instalada.")
    print("Ejecuta:  pip install rich\n")
    sys.exit(1)

from user_profile import UserProfile
from inference_engine import InferenceEngine
from nutrition import generate_nutrition_plan
from training import generate_training_plan
from database import save_profile, list_users, db_stats
import ui


# ──────────────────────────────────────────────
#  Flujo: Nueva Consulta
# ──────────────────────────────────────────────

def run_consultation() -> None:
    """
    Ejecuta el flujo completo de una consulta:
    recopilación de datos → inferencia → presentación → persistencia.
    """
    # 1. Recopilar datos del usuario
    profile = ui.collect_user_data()

    # 2. Ejecutar el motor de inferencia (calcula métricas + aplica reglas)
    engine = InferenceEngine()
    engine.run(profile)

    # ── Navegación de resultados ──────────────────────────────────────────

    ui.console.clear()
    ui.show_banner()
    ui.console.print(
        f"\n  [bold green]✓ Evaluación completada para: [bold white]{profile.name}[/bold white][/bold green]\n"
    )

    sections = [
        ("1", "📊 Métricas físicas (IMC, TMB, TDEE, Calorías)"),
        ("2", "🥗 Plan nutricional"),
        ("3", "🏋️  Rutina de entrenamiento"),
        ("4", "💡 Recomendaciones del Sistema Experto"),
        ("5", "🔍 Módulo de explicación (razonamiento)"),
        ("6", "🗂  Base de hechos (Objeto-Atributo-Valor)"),
        ("7", "📈 Estadísticas del motor de inferencia"),
        ("0", "Guardar y volver al menú principal"),
    ]

    while True:
        ui.console.print()
        from rich.table import Table
        from rich import box
        nav = Table(box=box.ROUNDED, show_header=False, border_style="cyan", padding=(0, 2))
        nav.add_column(style="bold cyan", no_wrap=True)
        nav.add_column(style="white")
        for key, label in sections:
            nav.add_row(f"[{key}]", label)
        ui.console.print(nav)
        ui.console.print()

        from rich.prompt import Prompt
        choice = Prompt.ask(
            "[bold cyan]Ver sección[/bold cyan]",
            choices=[s[0] for s in sections],
            default="1",
        )

        if choice == "1":
            ui.show_calculations(profile)
        elif choice == "2":
            plan = generate_nutrition_plan(profile)
            ui.show_nutrition_plan(plan)
        elif choice == "3":
            routine = generate_training_plan(profile)
            ui.show_training_plan(routine)
        elif choice == "4":
            ui.show_conclusions(profile)
        elif choice == "5":
            ui.show_explanations(profile)
        elif choice == "6":
            ui.show_facts(profile)
        elif choice == "7":
            ui.show_stats(db_stats(), engine.summary())
        elif choice == "0":
            break

    # 3. Guardar en base de datos
    if ui.confirm("¿Deseas guardar esta consulta en el historial?"):
        try:
            save_profile(profile)
            ui.show_save_confirmation(profile.name)
        except Exception as e:
            ui.show_error(f"No se pudo guardar: {e}")


# ──────────────────────────────────────────────
#  Flujo: Historial
# ──────────────────────────────────────────────

def run_history() -> None:
    """Muestra el historial de consultas guardadas."""
    users = list_users()
    ui.show_user_history(users)
    ui.press_enter_to_continue()


# ──────────────────────────────────────────────
#  Flujo: Estadísticas
# ──────────────────────────────────────────────

def run_stats() -> None:
    """Muestra estadísticas globales del sistema."""
    stats = db_stats()
    ui.show_stats(stats)
    ui.press_enter_to_continue()


# ──────────────────────────────────────────────
#  Bucle principal
# ──────────────────────────────────────────────

def main() -> None:
    """Punto de entrada principal. Gestiona el menú y el flujo de la aplicación."""
    while True:
        ui.console.clear()
        ui.show_banner()

        option = ui.show_main_menu()

        if option == "1":
            run_consultation()

        elif option == "2":
            ui.console.clear()
            run_history()

        elif option == "3":
            ui.console.clear()
            run_stats()

        elif option == "4":
            ui.console.clear()
            ui.show_about()
            ui.press_enter_to_continue()

        elif option == "0":
            ui.console.print(
                "\n  [bold cyan]¡Hasta pronto! Recuerda mantener hábitos saludables. 💪[/bold cyan]\n"
            )
            sys.exit(0)


# ──────────────────────────────────────────────
#  Ejecución directa
# ──────────────────────────────────────────────

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        ui.console.print("\n\n  [dim]Sesión interrumpida por el usuario.[/dim]\n")
        sys.exit(0)
