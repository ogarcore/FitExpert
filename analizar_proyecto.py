"""
analizar_proyecto.py
=====================
Corre todas las herramientas de análisis estático usadas para evaluar
el proyecto FitExpert contra ISO/IEC 25010, y guarda todo en un solo
archivo de texto: reporte_iso25010.txt

Requisitos previos (instalar una sola vez):
    pip install radon flake8 bandit

Uso:
    python analizar_proyecto.py
    (ejecútalo desde dentro de la carpeta del proyecto, ej: FitExpert/)
"""

import subprocess
import sys
from datetime import datetime

OUTPUT_FILE = "reporte_iso25010.txt"

# Carpetas que NO son código propio del proyecto (entornos virtuales, control de versiones, cache)
EXCLUDE_RADON = "venv/*,.venv/*,env/*,__pycache__/*"
EXCLUDE_FLAKE8 = "venv,.venv,env,__pycache__,.git"
EXCLUDE_BANDIT = "./.git,./venv,./.venv,./env,./__pycache__"

COMANDOS = [
    ("RADON - Complejidad Ciclomática (Analizabilidad)",
     [sys.executable, "-m", "radon", "cc", ".", "-a", "-s", "-e", EXCLUDE_RADON]),

    ("RADON - Índice de Mantenibilidad (Cap. de modificación)",
     [sys.executable, "-m", "radon", "mi", ".", "-s", "-e", EXCLUDE_RADON]),

    ("RADON - Métricas Raw: LOC, comentarios, blancos",
     [sys.executable, "-m", "radon", "raw", ".", "-s", "-e", EXCLUDE_RADON]),

    ("RADON - Métricas de Halstead (esfuerzo, volumen, bugs)",
     [sys.executable, "-m", "radon", "hal", ".", "-e", EXCLUDE_RADON]),

    ("FLAKE8 - Estilo, errores potenciales, código muerto",
     [sys.executable, "-m", "flake8", "--max-line-length=120",
      "--statistics", "--count", f"--exclude={EXCLUDE_FLAKE8}", "."]),

    ("BANDIT - Seguridad (SAST)",
     [sys.executable, "-m", "bandit", "-r", ".", "-x", EXCLUDE_BANDIT]),
]


def run_command(nombre, comando):
    print(f"Ejecutando: {nombre} ...")
    resultado = subprocess.run(
        comando, capture_output=True, text=True, encoding="utf-8", errors="ignore"
    )
    salida = resultado.stdout + resultado.stderr
    return salida


def main():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write("REPORTE DE ANÁLISIS - ISO/IEC 25010\n")
        out.write(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        out.write("=" * 70 + "\n\n")

        for nombre, comando in COMANDOS:
            salida = run_command(nombre, comando)
            out.write(f"\n{'=' * 70}\n")
            out.write(f"{nombre}\n")
            out.write(f"{'=' * 70}\n")
            out.write(salida + "\n")

    print(f"\nListo. Reporte guardado en: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()