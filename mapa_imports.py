"""
mapa_imports.py
================
Analiza los imports internos entre los archivos .py/.pyw de un proyecto
para detectar el grado de acoplamiento entre módulos (ISO 25010 - Modularidad).

Uso:
    python mapa_imports.py
    (ejecútalo desde dentro de la carpeta del proyecto, ej: FitExpert/)
"""

import os
import re

# Extensiones de archivo a analizar
EXTENSIONS = (".py", ".pyw")

# Carpetas a ignorar
IGNORE_DIRS = {".git", "__pycache__", "venv", ".venv", "env"}


def get_project_modules(root="."):
    """Devuelve el conjunto de nombres de módulo (sin extensión) del proyecto."""
    modules = set()
    for fname in os.listdir(root):
        if fname.endswith(EXTENSIONS):
            modules.add(os.path.splitext(fname)[0])
    return modules


def find_internal_imports(filepath, project_modules):
    """Busca líneas 'import X' o 'from X import ...' donde X sea un módulo propio."""
    found = []
    pattern = re.compile(r"^\s*(?:from|import)\s+([a-zA-Z_][\w]*)")

    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            match = pattern.match(line)
            if match:
                module_name = match.group(1)
                if module_name in project_modules:
                    found.append(line.strip())
    return found


def main(root="."):
    project_modules = get_project_modules(root)
    print(f"Módulos detectados en el proyecto: {sorted(project_modules)}\n")

    for fname in sorted(os.listdir(root)):
        if not fname.endswith(EXTENSIONS):
            continue
        filepath = os.path.join(root, fname)
        imports = find_internal_imports(filepath, project_modules)

        print(f"--- {fname} ---")
        if imports:
            for imp in imports:
                print(f"  {imp}")
        else:
            print("  (sin dependencias internas)")
        print()


if __name__ == "__main__":
    main()
