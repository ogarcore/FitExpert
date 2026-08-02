"""
auth.py
=======
Módulo de autenticación del Sistema Experto.

Gestiona registro e inicio de sesión de usuarios.
Las contraseñas se almacenan hasheadas con SHA-256.
Los nombres de usuario son únicos.
"""

import json
import hashlib
import uuid
from pathlib import Path

AUTH_DB_PATH = Path(__file__).parent / "auth_db.json"


# ──────────────────────────────────────────────
#  Helpers de persistencia
# ──────────────────────────────────────────────

def _load_auth_db() -> dict:
    if AUTH_DB_PATH.exists():
        try:
            with open(AUTH_DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {"users": []}


def _save_auth_db(data: dict) -> None:
    with open(AUTH_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _hash_password(password: str) -> str:
    """Retorna el hash SHA-256 de la contraseña."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# ──────────────────────────────────────────────
#  API pública
# ──────────────────────────────────────────────

def register(username: str, password: str) -> dict:
    """
    Registra un nuevo usuario.

    Retorna:
        {"ok": True, "user_id": "...", "username": "..."}
        {"ok": False, "error": "mensaje de error"}
    """
    username = username.strip()

    if not username:
        return {"ok": False, "error": "El nombre de usuario no puede estar vacío."}
    if len(username) < 3:
        return {"ok": False, "error": "El nombre de usuario debe tener al menos 3 caracteres."}
    if not password or len(password) < 4:
        return {"ok": False, "error": "La contraseña debe tener al menos 4 caracteres."}

    db = _load_auth_db()

    # Verificar duplicado (insensible a mayúsculas)
    for user in db["users"]:
        if user["username"].lower() == username.lower():
            return {"ok": False, "error": f"El usuario '{username}' ya existe. Elige otro nombre."}

    user_id = str(uuid.uuid4())
    db["users"].append({
        "user_id":  user_id,
        "username": username,
        "password": _hash_password(password),
    })
    _save_auth_db(db)

    return {"ok": True, "user_id": user_id, "username": username}


def login(username: str, password: str) -> dict:
    """
    Verifica las credenciales de un usuario.

    Retorna:
        {"ok": True, "user_id": "...", "username": "..."}
        {"ok": False, "error": "mensaje de error"}
    """
    username = username.strip()
    db = _load_auth_db()

    for user in db["users"]:
        if user["username"].lower() == username.lower():
            if user["password"] == _hash_password(password):
                return {"ok": True, "user_id": user["user_id"], "username": user["username"]}
            else:
                return {"ok": False, "error": "Contraseña incorrecta."}

    return {"ok": False, "error": f"El usuario '{username}' no existe."}


def username_exists(username: str) -> bool:
    """Verifica si un nombre de usuario ya está registrado."""
    db = _load_auth_db()
    return any(u["username"].lower() == username.lower() for u in db["users"])
