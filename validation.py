"""
validation.py
=============
Validación centralizada de entradas del Sistema Experto.

Todos los formularios (CLI, Streamlit, Escritorio) delegan aquí para que:
  - los rangos y mensajes sean idénticos en las tres interfaces;
  - ningún valor NaN/Inf/negativo/texto llegue al motor de inferencia;
  - las combinaciones imposibles se detecten antes de persistir;
  - los mensajes de error sean comprensibles para una persona normal
    (nunca "ValueError", "KeyError", "NoneType"...).

API principal:
    validate_evaluation(data) -> (valores_limpios, errores, advertencias)

Cada validador puntual devuelve FieldResult(ok, value, error).
"""

import math
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

from user_profile import (
    ACTIVITY_LABELS, ALLERGY_OPTIONS, DIET_TYPES, EQUIPMENT_OPTIONS,
    EXPERIENCE_LABELS, INJURY_OPTIONS, INJURY_RED_FLAGS, INJURY_SEVERITY_OPTIONS,
    INTOLERANCE_OPTIONS, OBJECTIVE_LABELS, PREFERENCE_OPTIONS,
    SEX_OPTIONS, TRAINING_PLACE_LABELS,
)


# ──────────────────────────────────────────────
#  Estructuras
# ──────────────────────────────────────────────

@dataclass
class FieldResult:
    ok: bool
    value: Any = None
    error: str | None = None


# Límites operativos del sistema (biológicamente razonables)
AGE_MIN, AGE_MAX = 10, 100
WEIGHT_MIN, WEIGHT_MAX = 30.0, 300.0
HEIGHT_MIN, HEIGHT_MAX = 100.0, 250.0
BODY_FAT_MIN, BODY_FAT_MAX = 3.0, 70.0
NAME_MAX = 60
NOTES_MAX = 300
MEAL_FREQ_MIN, MEAL_FREQ_MAX = 3, 5

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_NAME_ALLOWED = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 .,'()\-_]+$")


# ──────────────────────────────────────────────
#  Helpers de conversión segura
# ──────────────────────────────────────────────

def _to_float(raw: Any) -> float | None:
    """Convierte a float descartando texto, NaN e infinitos. Vacío → None."""
    if raw is None:
        return None
    if isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        val = float(raw)
    else:
        text = str(raw).strip().replace(",", ".")
        if not text:
            return None
        try:
            val = float(text)
        except (TypeError, ValueError):
            return None
    if math.isnan(val) or math.isinf(val):
        return None
    return val


def _to_int(raw: Any) -> int | None:
    """Convierte a entero estricto (sin decimales ni texto). Vacío → None."""
    if raw is None or isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return raw
    if isinstance(raw, float):
        return int(raw) if raw.is_integer() else None
    text = str(raw).strip()
    if not text or not re.fullmatch(r"[+-]?\d+", text):
        return None
    try:
        return int(text)
    except (TypeError, ValueError):
        return None


def sanitize_single_line(raw: Any, max_len: int = NAME_MAX) -> str:
    """Normaliza texto de una línea: quita controles, colapsa espacios, recorta."""
    text = "" if raw is None else str(raw)
    text = unicodedata.normalize("NFC", text)
    text = _CONTROL_CHARS.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len]


# ──────────────────────────────────────────────
#  Validadores puntuales
# ──────────────────────────────────────────────

def validate_name(raw: Any) -> FieldResult:
    name = sanitize_single_line(raw, NAME_MAX)
    if not name:
        return FieldResult(False, None, "Ingresa tu nombre para personalizar el plan.")
    if len(name) < 2:
        return FieldResult(False, None, "El nombre debe tener al menos 2 caracteres.")
    if len(name) > NAME_MAX:
        return FieldResult(False, None, f"El nombre no puede superar {NAME_MAX} caracteres.")
    if not _NAME_ALLOWED.match(name):
        return FieldResult(False, None,
                           "El nombre solo puede contener letras, números y los símbolos . , ' ( ) - _")
    return FieldResult(True, name)


def validate_age(raw: Any) -> FieldResult:
    age = _to_int(raw)
    if age is None:
        return FieldResult(False, None, "La edad debe ser un número entero (sin decimales ni texto).")
    if age < AGE_MIN:
        return FieldResult(False, None, f"La edad mínima admitida es {AGE_MIN} años.")
    if age > AGE_MAX:
        return FieldResult(False, None, f"La edad máxima admitida es {AGE_MAX} años.")
    return FieldResult(True, age)


def validate_weight(raw: Any) -> FieldResult:
    weight = _to_float(raw)
    if weight is None:
        return FieldResult(False, None, "El peso debe ser un número (usa punto o coma decimal).")
    if weight <= 0:
        return FieldResult(False, None, "El peso debe ser mayor que cero.")
    if weight < WEIGHT_MIN:
        return FieldResult(False, None, f"El peso mínimo admitido es {WEIGHT_MIN:.0f} kg.")
    if weight > WEIGHT_MAX:
        return FieldResult(False, None, f"El peso máximo admitido es {WEIGHT_MAX:.0f} kg.")
    return FieldResult(True, round(weight, 2))


def validate_height(raw: Any) -> FieldResult:
    height = _to_float(raw)
    if height is None:
        return FieldResult(False, None, "La estatura debe ser un número en centímetros (ej: 175).")
    if height <= 0:
        return FieldResult(False, None, "La estatura debe ser mayor que cero.")
    if height < HEIGHT_MIN:
        return FieldResult(False, None, f"La estatura mínima admitida es {HEIGHT_MIN:.0f} cm.")
    if height > HEIGHT_MAX:
        return FieldResult(False, None, f"La estatura máxima admitida es {HEIGHT_MAX:.0f} cm.")
    return FieldResult(True, round(height, 1))


def validate_body_fat(raw: Any) -> FieldResult:
    """Porcentaje de grasa opcional: vacío → 0.0 (dato no informado)."""
    if raw is None or str(raw).strip() == "":
        return FieldResult(True, 0.0)
    pct = _to_float(raw)
    if pct is None:
        return FieldResult(False, None, "El porcentaje de grasa debe ser un número (ej: 18.5).")
    if pct < 0:
        return FieldResult(False, None, "El porcentaje de grasa no puede ser negativo.")
    if pct == 0:
        return FieldResult(True, 0.0)
    if pct < BODY_FAT_MIN:
        return FieldResult(False, None, f"Un porcentaje de grasa válido está entre {BODY_FAT_MIN:.0f}% y {BODY_FAT_MAX:.0f}%.")
    if pct > BODY_FAT_MAX:
        return FieldResult(False, None, f"Un porcentaje de grasa válido está entre {BODY_FAT_MIN:.0f}% y {BODY_FAT_MAX:.0f}%.")
    return FieldResult(True, round(pct, 1))


def validate_choice(raw: Any, domain: dict, label: str) -> FieldResult:
    """Valida que el valor pertenezca al dominio (valores o etiquetas humanas)."""
    if isinstance(raw, str):
        text = sanitize_single_line(raw, 80)
        if text in domain:
            return FieldResult(True, text)
        # Acepta la etiqueta humana y devuelve la clave canónica
        for key, human in domain.items():
            if isinstance(human, str) and human.lower() == text.lower():
                return FieldResult(True, key)
        # Variaciones toleradas de la etiqueta (p.ej. "Masculino" → "masculino")
        lowered = text.lower()
        for key in domain:
            if isinstance(key, str) and key.lower() == lowered:
                return FieldResult(True, key)
    return FieldResult(False, None, f"Selecciona una opción válida para: {label}.")


def validate_sex(raw: Any) -> FieldResult:
    result = validate_choice(raw, SEX_OPTIONS, "sexo")
    if not result.ok:
        return result
    # SEX_OPTIONS usa claves numéricas legadas (1=masculino, 2=femenino);
    # el resto del sistema (reglas BIO, cálculos, PDF, hechos) consume el
    # valor canónico "masculino"/"femenino". Siempre devolver ese valor.
    canon = SEX_OPTIONS.get(result.value, result.value)
    return FieldResult(True, canon)


def validate_objective(raw: Any) -> FieldResult:
    return validate_choice(raw, OBJECTIVE_LABELS, "objetivo")


def validate_activity(raw: Any) -> FieldResult:
    return validate_choice(raw, ACTIVITY_LABELS, "nivel de actividad")


def validate_experience(raw: Any) -> FieldResult:
    return validate_choice(raw, EXPERIENCE_LABELS, "experiencia")


def validate_training_place(raw: Any) -> FieldResult:
    return validate_choice(raw, TRAINING_PLACE_LABELS, "lugar de entrenamiento")


def validate_diet(raw: Any) -> FieldResult:
    result = validate_choice(raw, DIET_TYPES, "tipo de dieta")
    return FieldResult(True, "omnivoro") if not result.ok else result


def validate_meal_frequency(raw: Any) -> FieldResult:
    freq = _to_int(raw)
    if freq is None:
        return FieldResult(False, None, "La frecuencia de comidas debe ser un número entero.")
    if freq < MEAL_FREQ_MIN or freq > MEAL_FREQ_MAX:
        return FieldResult(False, None,
                           f"Elige entre {MEAL_FREQ_MIN} y {MEAL_FREQ_MAX} comidas al día.")
    return FieldResult(True, freq)


def validate_injury_severity(raw: Any, injuries: list) -> FieldResult:
    if not injuries:
        return FieldResult(True, "ninguna")
    if raw in (None, ""):
        return FieldResult(True, "moderada")
    result = validate_choice(raw, INJURY_SEVERITY_OPTIONS, "intensidad de la molestia")
    return FieldResult(True, "moderada") if not result.ok else result


def validate_list(raw: Any, domain: dict, _label: str = "") -> FieldResult:
    """Filtrado de listas: conserva solo claves válidas, descarta basura."""
    if raw is None:
        return FieldResult(True, [])
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, (list, tuple, set)):
        return FieldResult(True, [])
    cleaned = []
    for item in raw:
        if isinstance(item, str) and item in domain and item not in cleaned:
            cleaned.append(item)
    return FieldResult(True, cleaned)


def validate_notes(raw: Any) -> FieldResult:
    text = sanitize_single_line(raw, NOTES_MAX) if raw else ""
    return FieldResult(True, text)


# ──────────────────────────────────────────────
#  Validación cruzada (combinaciones imposibles)
# ──────────────────────────────────────────────

def _cross_validate(values: dict, warnings: list[str], errors: dict) -> None:
    """Comprobaciones que requieren varios campos a la vez."""
    age = values.get("age")
    weight = values.get("weight")
    height = values.get("height")
    sex = values.get("sex")
    objective = values.get("objective")

    # ── Plausibilidad de la combinación peso × estatura ─────────────────────
    if weight and height:
        imc = weight / ((height / 100) ** 2)
        if imc < 10 or imc > 80:
            errors["weight"] = (
                "Revisa la combinación de peso y estatura: el resultado "
                f"(IMC {imc:.1f}) no es plausible."
            )
        elif imc < 12 or imc > 60:
            warnings.append(
                f"El IMC resultante ({imc:.1f}) está en un rango extremo. "
                "Verifica que los datos sean correctos; el plan llevará alertas de seguridad."
            )

    # ── Edad mínima del sistema: 10 años ────────────────────────────────────
    if age is not None and age < 18:
        if objective in ("perdida_grasa", "definicion"):
            warnings.append(
                "Eres menor de edad: el sistema no aplicará déficits calóricos "
                "ni objetivos agresivos de pérdida de peso. Se prioriza crecimiento "
                "y desarrollo, con supervisión de un adulto y profesional de salud."
            )
        if values.get("experience") == "avanzado":
            warnings.append(
                "Para menores se prioriza supervisión y técnica por encima del volumen "
                "o la carga, independientemente de la experiencia declarada."
            )

    # ── Adultos mayores ─────────────────────────────────────────────────────
    if age is not None and age >= 60:
        if values.get("balance_issues"):
            warnings.append(
                "Por los problemas de equilibrio declarados, la rutina priorizará "
                "prevención de caídas y ejercicios con apoyo o supervisión."
            )
        if values.get("activity_level") == "sedentario":
            warnings.append(
                "Sedentarismo en adulto mayor: se empezará con bajo volumen y "
                "progresión gradual. Considera una revisión médica antes de iniciar."
            )

    # ── Alergia a la soja + dieta vegana → fuentes proteicas limitadas ──────
    if (values.get("diet_type") == "vegano"
            and "soja" in (values.get("allergies") or [])):
        warnings.append(
            "Con dieta vegana y alergia a la soja, las fuentes de proteína se "
            "reducen (legumbres, tempeh no soya, quinoa, frutos secos según tolerancia). "
            "Considera supervisión nutricional."
        )

    # ── Celiaquía declarada ─────────────────────────────────────────────────
    if "gluten" in (values.get("allergies") or []):
        warnings.append(
            "Por celiaquía/alergia al gluten declarada, el plan elimina trigo, cebada, "
            "centeno y avena no certificada. La exclusión debe ser total: ante la duda, "
            "el sistema descarta el alimento."
        )

    # ── Síntomas de alarma ──────────────────────────────────────────────────
    if values.get("red_flags"):
        warnings.insert(0, "SÍNTOMAS DE ALARMA DECLARADOS: el sistema no generará "
                           "prescripción de ejercicio. Busca evaluación profesional "
                           "antes de entrenar.")

    # ── Peso extremadamente bajo ────────────────────────────────────────────
    if weight and weight < 45:
        warnings.append(
            "Peso muy bajo: se evitarán déficits calóricos y se recomendará "
            "evaluación profesional antes de cualquier objetivo de pérdida de peso."
        )


# ──────────────────────────────────────────────
#  API principal
# ──────────────────────────────────────────────

def validate_evaluation(data: dict) -> tuple[dict, dict, list]:
    """
    Valida y normaliza una evaluación completa.

    Retorna:
        values  → dict con los valores limpios y canónicos
        errors  → dict {campo: mensaje} (solo campos con error)
        warnings→ list de advertencias comprensibles para el usuario

    Nunca lanza excepciones: cualquier entrada inesperada se traduce en un
    mensaje de error legible.
    """
    data = data or {}
    values: dict = {}
    errors: dict = {}
    warnings: list[str] = []

    checks = [
        ("name",        validate_name,           "nombre"),
        ("age",         validate_age,            "edad"),
        ("sex",         validate_sex,            "sexo"),
        ("weight",      validate_weight,         "peso"),
        ("height",      validate_height,         "estatura"),
        ("body_fat_pct", validate_body_fat,      "% de grasa"),
        ("objective",   validate_objective,      "objetivo"),
        ("activity_level", validate_activity,    "nivel de actividad"),
        ("experience",  validate_experience,     "experiencia"),
        ("training_place", validate_training_place, "lugar de entrenamiento"),
        ("diet_type",   validate_diet,           "tipo de dieta"),
        ("meal_frequency", validate_meal_frequency, "frecuencia de comidas"),
    ]

    for key, fn, label in checks:
        result = fn(data.get(key))
        if result.ok:
            values[key] = result.value
        else:
            errors[key] = result.error or f"Revisa el campo: {label}."

    # Listas / opciones múltiples
    values["injuries"] = validate_list(data.get("injuries"), INJURY_OPTIONS).value
    values["equipment"] = validate_list(data.get("equipment"), EQUIPMENT_OPTIONS).value
    values["allergies"] = validate_list(data.get("allergies"), ALLERGY_OPTIONS).value
    values["intolerances"] = validate_list(data.get("intolerances"), INTOLERANCE_OPTIONS).value
    values["preferences"] = validate_list(data.get("preferences"), PREFERENCE_OPTIONS).value
    values["red_flags"] = validate_list(data.get("red_flags"), INJURY_RED_FLAGS).value

    sev = validate_injury_severity(data.get("injury_severity"), values.get("injuries", []))
    values["injury_severity"] = sev.value if sev.ok else "moderada"
    values["balance_issues"] = bool(data.get("balance_issues", False))
    values["notes"] = validate_notes(data.get("notes")).value

    # Coherencia: sin lesiones declaradas no hay severidad
    if not values["injuries"]:
        values["injury_severity"] = "ninguna"
        values["balance_issues"] = False

    # Si hay dolor agudo, debe existir una lesión declarada o bandera roja
    if values["injury_severity"] == "aguda" and not values["injuries"] \
            and not values["red_flags"]:
        values["injury_severity"] = "moderada"

    # Combinaciones imposibles
    if not errors:
        _cross_validate(values, warnings, errors)

    return values, errors, warnings


def validate_credentials(username: Any, password: Any, *, for_register: bool = False) -> dict:
    """
    Validación de credenciales compartida por las interfaces.

    Retorna {"ok": bool, "username": str, "password": str, "error": str|None}
    """
    user = sanitize_single_line(username, 32)
    pwd = "" if password is None else str(password)

    if not user:
        return {"ok": False, "username": user, "password": pwd,
                "error": "Ingresa tu nombre de usuario."}
    if for_register:
        if len(user) < 3:
            return {"ok": False, "username": user, "password": pwd,
                    "error": "El nombre de usuario debe tener al menos 3 caracteres."}
        if len(pwd) < 8:
            return {"ok": False, "username": user, "password": pwd,
                    "error": "La contraseña debe tener al menos 8 caracteres."}
        if len(pwd) > 128:
            return {"ok": False, "username": user, "password": pwd,
                    "error": "La contraseña no puede superar 128 caracteres."}
        if pwd.lower() == user.lower():
            return {"ok": False, "username": user, "password": pwd,
                    "error": "La contraseña no puede ser igual al nombre de usuario."}
    else:
        if not pwd:
            return {"ok": False, "username": user, "password": pwd,
                    "error": "Ingresa tu contraseña."}
    return {"ok": True, "username": user, "password": pwd, "error": None}
