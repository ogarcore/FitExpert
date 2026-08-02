"""
user_profile.py
===============
Modelo de datos que representa el perfil de un usuario en el Sistema Experto.
Usa dataclasses para una estructura limpia y tipada.
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

TRAINING_PLACES = {
    "1": "casa",
    "2": "gimnasio",
}

SEX_OPTIONS = {
    "1": "masculino",
    "2": "femenino",
}

DIET_TYPES = {
    "omnivoro":       "Omnívoro (sin restricciones)",
    "vegetariano":    "Vegetariano (sin carne)",
    "vegano":         "Vegano (sin productos animales)",
    "pescetariano":   "Pescetariano (pescado pero sin carne roja/pollo)",
}

ALLERGY_OPTIONS = [
    "lactosa",
    "gluten",
    "nueces",
    "soya",
    "huevo",
]

INJURY_OPTIONS = [
    "rodilla",
    "lumbar",
    "hombro",
]

EQUIPMENT_OPTIONS = [
    "mancuernas",
    "bandas_elasticas",
    "barra_dominadas",
    "kettlebell",
    "solo_peso_corporal",
]


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
    injuries: list = field(default_factory=list)    # rodilla, lumbar, hombro

    # Nutrición y estilo de vida
    diet_type: str = "omnivoro"                     # omnivoro | vegetariano | vegano | pescetariano
    allergies: list = field(default_factory=list)   # lactosa, gluten, etc.
    meal_frequency: int = 3                          # 3, 4 o 5 comidas al día

    # Campos calculados (se completan en inference_engine)
    imc: float = 0.0
    tmb: float = 0.0
    tdee: float = 0.0
    target_calories: float = 0.0
    imc_category: str = ""

    # Resultados del motor de inferencia
    facts: dict = field(default_factory=dict)
    conclusions: list = field(default_factory=list)
    explanations: list = field(default_factory=list)

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))

    # ── helpers ──────────────────────────────

    def objective_label(self) -> str:
        return OBJECTIVE_LABELS.get(self.objective, self.objective)

    def activity_label(self) -> str:
        return ACTIVITY_LABELS.get(self.activity_level, self.activity_level)

    def experience_label(self) -> str:
        return EXPERIENCE_LEVELS.get(
            next((k for k, v in EXPERIENCE_LEVELS.items() if v == self.experience), ""),
            self.experience,
        ).capitalize()

    def has_injury(self, injury: str) -> bool:
        return injury in self.injuries

    def has_allergy(self, allergen: str) -> bool:
        return allergen in self.allergies

    def has_equipment(self, item: str) -> bool:
        return item in self.equipment

    def to_dict(self) -> dict:
        """Serializa el perfil a un diccionario (para persistencia JSON)."""
        return {
            "user_id": self.user_id,
            "name": self.name,
            "age": self.age,
            "sex": self.sex,
            "weight": self.weight,
            "height": self.height,
            "body_fat_pct": self.body_fat_pct,
            "activity_level": self.activity_level,
            "objective": self.objective,
            "experience": self.experience,
            "training_place": self.training_place,
            "equipment": self.equipment,
            "injuries": self.injuries,
            "diet_type": self.diet_type,
            "allergies": self.allergies,
            "meal_frequency": self.meal_frequency,
            "imc": round(self.imc, 2),
            "tmb": round(self.tmb, 2),
            "tdee": round(self.tdee, 2),
            "target_calories": round(self.target_calories, 2),
            "imc_category": self.imc_category,
            "conclusions": self.conclusions,
            "created_at": self.created_at,
        }
