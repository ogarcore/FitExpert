"""
database.py
===========
Capa de persistencia del Sistema Experto.

Almacena el historial de consultas por usuario, permitiendo:
  - Múltiples consultas por usuario (historial individual)
  - Detección de estancamientos (sobrecarga progresiva)
  - Comparativa de progreso entre sesiones
"""

import json
from pathlib import Path
from datetime import datetime
from user_profile import UserProfile

DB_PATH = Path(__file__).parent / "usuarios.json"


# ──────────────────────────────────────────────
#  Helpers de persistencia
# ──────────────────────────────────────────────

def _load_db() -> dict:
    if DB_PATH.exists():
        try:
            with open(DB_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return {"sessions": data}
                if isinstance(data, dict) and "sessions" not in data:
                    return {"sessions": list(data.values())}
                return data
        except (json.JSONDecodeError, Exception):
            pass
    return {"sessions": []}


def _save_db(data: dict) -> None:
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ──────────────────────────────────────────────
#  API pública
# ──────────────────────────────────────────────

def save_profile(profile: UserProfile) -> None:
    """Guarda la sesión del usuario en la base de datos."""
    db = _load_db()
    entry = profile.to_dict()
    entry["saved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db["sessions"].append(entry)
    _save_db(db)


def list_users() -> list:
    """Retorna todas las sesiones guardadas (todas las consultas de todos los usuarios)."""
    db = _load_db()
    return db.get("sessions", [])


def get_user_history(user_id: str) -> list:
    """Retorna el historial completo de un usuario específico, ordenado por fecha."""
    db = _load_db()
    sessions = [s for s in db.get("sessions", []) if s.get("user_id") == user_id]
    return sorted(sessions, key=lambda x: x.get("saved_at", ""))


def get_last_session(user_id: str) -> dict | None:
    """Retorna la consulta más reciente de un usuario."""
    history = get_user_history(user_id)
    return history[-1] if history else None


def get_progress_summary(user_id: str) -> dict:
    """
    Calcula el progreso del usuario entre su primera y última sesión.
    Útil para detectar estancamientos y aplicar sobrecarga progresiva.
    """
    history = get_user_history(user_id)
    if not history:
        return {
            "sesiones":            0,
            "progreso_disponible": False,
            "primera_sesion":      "N/A",
            "ultima_sesion":       "N/A",
            "delta_peso_kg":       0.0,
            "delta_calorias":      0.0,
            "objetivo_inicial":    "N/A",
            "objetivo_actual":     "N/A",
        }

    primera = history[0]
    ultima  = history[-1]

    delta_peso    = round(ultima.get("weight", 0) - primera.get("weight", 0), 2)
    delta_calorias = round(ultima.get("target_calories", 0) - primera.get("target_calories", 0), 2)

    return {
        "sesiones":            len(history),
        "progreso_disponible": len(history) > 1,
        "primera_sesion":      primera.get("saved_at", ""),
        "ultima_sesion":       ultima.get("saved_at", ""),
        "delta_peso_kg":       delta_peso,
        "delta_calorias":      delta_calorias,
        "objetivo_inicial":    primera.get("objective", ""),
        "objetivo_actual":     ultima.get("objective", ""),
    }


def db_stats() -> dict:
    """Estadísticas generales de la base de datos."""
    sessions = list_users()
    users_set = {s.get("user_id") for s in sessions if s.get("user_id")}
    return {
        "total_sesiones": len(sessions),
        "usuarios_unicos": len(users_set),
    }
