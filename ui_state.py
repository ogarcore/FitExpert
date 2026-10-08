"""
ui_state.py
===========
Estado de sesión para la pestaña "Entrenamiento" de la web (gui.py).

Separa la lógica testeable (sin navegador) del acordeón de días:
  - Constante DIAS_ABIERTOS_POR_DEFECTO: qué días arrancan abiertos.
  - dias_abiertos_iniciales(): qué slugs deben quedar abiertos al
    iniciar o al generar un plan nuevo (con fallback robusto).
"""

from __future__ import annotations

import unicodedata

from exercise_info import slugify

# ── Configuración editable ─────────────────────────────────────────────
# Días que aparecen ABIERTOS por defecto. Comparación tolerante a
# mayúsculas/tildes. Si ninguno coincide con el plan, se abre el primer
# día del plan como fallback (nunca queda todo cerrado de inicio).
DIAS_ABIERTOS_POR_DEFECTO = ["Lunes"]


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s or ""))
    return s.encode("ascii", "ignore").decode("ascii").lower().strip()


def nombre_de_dia(d) -> str:
    """Acepta dict ({'dia': ...}) o string y devuelve el nombre."""
    if isinstance(d, dict):
        return str(d.get("dia", "") or "")
    return str(d or "")


def plan_key_de(perfil, rutina) -> str:
    """Huella del plan activo: cambia si cambia el plan (reset de UI)."""
    semana = (rutina or {}).get("semana", []) or []
    dias = ",".join(nombre_de_dia(d) for d in semana)
    return (f"{getattr(perfil, 'created_at', '')}|{(rutina or {}).get('nombre', '')}|{dias}")


def conteo_ejercicios(day) -> int:
    """Número de ejercicios de un día (robusto ante datos ausentes)."""
    if isinstance(day, dict):
        exs = day.get("ejercicios")
        if isinstance(exs, (list, tuple)):
            return len(exs)
    return 0


def texto_secundario_dia(day) -> str:
    """Línea secundaria del encabezado del día."""
    if not isinstance(day, dict):
        return "Día de recuperación"
    n = conteo_ejercicios(day)
    activo = "activo" in _norm(day.get("grupo", ""))
    if n > 0:
        base = f"{n} ejercicio{'s' if n != 1 else ''}"
        return f"{base} · Recuperación" if activo else base
    return "Día de recuperación"


def es_descanso(day) -> bool:
    """Día de recuperación/descanso SIN ejercicios.

    Un día con ejercicios (aunque su grupo diga "descanso activo" o su
    flag descanso sea True) NO se considera descanso a efectos de UI:
    muestra su lista de ejercicios y el secundario "N ejercicios ·
    Recuperación" cuando aplica.
    """
    if not isinstance(day, dict):
        return False
    if conteo_ejercicios(day) > 0:
        return False
    if day.get("descanso"):
        return True
    if "descanso" in _norm(day.get("grupo", "")):
        return True
    return not day.get("ejercicios")


def dias_abiertos_iniciales(semana, default=None) -> set:
    """
    Devuelve el conjunto de slugs de día que deben arrancar abiertos.

    - Abre los días listados en `default` (tolerante a mayús/tildes).
    - Si ninguno de esos días existe en el plan, abre SOLO el primer
      día del plan (fallback robusto, nunca falla ni deja todo cerrado
      salvo que el plan esté vacío).
    """
    if default is None:
        default = DIAS_ABIERTOS_POR_DEFECTO
    nombres = [nombre_de_dia(d) for d in (semana or [])]
    objetivo = {_norm(d) for d in (default or [])}
    abiertos = {slugify(n) for n in nombres if _norm(n) in objetivo}
    if not abiertos and nombres:
        abiertos = {slugify(nombres[0])}
    return abiertos
