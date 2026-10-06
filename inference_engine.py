"""
inference_engine.py
===================
Motor de Inferencia del Sistema Experto FitExpert.

Implementa encadenamiento hacia adelante (forward chaining) con
resolución determinista de conflictos:

  1. Ejecuta los cálculos sobre el perfil (IMC, TMB, TDEE, meta).
  2. Construye los hechos (OAV) del perfil.
  3. Evalúa TODAS las reglas de la base de conocimiento.
  4. Resuelve conflictos entre reglas activadas aplicando la jerarquía
     de seguridad documentada en knowledge_base.TIER_ORDER:

         SEGURIDAD > CONTRAINDICACIONES > EDAD > CONDICIÓN FÍSICA
                   > OBJETIVO > PREFERENCIAS > SEGUIMIENTO

     Dentro del mismo tier gana la mayor `priority`; si persiste el
     empate, el id alfabéticamente menor (resultado siempre determinista).
     Una regla puede declarar `conflicts` (ids o globs como "TRAIN-*"):
     si gana, la regla en conflicto queda SUPRIMIDA y el motivo se
     registra en `profile.suppressed` (visible para el usuario).
  5. Registra conclusiones, explicaciones (con qué dato la activó) y
     cualquier error de evaluación en `profile.engine_errors`
     (nunca se omite una regla en silencio).

Contrato consumido por las interfaces (gui.py, ui.py, app_desktop.pyw):
  - profile.conclusions: {id, description, conclusion, category, ...}
  - profile.explanations: {id, explanation, ...}
  - profile.facts: {objeto: {atributo: valor}}
"""

import fnmatch

from user_profile import UserProfile
from knowledge_base import RULES, TIER_LABELS, tier_rank
from calculations import run_calculations


# ──────────────────────────────────────────────
#  Motor de Inferencia
# ──────────────────────────────────────────────

class InferenceEngine:
    """
    Motor de inferencia por encadenamiento hacia adelante con
    jerarquía de seguridad en la resolución de conflictos.
    """

    def __init__(self):
        self.rules = RULES
        self.fired_rules: list[str] = []      # reglas activadas (y no suprimidas)
        self.skipped_rules: list[str] = []    # reglas cuya condición fue falsa
        self.suppressed_rules: list[dict] = []  # {id, suppressed_by, reason}
        self.error_rules: list[dict] = []     # {id, error}

    # ── Método principal ──────────────────────────────────────────────────

    def run(self, profile: UserProfile) -> UserProfile:
        """
        Ejecuta el ciclo de inferencia completo y retorna el perfil
        enriquecido con conclusiones, explicaciones y trazabilidad.
        """
        # Paso 1 — Calcular métricas
        run_calculations(profile)

        # Paso 2 — Construir hechos (facts) como snapshot del perfil
        profile.facts = self._build_facts(profile)

        # Paso 3 — Evaluar todas las reglas (forward chaining)
        self.fired_rules.clear()
        self.skipped_rules.clear()
        self.suppressed_rules.clear()
        self.error_rules.clear()

        profile.conclusions = []
        profile.explanations = []
        profile.suppressed = []
        profile.engine_errors = []

        fired = []   # list[Rule] en orden de activación
        for rule in self.rules:
            try:
                if rule.condition(profile):
                    fired.append(rule)
                    self.fired_rules.append(rule.id)
                else:
                    self.skipped_rules.append(rule.id)
            except Exception as exc:
                # Nunca en silencio: se registra en el perfil para auditoría
                error = {"id": rule.id, "error": f"{type(exc).__name__}: {exc}"}
                self.error_rules.append(error)
                profile.engine_errors.append(error)
                self.skipped_rules.append(rule.id)

        # Paso 4 — Resolver conflictos (jerarquía de seguridad)
        winners, suppressed = self._resolve_conflicts(fired)

        # Paso 5 — Registrar conclusiones + explicaciones
        for rule in winners:
            refs = (list(rule.references)
                    if isinstance(rule.references, (tuple, list))
                    else [rule.references])
            profile.conclusions.append({
                "id":          rule.id,
                "description": rule.description,
                "conclusion":  rule.conclusion,
                "category":    rule.category,
                "severity":    rule.severity,
                "tier":        rule.tier,
                "tier_label":  TIER_LABELS.get(rule.tier, rule.tier),
                "priority":    rule.priority,
                "action":      rule.action,
                "alternative": rule.alternative,
                "references":  refs,
                "test":        rule.test,
            })
            profile.explanations.append({
                "id":          rule.id,
                "explanation": rule.explanation,
                "test":        rule.test,
                "trigger":     self._trigger_text(rule, profile),
                "references":  refs,
                "tier_label":  TIER_LABELS.get(rule.tier, rule.tier),
            })

        for item in suppressed:
            profile.suppressed.append(item)
        self.suppressed_rules = list(suppressed)

        return profile

    # ── Resolución de conflictos ──────────────────────────────────────────

    def _resolve_conflicts(self, fired: list) -> tuple[list, list]:
        """
        Aplica la jerarquía de seguridad y los `conflicts` declarados.

        Reglas que deben suprimirse se eliminan ANTES de ordenar; el
        resultado es determinista (tier, -priority, id).
        """
        # Mapa id -> regla activada
        active = {r.id: r for r in fired}
        suppressed: list[dict] = []

        for rule in fired:
            if not rule.conflicts:
                continue
            for pattern in rule.conflicts:
                for other in fired:
                    if other.id == rule.id:
                        continue
                    if not fnmatch.fnmatchcase(other.id, pattern):
                        continue
                    # ¿Debe ganar esta regla sobre la otra?
                    if self._wins(rule, other):
                        active.pop(other.id, None)
                        if not any(s["id"] == other.id for s in suppressed):
                            suppressed.append({
                                "id":            other.id,
                                "description":   other.description,
                                "suppressed_by": rule.id,
                                "suppressed_by_description": rule.description,
                                "reason": (
                                    f"Regla «{rule.description}» (tier "
                                    f"{TIER_LABELS.get(rule.tier, rule.tier)}, "
                                    f"prioridad {rule.priority}) tiene prioridad "
                                    f"sobre esta recomendación por la jerarquía "
                                    f"SEGURIDAD > CONTRAINDICACIONES > EDAD > "
                                    f"CONDICIÓN FÍSICA > OBJETIVO > PREFERENCIAS."
                                ),
                            })

        winners = [r for r in fired if r.id in active]
        # Orden final determinista por jerarquía
        winners.sort(key=lambda r: (tier_rank(r.tier), -r.priority, r.id))
        return winners, suppressed

    @staticmethod
    def _wins(a, b) -> bool:
        """True si la regla `a` debe suprimir a `b` (jerarquía y prioridad)."""
        ra, rb = tier_rank(a.tier), tier_rank(b.tier)
        if ra != rb:
            return ra < rb
        if a.priority != b.priority:
            return a.priority > b.priority
        return a.id <= b.id  # desempate determinista

    # ── Explicabilidad ────────────────────────────────────────────────────

    def _trigger_text(self, rule, profile: UserProfile) -> str:
        """
        Devuelve un texto legible con el dato que activó la regla.
        Usa el campo `test` de la regla (condición en lenguaje humano).
        """
        if rule.test:
            return f"Se activó porque: {rule.test}."
        return f"Se activó porque su condición se cumple: {rule.description}."

    # ── Hechos OAV ────────────────────────────────────────────────────────

    def _build_facts(self, profile: UserProfile) -> dict:
        """
        Construye el diccionario de hechos en formato Objeto-Atributo-Val
        (snapshot completo para trazabilidad y exportación).
        """
        facts = {
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
                "Ajuste calórico":   profile.caloric_adjustment,
                "Motivo ajuste":     profile.adjustment_reason,
                "Hidratación (ml)":  profile.hidratacion_ml,
            },
            "Objetivos": {
                "Meta corporal":     profile.objective,
                "Nivel actividad":   profile.activity_level,
                "Experiencia":       profile.experience,
                "Lugar entreno":     profile.training_place,
            },
        }
        facts["Salud"] = {
            "Lesiones":        ", ".join(profile.injuries) or "Ninguna",
            "Severidad":       profile.injury_severity or "Sin declarar",
            "Equilibrio":      "Problemas declarados" if profile.balance_issues else "Sin problemas",
            "Alertas rojas":   ", ".join(profile.red_flags) or "Ninguna",
            "Grupo de edad":   profile.age_group(),
        }
        facts["Nutrición"] = {
            "Tipo de dieta":   profile.diet_type or "Sin declarar",
            "Alergias":        ", ".join(profile.allergies) or "Ninguna",
            "Intolerancias":   ", ".join(profile.intolerances) or "Ninguna",
            "Preferencias":    ", ".join(profile.preferences) or "Ninguna",
            "Comidas/día":     profile.meal_frequency,
        }
        if profile.equipment:
            facts["Equipo"] = {"Disponible": ", ".join(profile.equipment)}
        return facts

    # ── Resumen ───────────────────────────────────────────────────────────

    def summary(self) -> dict:
        """Retorna un resumen del ciclo de inferencia (auditoría)."""
        return {
            "total_rules":  len(self.rules),
            "fired":        len(self.fired_rules),
            "skipped":      len(self.skipped_rules),
            "suppressed":   len(self.suppressed_rules),
            "errors":       len(self.error_rules),
            "fired_ids":    self.fired_rules,
            "suppressed_detail": self.suppressed_rules,
            "errors_detail":     self.error_rules,
        }
