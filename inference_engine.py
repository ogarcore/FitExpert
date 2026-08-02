"""
inference_engine.py
===================
Motor de Inferencia del Sistema Experto.

Implementa encadenamiento hacia adelante (forward chaining):
  1. Ejecuta los cálculos sobre el perfil del usuario.
  2. Evalúa cada regla de la base de conocimiento.
  3. Registra conclusiones y explicaciones de las reglas activadas.
  4. Almacena los resultados en el UserProfile.
"""

from user_profile import UserProfile
from knowledge_base import RULES
from calculations import run_calculations


# ──────────────────────────────────────────────
#  Motor de Inferencia
# ──────────────────────────────────────────────

class InferenceEngine:
    """
    Motor de inferencia por encadenamiento hacia adelante.

    Proceso:
    --------
    1. Recibe un UserProfile con datos del usuario.
    2. Ejecuta cálculos (IMC, TMB, TDEE, calorías objetivo).
    3. Evalúa TODAS las reglas de la base de conocimiento.
    4. Para cada regla cuya condición sea verdadera (FIRE),
       registra la conclusión y la explicación en el perfil.
    5. Devuelve el perfil actualizado.
    """

    def __init__(self):
        self.rules = RULES
        self.fired_rules: list[str] = []    # IDs de reglas activadas
        self.skipped_rules: list[str] = []  # IDs de reglas NO activadas

    # ── Método principal ──────────────────────────────────────────────────

    def run(self, profile: UserProfile) -> UserProfile:
        """
        Ejecuta el ciclo de inferencia completo.

        Retorna el UserProfile enriquecido con conclusiones y explicaciones.
        """
        # Paso 1 — Calcular métricas
        run_calculations(profile)

        # Paso 2 — Construir hechos (facts) como snapshot del perfil
        profile.facts = self._build_facts(profile)

        # Paso 3 — Evaluar reglas (forward chaining)
        self.fired_rules.clear()
        self.skipped_rules.clear()

        for rule in self.rules:
            try:
                if rule.condition(profile):
                    # La regla se dispara (FIRE)
                    profile.conclusions.append({
                        "id":          rule.id,
                        "description": rule.description,
                        "conclusion":  rule.conclusion,
                        "category":    rule.category,
                    })
                    profile.explanations.append({
                        "id":          rule.id,
                        "explanation": rule.explanation,
                    })
                    self.fired_rules.append(rule.id)
                else:
                    self.skipped_rules.append(rule.id)
            except Exception:
                # Regla no puede evaluarse con datos incompletos — se omite
                self.skipped_rules.append(rule.id)

        return profile

    # ── Helpers ───────────────────────────────────────────────────────────

    def _build_facts(self, profile: UserProfile) -> dict:
        """
        Construye el diccionario de hechos en formato Objeto-Atributo-Valor.
        """
        return {
            "Usuario": {
                "Nombre":            profile.name,
                "Edad":              profile.age,
                "Sexo":              profile.sex,
                "Peso (kg)":         profile.weight,
                "Altura (cm)":       profile.height,
            },
            "Evaluación": {
                "IMC":               profile.imc,
                "Categoría IMC":     profile.imc_category,
                "TMB (kcal/día)":    profile.tmb,
                "TDEE (kcal/día)":   profile.tdee,
                "Objetivo kcal/día": profile.target_calories,
            },
            "Objetivos": {
                "Meta corporal":     profile.objective,
                "Nivel actividad":   profile.activity_level,
                "Experiencia":       profile.experience,
                "Lugar entreno":     profile.training_place,
            },
        }

    def summary(self) -> dict:
        """Retorna un resumen del ciclo de inferencia."""
        return {
            "total_rules":   len(self.rules),
            "fired":         len(self.fired_rules),
            "skipped":       len(self.skipped_rules),
            "fired_ids":     self.fired_rules,
        }
