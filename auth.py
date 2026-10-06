"""
auth.py
=======
Módulo de autenticación del Sistema Experto FitExpert.

Seguridad (v2 — auditoría de seguridad):
  - Contraseñas con **Argon2id** (OWASP Password Storage Cheat Sheet:
    t=2, m=19 MiB, p=1) mediante `argon2-cffi`.
  - **Fallback automático** a PBKDF2-HMAC-SHA256 (stdlib, 600 000
    iteraciones, recomendación OWASP) si `argon2-cffi` no está
    instalado. El formato del hash identifica el esquema usado.
  - **Migración automática** de los hashes históricos SHA-256 (64
    caracteres hex) al esquema actual en el primer login exitoso:
    ningún usuario existente pierde su acceso.
  - **Sin enumeración de usuarios**: login devuelve siempre el mismo
    mensaje genérico, y se ejecuta una verificación "falsa" cuando el
    usuario no existe para igualar el tiempo de respuesta.
  - **Rate limiting**: bloqueo temporal tras intentos fallidos
    consecutivos (por usuario y global).
  - **Escritura atómica** (archivo temporal + os.replace) y respaldo
    del archivo corrupto antes de continuar, para no perder datos.
  - Validación de credenciales compartida con `validation.py`
    (mismos mensajes en las tres interfaces).

Contrato público (sin cambios respecto de v1):
    register(username, password) -> {"ok", "user_id"?, "username"?, "error"?}
    login(username, password)    -> {"ok", "user_id"?, "username"?, "error"?}
    username_exists(username)    -> bool
    validate_session(session)    -> dict | None
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
import shutil
import time
import uuid
from datetime import datetime
from pathlib import Path

from validation import validate_credentials

logger = logging.getLogger("fitexpert.auth")

AUTH_DB_PATH = Path(__file__).parent / "auth_db.json"

# ──────────────────────────────────────────────
#  Configuración criptográfica
# ──────────────────────────────────────────────

# OWASP Password Storage Cheat Sheet: Argon2id m=19MiB t=2 p=1
# (mínimo recomendado; coste ~20-30 ms — adecuado para app local)
ARGON2_TIME_COST = 2
ARGON2_MEMORY_KIB = 19 * 1024
ARGON2_PARALLELISM = 1

# OWASP: PBKDF2-HMAC-SHA256 ≥ 600 000 iteraciones
PBKDF2_ITERATIONS = 600_000
PBKDF2_PREFIX = "pbkdf2_sha256"

_LEGACY_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")

try:  # dependencia opcional (recomendada)
    from argon2 import PasswordHasher
    from argon2.exceptions import (
        VerificationError as _ArgonVerificationError,
        InvalidHashError as _ArgonInvalidHashError,
    )
    _ph = PasswordHasher(
        time_cost=ARGON2_TIME_COST,
        memory_cost=ARGON2_MEMORY_KIB,
        parallelism=ARGON2_PARALLELISM,
        hash_len=32,
        salt_len=16,
    )
    ARGON2_AVAILABLE = True
except ImportError:  # pragma: no cover - depende del entorno
    _ph = None
    ARGON2_AVAILABLE = False
    _ArgonVerificationError = Exception
    _ArgonInvalidHashError = Exception

PREFERRED_SCHEME = "argon2id" if ARGON2_AVAILABLE else "pbkdf2"


# ──────────────────────────────────────────────
#  Rate limiting (en memoria, por proceso)
# ──────────────────────────────────────────────

_RATE_WINDOW_S = 300.0        # ventana de 5 minutos
_MAX_FAILS_PER_USER = 5       # intentos fallidos por usuario en la ventana
_MAX_FAILS_GLOBAL = 30        # intentos fallidos globales en la ventana
_failures: dict[str, list[float]] = {"_global_": []}
_locked_until: dict[str, float] = {}
_lock_strikes: dict[str, int] = {}


def _prune(now: float) -> None:
    for key in list(_failures):
        _failures[key] = [t for t in _failures[key] if now - t < _RATE_WINDOW_S]
        if not _failures[key]:
            del _failures[key]


def _is_rate_limited(username: str, now: float | None = None) -> str | None:
    now = now if now is not None else time.monotonic()
    key = (username or "").lower()
    until = _locked_until.get(key)
    if until is not None:
        if now < until:
            return ("Demasiados intentos fallidos. Espera unos segundos antes "
                    "de volver a intentarlo.")
        _locked_until.pop(key, None)
        _lock_strikes.pop(key, None)
    return None


def _register_failure(username: str) -> None:
    now = time.monotonic()
    _prune(now)
    key = (username or "").lower()
    _failures.setdefault(key, []).append(now)
    _failures.setdefault("_global_", []).append(now)

    if len(_failures.get(key, [])) >= _MAX_FAILS_PER_USER:
        # Bloqueo progresivo: 30 s por reincidencia (máximo 15 minutos)
        strikes = _lock_strikes.get(key, 0) + 1
        _lock_strikes[key] = strikes
        _locked_until[key] = now + min(30.0 * strikes, 900.0)
        _failures[key] = []
    if len(_failures.get("_global_", [])) >= _MAX_FAILS_GLOBAL:
        _failures["_global_"] = []
        _locked_until["_global_"] = now + 60.0


def _clear_failures(username: str) -> None:
    _failures.pop(username.lower(), None)
    _locked_until.pop(username.lower(), None)


def reset_rate_limit() -> None:
    """Reinicia el bloqueo por intentos fallidos (uso en pruebas)."""
    _failures.clear()
    _failures["_global_"] = []
    _locked_until.clear()


# ──────────────────────────────────────────────
#  Hashing de contraseñas
# ──────────────────────────────────────────────

def _hash_password(password: str) -> str:
    """
    Hashea la contraseña con el esquema preferido:
    Argon2id si `argon2-cffi` está instalado; PBKDF2-HMAC-SHA256 si no.
    Devuelve una cadena PHC/identificable por prefijo.
    """
    if ARGON2_AVAILABLE:
        return _ph.hash(password)
    return _hash_pbkdf2(password)


def _hash_pbkdf2(password: str, salt: bytes | None = None,
                 iterations: int = PBKDF2_ITERATIONS) -> str:
    salt = salt or os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"{PBKDF2_PREFIX}${iterations}${salt.hex()}${dk.hex()}"


def _verify_password(password: str, stored: str) -> tuple[bool, bool]:
    """
    Verifica una contraseña contra un hash almacenado.

    Returns:
        (válido, es_legacy) — es_legacy indica que el hash estaba en el
        formato histórico SHA-256 y debe migrarse.
    """
    if not isinstance(stored, str) or not stored:
        return False, False

    # Formato histórico: SHA-256 sin sal (64 hex)
    if _LEGACY_SHA256_RE.match(stored):
        digest = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(digest, stored.lower()), True

    # Argon2 (PHC: $argon2id$...)
    if stored.startswith("$argon2"):
        if not ARGON2_AVAILABLE:
            logger.error("El hash es Argon2 pero argon2-cffi no está instalado.")
            return False, False
        try:
            return _ph.verify(stored, password), False
        except (_ArgonVerificationError, _ArgonInvalidHashError, ValueError):
            return False, False
        except Exception:  # pragma: no cover - defensa
            logger.exception("Error inesperado verificando hash Argon2")
            return False, False

    # PBKDF2 con prefijo
    if stored.startswith(PBKDF2_PREFIX + "$"):
        try:
            _, iters_s, salt_hex, dk_hex = stored.split("$")
            dk = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"),
                bytes.fromhex(salt_hex), int(iters_s))
            return hmac.compare_digest(dk.hex(), dk_hex), False
        except (ValueError, TypeError):
            return False, False

    return False, False


def _needs_upgrade(stored: str) -> bool:
    """True si el hash usa un esquema distinto al preferido."""
    if _LEGACY_SHA256_RE.match(stored or ""):
        return True
    if PREFERRED_SCHEME == "argon2id":
        return not (stored or "").startswith("$argon2")
    return not (stored or "").startswith(PBKDF2_PREFIX)


def _dummy_verify() -> None:
    """Verificación con coste similar cuando el usuario no existe
    (mitiga la enumeración de usuarios por tiempo de respuesta)."""
    if ARGON2_AVAILABLE:
        try:
            _ph.verify(
                "$argon2id$v=19$m=65536,t=2,p=1$c29tZXNhbHRzb21lc2FsdA$" +
                "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "dummy")
        except Exception:
            pass
    else:
        _hash_pbkdf2("dummy")


# ──────────────────────────────────────────────
#  Persistencia (atómica + respaldo ante corrupción)
# ──────────────────────────────────────────────

def _load_auth_db() -> dict:
    """
    Carga la base de usuarios.

    - Si el archivo está corrupto se respalda como
      `auth_db.json.corrupt-<fecha>.bak` y se continúa con una base
      vacía: los datos originales nunca se destruyen.
    - Las entradas mal formadas se ignoran sin abortar la carga.
    """
    path = Path(AUTH_DB_PATH)
    if not path.exists():
        return {"users": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or not isinstance(data.get("users"), list):
            raise ValueError("estructura inesperada")
    except (json.JSONDecodeError, ValueError, OSError, UnicodeDecodeError) as exc:
        backup = path.with_name(
            f"{path.name}.corrupt-{datetime.now().strftime('%Y%m%d-%H%M%S')}.bak")
        try:
            shutil.copy2(path, backup)
            logger.warning("Base de autenticación corrupta (%s). Respaldo en %s",
                           exc, backup)
        except OSError:
            logger.exception("No se pudo respaldar auth_db corrupto")
        return {"users": []}

    users = []
    for u in data.get("users", []):
        if isinstance(u, dict) and u.get("username") and u.get("password"):
            if not u.get("user_id"):
                u["user_id"] = str(uuid.uuid4())
            users.append(u)
    return {"users": users}


def _save_auth_db(data: dict) -> None:
    """Escritura atómica: temporal + os.replace (sin archivos a medias)."""
    path = Path(AUTH_DB_PATH)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def _find_user(db: dict, username: str) -> dict | None:
    key = username.strip().lower()
    for user in db["users"]:
        if str(user.get("username", "")).lower() == key:
            return user
    return None


# ──────────────────────────────────────────────
#  API pública
# ──────────────────────────────────────────────

def register(username: str, password: str) -> dict:
    """
    Registra un nuevo usuario.

    Validación compartida con `validation.validate_credentials`:
    usuario ≥ 3 caracteres (máx 32), contraseña ≥ 8 y ≤ 128
    caracteres y distinta del usuario.

    Retorna:
        {"ok": True, "user_id": "...", "username": "..."}
        {"ok": False, "error": "mensaje amigable"}
    """
    checked = validate_credentials(username, password, for_register=True)
    if not checked["ok"]:
        return {"ok": False, "error": checked["error"]}
    username, password = checked["username"], checked["password"]

    now = time.monotonic()
    locked = _is_rate_limited(username, now)
    if locked:
        return {"ok": False, "error": locked}

    db = _load_auth_db()
    if _find_user(db, username):
        return {"ok": False,
                "error": f"El usuario '{username}' ya existe. Elige otro nombre."}

    user_id = str(uuid.uuid4())
    db["users"].append({
        "user_id": user_id,
        "username": username,
        "password": _hash_password(password),
        "created_at": datetime.now().isoformat(timespec="seconds"),
    })
    try:
        _save_auth_db(db)
    except OSError:
        logger.exception("No se pudo persistir auth_db")
        return {"ok": False,
                "error": "No se pudo guardar el registro. "
                         "Revisa los permisos del directorio y vuelve a intentar."}

    _clear_failures(username)
    return {"ok": True, "user_id": user_id, "username": username}


def login(username: str, password: str) -> dict:
    """
    Verifica las credenciales de un usuario.

    - Mensaje genérico ante usuario inexistente o contraseña errónea
      (no revela cuál falló).
    - Bloqueo temporal tras intentos fallidos consecutivos.
    - Migra automáticamente los hashes legacy SHA-256 (y actualiza
      PBKDF2 → Argon2id cuando `argon2-cffi` está disponible) tras un
      login exitoso, sin romper el acceso de usuarios existentes.

    Retorna:
        {"ok": True, "user_id": "...", "username": "..."}
        {"ok": False, "error": "mensaje amigable"}
    """
    username = (username or "").strip()
    password = password or ""
    generic_error = "Usuario o contraseña incorrectos."

    now = time.monotonic()
    locked = _is_rate_limited("_global_", now) or _is_rate_limited(username, now)
    if locked:
        return {"ok": False, "error": locked}

    if not username or not password:
        return {"ok": False, "error": "Ingresa tu usuario y contraseña."}

    db = _load_auth_db()
    user = _find_user(db, username)

    if user is None:
        _dummy_verify()               # iguala el tiempo de respuesta
        _register_failure(username)
        return {"ok": False, "error": generic_error}

    valid, is_legacy = _verify_password(password, user.get("password", ""))
    if not valid:
        _register_failure(username)
        return {"ok": False, "error": generic_error}

    # Migración / mejora de esquema tras autenticación exitosa
    if is_legacy or _needs_upgrade(user.get("password", "")):
        try:
            user["password"] = _hash_password(password)
            _save_auth_db(db)
            logger.info("Hash de '%s' migrado a %s.", username, PREFERRED_SCHEME)
        except OSError:
            logger.exception("No se pudo migrar el hash de %s", username)

    _clear_failures(username)
    return {"ok": True, "user_id": user["user_id"], "username": user["username"]}


def username_exists(username: str) -> bool:
    """Verifica si un nombre de usuario ya está registrado."""
    if not username or not str(username).strip():
        return False
    return _find_user(_load_auth_db(), str(username)) is not None


def validate_session(session: dict | None) -> dict | None:
    """
    Valida una sesión persistida (`local_session.json`) frente a la
    base de usuarios: devuelve la sesión saneada si el usuario sigue
    existiendo; None si es inválida, incompleta o el usuario fue
    eliminado (evita sesiones huérfanas o manipuladas).
    """
    if not isinstance(session, dict):
        return None
    user_id = session.get("user_id")
    username = session.get("username")
    if not user_id or not username:
        return None
    db = _load_auth_db()
    user = next((u for u in db["users"] if u.get("user_id") == user_id), None)
    if user is None:
        return None
    return {"user_id": user_id, "username": user["username"]}


def change_password(username: str, old_password: str,
                    new_password: str) -> dict:
    """Cambia la contraseña de un usuario autenticado previamente."""
    result = login(username, old_password)
    if not result.get("ok"):
        return {"ok": False, "error": "La contraseña actual no es correcta."}

    checked = validate_credentials(username, new_password, for_register=True)
    if not checked["ok"]:
        return {"ok": False, "error": checked["error"]}
    if checked["password"] == old_password:
        return {"ok": False,
                "error": "La nueva contraseña debe ser distinta a la actual."}

    db = _load_auth_db()
    user = _find_user(db, username)
    if user is None:
        return {"ok": False, "error": generic_error_msg()}
    user["password"] = _hash_password(checked["password"])
    try:
        _save_auth_db(db)
    except OSError:
        return {"ok": False,
                "error": "No se pudo guardar la nueva contraseña."}
    return {"ok": True, "username": user["username"]}


def generic_error_msg() -> str:
    """Mensaje genérico compartido (no revela si el usuario existe)."""
    return "Usuario o contraseña incorrectos."
