"""
user_profile.py
===============
Modelo de datos central (Blackboard) del Sistema Experto.

Representa el perfil de un usuario mediante una dataclass tipada y define los
dominios cerrados de valores permitidos (Objeto-Atributo-Valor).

Se mantienen TODOS los campos y claves históricas para no romper:
  - sesiones persistidas en usuarios.json
  - las tres interfaces (CLI, Streamlit, Escritorio)
  - el PDF exportado

Campos nuevos (v3):
  - intolerances / preferences      → distinción alergia vs intolerancia vs preferencia
  - injury_severity                 → leve | moderada | aguda (activa derivación profesional)
  - balance_issues                  → problemas de equilibrio / caídas (adultos mayores)
  - red_flags                       → síntomas de alarma declarados (fuerza derivación)
  - notes                           → observaciones libres del usuario
"""

from dataclasses import dataclass, field
from datetime import datetime


# ──────────────────────────────────────────────
#  Constantes del dominio
# ──────────────────────────────────────────────

OBJECTIVES = {
    "1": "perdida_grasa",
    "2": "aumento_muscular",
    "3": "definicion",
    "4": "recomposicion",
    "5": "mantenimiento",
}

OBJECTIVE_LABELS = {
    "perdida_grasa":    "Pérdida de grasa",
    "aumento_muscular": "Aumento de masa muscular",
    "definicion":       "Definición muscular",
    "recomposicion":    "Recomposición corporal",
    "mantenimiento":    "Mantenimiento de peso saludable",
}

# Objetivos que implican déficit calórico (se restringen en menores y bajo peso)
OBJECTIVES_WITH_DEFICIT = ("perdida_grasa", "definicion")

ACTIVITY_LEVELS = {
    "1": "sedentario",
    "2": "ligero",
    "3": "moderado",
    "4": "activo",
    "5": "muy_activo",
}

ACTIVITY_LABELS = {
    "sedentario":  "Sedentario (sin ejercicio)",
    "ligero":      "Ligero (1–2 días/semana)",
    "moderado":    "Moderado (3–5 días/semana)",
    "activo":      "Activo (6–7 días/semana)",
    "muy_activo":  "Muy activo (2 veces/día)",
}

EXPERIENCE_LEVELS = {
    "1": "principiante",
    "2": "intermedio",
    "3": "avanzado",
}

EXPERIENCE_LABELS = {
    "principiante": "Principiante (menos de 6 meses)",
    "intermedio":   "Intermedio (6 meses – 2 años)",
    "avanzado":     "Avanzado (más de 2 años)",
}

TRAINING_PLACES = {
    "1": "casa",
    "2": "gimnasio",
}

TRAINING_PLACE_LABELS = {
    "casa":     "Entrenamiento en casa",
    "gimnasio": "Gimnasio",
}

SEX_OPTIONS = {
    "1": "masculino",
    "2": "femenino",
}

DIET_TYPES = {
    "omnivoro":      "Omnívoro (sin restricciones)",
    "vegetariano":   "Vegetariano (sin carne)",
    "vegano":        "Vegano (sin productos animales)",
    "pescetariano":  "Pescetariano (pescado, sin carne roja ni aves)",
}

# ── Restricciones alimentarias ──────────────────────────────────────────────
# ALERGIAS: reacción inmunológica → exclusión estricta de la familia completa
#           y de derivados; el sistema NUNCA afirma "100% seguro".
ALLERGY_OPTIONS = {
    "leche":        "Alergia a la proteína de leche",
    "gluten":       "Celiaquía / alergia al gluten",
    "huevo":        "Alergia al huevo",
    "frutos_secos": "Alergia a frutos secos (nuez, almendra, avellana, pecana…)",
    "cacahuetes":   "Alergia a cacahuetes (maní)",
    "soja":         "Alergia a la soja",
    "pescado":      "Alergia al pescado",
    "mariscos":     "Alergia a crustáceos y moluscos",
    "sesamo":       "Alergia al sésamo",
}

# INTOLERANCIAS: intolerancia digestiva → se evitan las fuentes principales,
#                pero los derivados proteicos pueden tolerarse (p.ej. queso curado
#                sin lactosa). Nunca se equipara a alergia.
INTOLERANCE_OPTIONS = {
    "lactosa":            "Intolerancia a la lactosa",
    "fructosa":           "Intolerancia a la fructosa",
    "gluten_no_celiaca":  "Sensibilidad al gluten no celíaca",
}

# PREFERENCIAS: elección voluntaria → filtrado suave con alternativas.
PREFERENCE_OPTIONS = {
    "bajo_en_sal":         "Bajo en sal",
    "sin_azucar_anadido":  "Sin azúcar añadido",
    "alta_proteina":       "Rico en proteína",
    "economica":           "Económica / bajo costo",
    "rapida":              "Preparación rápida (< 20 min)",
}

# Mapeo de claves históricas (v1/v2) → esquema actual
LEGACY_ALLERGY_MAP = {
    "lactosa": ("intolerances", "lactosa"),
    "nueces":  ("allergies", "frutos_secos"),
    "soya":    ("allergies", "soja"),
    "huevo":   ("allergies", "huevo"),
    "gluten":  ("allergies", "gluten"),
}

INJURY_OPTIONS = {
    "lumbar":         "Zona lumbar (espalda baja)",
    "cervical":       "Cuello / cervical",
    "rodilla":        "Rodilla",
    "hombro":         "Hombro",
    "codo":           "Codo",
    "muneca":         "Muñeca",
    "tobillo":        "Tobillo",
    "cadera":         "Cadera",
    "dolor_general":  "Dolor articular generalizado",
    "movilidad":      "Movilidad reducida",
}

INJURY_SEVERITY_OPTIONS = {
    "ninguna": "Sin molestias",
    "leve":    "Molestia leve (no duele en reposo)",
    "moderada": "Molestia frecuente al entrenar",
    "aguda":   "Dolor agudo actual / lesión en curso",
}

# Lesiones cuyo tratamiento requiere evaluación profesional (fuerza derivación)
INJURY_RED_FLAGS = {
    "dolor_toracico":        "Dolor o presión en el pecho al esfuerzo",
    "mareo_desmayo":         "Mareos o pérdida de conciencia al esfuerzo",
    "falta_aire_reposo":     "Falta de aire en reposo",
    "dolor_agudo_articular": "Dolor articular intenso e hinchazón sin causa aparente",
    "debilidad_progresiva":  "Debilidad progresiva o pérdida de sensibilidad",
}

EQUIPMENT_OPTIONS = {
    "mancuernas":       "Mancuernas",
    "bandas_elasticas": "Bandas elásticas",
    "barra_dominadas":  "Barra de dominadas",
    "kettlebell":       "Kettlebell",
    "solo_peso_corporal": "Solo peso corporal",
}

# ── Grupos de edad (franjas usadas por la base de conocimiento) ─────────────
# Referencias: OMS (adolescencia 10–19 años), clasificación de adultez de la
# OMS/EPS para América Latina (adulto mayor desde los 60 años).
AGE_GROUPS = {
    "infantil":            (10, 12),
    "adolescente":         (13, 17),
    "adulto_joven":        (18, 29),
    "adulto":              (30, 59),
    "adulto_mayor":        (60, 74),
    "adulto_mayor_avanzado": (75, 120),
}

AGE_GROUP_LABELS = {
    "infantil":              "Infancia (10–12 años)",
    "adolescente":           "Adolescencia (13–17 años)",
    "adulto_joven":          "Adulto joven (18–29 años)",
    "adulto":                "Adulto (30–59 años)",
    "adulto_mayor":          "Adulto mayor (60–74 años)",
    "adulto_mayor_avanzado": "Adulto mayor de edad avanzada (75+ años)",
}


def age_group_for(age: int) -> str:
    """Devuelve la franja de edad canónica para una edad dada."""
    for key, (lo, hi) in AGE_GROUPS.items():
        if lo <= age <= hi:
            return key
    if age < 10:
        return "infantil"
    return "adulto_mayor_avanzado"


def normalize_profile_data(data: dict) -> dict:
    """
    Normaliza una sesión persistida (v1/v2) al esquema actual.

    - Migra claves históricas de alergias ("lactosa" → intolerancia, etc.)
    - Rellena campos nuevos con valores seguros por defecto.
    - Nunca lanza excepción: ante datos corruptos devuelve valores seguros.
    """
    if not isinstance(data, dict):
        return {}

    out = dict(data)

    allergies = out.get("allergies") or []
    intolerances = list(out.get("intolerances") or [])
    preferences = list(out.get("preferences") or [])

    if isinstance(allergies, list):
        migrated = []
        for item in allergies:
            if not isinstance(item, str):
                continue
            target = LEGACY_ALLERGY_MAP.get(item)
            if target:
                bucket, key = target
                if bucket == "intolerances":
                    if key not in intolerances:
                        intolerances.append(key)
                else:
                    if key not in migrated:
                        migrated.append(key)
            elif item in ALLERGY_OPTIONS:
                migrated.append(item)
            # claves desconocidas se descartan silenciosamente (datos corruptos)
        allergies = migrated

    out["allergies"] = allergies
    out["intolerances"] = [i for i in intolerances if i in INTOLERANCE_OPTIONS]
    out["preferences"] = [p for p in preferences if p in PREFERENCE_OPTIONS]

    injuries = out.get("injuries") or []
    out["injuries"] = [i for i in injuries if isinstance(i, str) and i in INJURY_OPTIONS] \
        if isinstance(injuries, list) else []

    equipment = out.get("equipment") or []
    if isinstance(equipment, list):
        fixed = []
        for e in equipment:
            if e == "bandas_elásticas":        # corrección de clave histórica mal escrita
                e = "bandas_elasticas"
            if e in EQUIPMENT_OPTIONS:
                fixed.append(e)
        out["equipment"] = fixed
    else:
        out["equipment"] = []

    if out.get("injury_severity") not in INJURY_SEVERITY_OPTIONS:
        out["injury_severity"] = "ninguna" if not out["injuries"] else "moderada"

    flags = out.get("red_flags") or []
    out["red_flags"] = [f for f in flags if isinstance(f, str) and f in INJURY_RED_FLAGS] \
        if isinstance(flags, list) else []
    out["balance_issues"] = bool(out.get("balance_issues", False))
    out["notes"] = str(out.get("notes") or "")[:300]

    for list_field, domain in (("allergies", ALLERGY_OPTIONS),
                               ("intolerances", INTOLERANCE_OPTIONS),
                               ("preferences", PREFERENCE_OPTIONS)):
        value = out.get(list_field)
        if not isinstance(value, list):
            out[list_field] = []

    return out


# ──────────────────────────────────────────────
#  Dataclass principal
# ──────────────────────────────────────────────

@dataclass
class UserProfile:
    """Almacena todos los datos recopilados durante la evaluación inicial."""

    # Identificación
    user_id: str = ""

    # Datos personales
    name: str = ""
    age: int = 0
    sex: str = ""                   # "masculino" | "femenino"
    weight: float = 0.0             # kg
    height: float = 0.0             # cm

    # Métricas avanzadas
    body_fat_pct: float = 0.0       # % de grasa corporal estimado (opcional)

    # Parámetros de entrenamiento
    activity_level: str = ""        # sedentario | ligero | moderado | activo | muy_activo
    objective: str = ""             # perdida_grasa | aumento_muscular | ...
    experience: str = ""            # principiante | intermedio | avanzado
    training_place: str = ""        # casa | gimnasio
    equipment: list = field(default_factory=list)   # mancuernas, bandas_elasticas, etc.

    # Salud y lesiones
    injuries: list = field(default_factory=list)    # claves de INJURY_OPTIONS
    injury_severity: str = "ninguna"                # ninguna | leve | moderada | aguda
    balance_issues: bool = False                    # historial de caídas / equilibrio
    red_flags: list = field(default_factory=list)   # claves de INJURY_RED_FLAGS

    # Nutrición y estilo de vida
    diet_type: str = "omnivoro"                     # omnivoro | vegetariano | vegano | pescetariano
    allergies: list = field(default_factory=list)   # claves de ALLERGY_OPTIONS
    intolerances: list = field(default_factory=list)  # claves de INTOLERANCE_OPTIONS
    preferences: list = field(default_factory=list)   # claves de PREFERENCE_OPTIONS
    meal_frequency: int = 3                         # 3, 4 o 5 comidas al día
    notes: str = ""                                 # observaciones libres (<= 300)

    # Campos calculados (se completan en calculations / inference_engine)
    imc: float = 0.0
    tmb: float = 0.0
    tdee: float = 0.0
    target_calories: float = 0.0
    imc_category: str = ""
    hidratacion_ml: float = 0.0                     # hidratación sugerida (ml/día)
    caloric_adjustment: float = 0.0                 # ajuste efectivo aplicado
    adjustment_capped: bool = False                 # ¿el ajuste fue limitado por seguridad?
    adjustment_reason: str = ""                     # explicación del límite aplicado

    # Resultados del motor de inferencia
    facts: dict = field(default_factory=dict)
    conclusions: list = field(default_factory=list)
    explanations: list = field(default_factory=list)
    suppressed: list = field(default_factory=list)         # reglas excluidas/reemplazadas + motivo
    engine_errors: list = field(default_factory=list)   # reglas que fallaron (auditoría)

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))

    # ── helpers de dominio ─────────────────────

    def objective_label(self) -> str:
        return OBJECTIVE_LABELS.get(self.objective, self.objective)

    def activity_label(self) -> str:
        return ACTIVITY_LABELS.get(self.activity_level, self.activity_level)

    def experience_label(self) -> str:
        return EXPERIENCE_LABELS.get(self.experience, self.experience)

    def diet_label(self) -> str:
        return DIET_TYPES.get(self.diet_type, self.diet_type)

    def age_group(self) -> str:
        """Franja de edad canónica (ver AGE_GROUPS)."""
        return age_group_for(self.age)

    def age_group_label(self) -> str:
        return AGE_GROUP_LABELS.get(self.age_group(), "")

    def is_minor(self) -> bool:
        """Menor de edad según el rango operativo del sistema (<18)."""
        return 0 <= self.age < 18

    def is_senior(self) -> bool:
        """Adulto mayor (≥60 años)."""
        return self.age >= 60

    def has_injury(self, injury: str) -> bool:
        return injury in self.injuries

    def has_allergy(self, allergen: str) -> bool:
        return allergen in self.allergies

    def has_intolerance(self, item: str) -> bool:
        return item in self.intolerances

    def has_preference(self, item: str) -> bool:
        return item in self.preferences

    def has_equipment(self, item: str) -> bool:
        return item in self.equipment

    def to_dict(self) -> dict:
        """Serializa el perfil a un diccionario (para persistencia JSON)."""
        return {
            "user_id": self.user_id,
            "name": self.name,
            "age": self.age,
            "sex": self.sex,
            "weight": round(float(self.weight), 2) if self.weight else self.weight,
            "height": round(float(self.height), 2) if self.height else self.height,
            "body_fat_pct": self.body_fat_pct,
            "activity_level": self.activity_level,
            "objective": self.objective,
            "experience": self.experience,
            "training_place": self.training_place,
            "equipment": self.equipment,
            "injuries": self.injuries,
            "injury_severity": self.injury_severity,
            "balance_issues": self.balance_issues,
            "red_flags": self.red_flags,
            "diet_type": self.diet_type,
            "allergies": self.allergies,
            "intolerances": self.intolerances,
            "preferences": self.preferences,
            "meal_frequency": self.meal_frequency,
            "notes": self.notes,
            "imc": round(self.imc, 2),
            "tmb": round(self.tmb, 2),
            "tdee": round(self.tdee, 2),
            "target_calories": round(self.target_calories, 2),
            "imc_category": self.imc_category,
            "hidratacion_ml": round(self.hidratacion_ml),
            "caloric_adjustment": round(self.caloric_adjustment),
            "adjustment_capped": self.adjustment_capped,
            "adjustment_reason": self.adjustment_reason,
            "conclusions": self.conclusions,
            "explanations": self.explanations,
            "suppressed": self.suppressed,
            "engine_errors": self.engine_errors,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        """
        Reconstruye un perfil desde datos persistidos tolerando campos
        ausentes, con tipos incorrectos o de versiones anteriores.
        """
        data = normalize_profile_data(data or {})
        campos = cls.__dataclass_fields__
        kwargs = {}

        def _num(key, cast, default=0):
            val = data.get(key, default)
            try:
                val = cast(val)
                if val != val or val in (float("inf"), float("-inf")):  # NaN / Inf
                    return default
                return val
            except (TypeError, ValueError):
                return default

        kwargs["user_id"] = str(data.get("user_id") or "")
        kwargs["name"] = str(data.get("name") or "")[:60]
        kwargs["age"] = _num("age", int)
        # Acepta tanto el valor canónico ("femenino") como la clave numérica
        # legada persistida por versiones anteriores ("1"/"2").
        _raw_sex = data.get("sex")
        kwargs["sex"] = SEX_OPTIONS.get(_raw_sex, _raw_sex) \
            if _raw_sex in SEX_OPTIONS or _raw_sex in SEX_OPTIONS.values() else ""
        kwargs["weight"] = _num("weight", float)
        kwargs["height"] = _num("height", float)
        kwargs["body_fat_pct"] = _num("body_fat_pct", float)

        for key, domain in (("activity_level", ACTIVITY_LABELS),
                            ("objective", OBJECTIVE_LABELS),
                            ("experience", EXPERIENCE_LABELS),
                            ("training_place", TRAINING_PLACE_LABELS),
                            ("diet_type", DIET_TYPES),
                            ("injury_severity", INJURY_SEVERITY_OPTIONS)):
            val = data.get(key)
            kwargs[key] = val if val in domain else ("" if key != "injury_severity" else "ninguna")
        if kwargs["diet_type"] == "":
            kwargs["diet_type"] = "omnivoro"

        kwargs["meal_frequency"] = _num("meal_frequency", int, 3)

        for key in ("equipment", "injuries", "allergies", "intolerances",
                    "preferences", "red_flags", "conclusions", "explanations",
                    "suppressed", "engine_errors"):
            val = data.get(key)
            kwargs[key] = list(val) if isinstance(val, list) else []

        kwargs["notes"] = str(data.get("notes") or "")[:300]
        kwargs["balance_issues"] = bool(data.get("balance_issues", False))

        # Métricas calculadas persistidas
        kwargs["imc"] = _num("imc", float)
        kwargs["tmb"] = _num("tmb", float)
        kwargs["tdee"] = _num("tdee", float)
        kwargs["target_calories"] = _num("target_calories", float)
        kwargs["hidratacion_ml"] = _num("hidratacion_ml", float)
        kwargs["caloric_adjustment"] = _num("caloric_adjustment", float)
        kwargs["imc_category"] = str(data.get("imc_category") or "")
        kwargs["adjustment_capped"] = bool(data.get("adjustment_capped", False))
        kwargs["adjustment_reason"] = str(data.get("adjustment_reason") or "")
        kwargs["created_at"] = str(data.get("created_at") or
                                   datetime.now().strftime("%Y-%m-%d %H:%M"))

        return cls(**{k: v for k, v in kwargs.items() if k in campos})
