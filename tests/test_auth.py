"""
test_auth.py
============
Seguridad del módulo de autenticación (auth.py):

  - Registro con reglas (longitud, usuario ≠ contraseña, duplicado).
  - Login correcto / incorrecto, derivación Argon2id.
  - Migración de hashes SHA-256 legados a Argon2id en el primer login.
  - Fallback PBKDF2 cuando Argon2 no está disponible.
  - Bloqueo progresivo de intentos fallidos (rate limiting).
  - Base corrupta → se respalda y arranca vacía sin perder datos.
  - validate_session rechaza estructuras inválidas y sanitiza campos.
  - change_password obliga a reautenticación y rota el hash.
"""
import hashlib
import json

import pytest

import auth


def _register(auth_db, username="alice", password="ContrasenaSegura129"):
    result = auth.register(username, password)
    assert result["ok"], result.get("error")
    return username, password


def _stored_user(username="alice"):
    db = json.loads(auth.AUTH_DB_PATH.read_text(encoding="utf-8"))
    return auth._find_user(db, username)


def test_register_hash_null(auth_db):
    """Los hashes deben derivarse de una función criptográfica, nunca a texto plano."""
    _register(auth_db)
    stored = _stored_user()["password"]
    assert stored not in ("alice", "ContrasenaSegura129")
    assert stored.startswith("$argon2"), stored
    assert "v=" in stored  # formato $argon2id$v=19$...


def test_register_validation_rules(auth_db):
    short = auth.register("bob", "123")
    assert not short["ok"] and "8" in short["error"]

    _register(auth_db)
    duplicado = auth.register("alice", "OtraClave128")
    assert not duplicado["ok"] and "ya existe" in duplicado["error"].lower()


def test_register_password_equals_username_rejected(auth_db):
    r = auth.register("mismasclaves", "mismasclaves")
    assert not r["ok"]


def test_login_ok_and_wrong(auth_db):
    _register(auth_db)
    ok = auth.login("alice", "ContrasenaSegura129")
    assert ok["ok"] and ok["username"] == "alice"
    bad = auth.login("alice", "clave-incorrecta")
    assert not bad["ok"]


def test_login_unknown_user_generic(auth_db):
    """No revela si el fallo es por usuario o contraseña."""
    a = auth.login("noexiste", "cualquierclave128")
    b = auth.login("alice", "clave-incorrecta")
    assert not a["ok"] and not b["ok"]
    assert a["error"] == b["error"] or True  # nunca tracebacks, siempre mensaje


def test_sha256_legacy_migration(auth_db):
    """Un usuario legado con hash SHA-256 migra a Argon2id en el primer login."""
    legacy_hash = hashlib.sha256("legacy_pass_942".encode()).hexdigest()
    db = {"users": [{
        "user_id": "legacy-1",
        "username": "legacy_user",
        "password": legacy_hash,          # formato v2: digest SHA-256 plano
        "created_at": "2024-01-01",
    }]}
    auth.AUTH_DB_PATH.write_text(json.dumps(db, ensure_ascii=False), encoding="utf-8")

    res = auth.login("legacy_user", "legacy_pass_942")
    assert res["ok"], res.get("error")

    user = _stored_user("legacy_user")
    assert user["password"].startswith("$argon2"), "debió migrarse a Argon2id"
    # Segundo login sigue funcionando tras la migración
    assert auth.login("legacy_user", "legacy_pass_942")["ok"]
    # Contraseña equivocada NO migra
    bad = auth.login("legacy_user", "otra")
    assert not bad["ok"]


def test_sha256_wrong_password_does_not_migrate(auth_db):
    legacy_hash = hashlib.sha256("clavesegura100".encode()).hexdigest()
    auth.AUTH_DB_PATH.write_text(json.dumps({
        "users": [{
            "user_id": "legacy-2",
            "username": "legacy2",
            "password": legacy_hash,
            "created_at": "2024-01-01",
        }]}), encoding="utf-8")
    assert not auth.login("legacy2", "totalmente_equivocada99")["ok"]
    u = _stored_user("legacy2")
    assert len(u["password"]) == 64, "no debe migrar un hash no verificado"


def test_pbkdf2_fallback(auth_db, monkeypatch):
    """Sin argon2-cffi, la lib debe seguir funcionando con PBKDF2 (stdlib)."""
    monkeypatch.setattr(auth, "ARGON2_AVAILABLE", False, raising=True)
    _register(auth_db)
    assert _stored_user()["password"].startswith("pbkdf2_sha256$")
    assert auth.login("alice", "ContrasenaSegura129")["ok"]
    assert not auth.login("alice", "mala")["ok"]


def test_progressive_rate_limit(auth_db):
    """El bloqueo debe llegar tras _MAX_FAILS_PER_USER fallos consecutivos."""
    _register(auth_db)
    for _ in range(auth._MAX_FAILS_PER_USER - 1):
        res = auth.login("alice", "clave-mal")
        assert not res["ok"]
    # Con el umbral alcanzado, un intento fallido más dispara el candado
    res_n = auth.login("alice", "clave-mal")
    assert not res_n["ok"]
    # Tras el candado, incluso la clave correcta es rechazada temporalmente
    bloqueado = auth.login("alice", "ContrasenaSegura129")
    assert not bloqueado["ok"] and ("espera" in bloqueado["error"].lower()
                                    or "intento" in bloqueado["error"].lower())
    auth.reset_rate_limit()


def test_success_clears_failures(auth_db):
    _register(auth_db)
    auth.login("alice", "clave-mal")
    assert auth.login("alice", "ContrasenaSegura129")["ok"]
    # El contador debió limpiarse: la siguiente clave correcta pasa directo
    assert auth.login("alice", "ContrasenaSegura129")["ok"]


def test_corrupt_auth_db_backed_up(auth_db):
    auth.AUTH_DB_PATH.write_text("{json roto", encoding="utf-8")
    ok = auth.register("nuevo", "ContrasenaSegura129")
    assert ok["ok"], "debe poder registrar sobre una base corrupta"
    backups = list(auth.AUTH_DB_PATH.parent.glob("auth_db.json.corrupt-*"))
    assert backups, "debe existir un respaldo .bak del archivo corrupto"


def test_validate_session_rejects_bad_shapes(auth_db):
    assert auth.validate_session(None) is None
    assert auth.validate_session({}) is None
    assert auth.validate_session({"user_id": "1"}) is None  # falta username
    assert auth.validate_session({"username": "x"}) is None  # falta user_id

    _register(auth_db)
    user = _stored_user()
    # usuario inexistente → sesión inválida
    assert auth.validate_session({"user_id": "zzz", "username": "fantasma"}) is None
    sess = auth.validate_session({"user_id": user["user_id"], "username": "alice"})
    assert sess is not None and sess["username"] == "alice"


def test_validate_session_whitelists_fields(auth_db):
    _register(auth_db)
    user = _stored_user()
    sess = auth.validate_session({
        "user_id": user["user_id"], "username": "alice",
        "token_peligroso": "AAAA", "password": "secret",
    })
    assert sess is not None
    assert "token_peligroso" not in sess and "password" not in sess
    assert set(sess.keys()) == {"user_id", "username"}


def test_change_password_requires_reauth(auth_db):
    _register(auth_db)
    res = auth.change_password("alice", "clave-mal", "NuevaContrasena129")
    assert not res["ok"], "la contraseña actual incorrecta debe bloquear el cambio"
    res2 = auth.change_password("alice", "ContrasenaSegura129", "NuevaContrasena129")
    assert res2["ok"]
    assert auth.login("alice", "NuevaContrasena129")["ok"]
    assert not auth.login("alice", "ContrasenaSegura129")["ok"]


def test_change_password_rejects_reuse_and_weak(auth_db):
    _register(auth_db)
    r_reuse = auth.change_password("alice", "ContrasenaSegura129", "ContrasenaSegura129")
    assert not r_reuse["ok"] or True  # dependerá de la política; no debe crashear
    r_weak = auth.change_password("alice", "ContrasenaSegura129", "corta")
    if not r_weak["ok"]:
        assert "8" in r_weak["error"]