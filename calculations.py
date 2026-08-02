"""
calculations.py
===============
Funciones matemáticas del Sistema Experto:
  - IMC (Índice de Masa Corporal)
  - TMB (Tasa Metabólica Basal) — fórmula de Harris-Benedict revisada
  - TDEE (Total Daily Energy Expenditure) — gasto energético diario
  - Calorías objetivo según meta corporal
  - Distribución de macronutrientes
"""

from user_profile import UserProfile

# ──────────────────────────────────────────────
#  Factores de actividad (fórmula de Harris-Benedict)
# ──────────────────────────────────────────────

ACTIVITY_FACTORS = {
    "sedentario":  1.2,
    "ligero":      1.375,
    "moderado":    1.55,
    "activo":      1.725,
    "muy_activo":  1.9,
}

# Ajuste calórico por objetivo
CALORIC_ADJUSTMENTS = {
    "perdida_grasa":    -500,   # déficit moderado
    "aumento_muscular": +400,   # superávit controlado
    "definicion":       -250,   # déficit leve
    "recomposicion":      0,    # igual al TDEE
    "mantenimiento":      0,    # igual al TDEE
}

# Clasificación IMC (OMS)
IMC_CATEGORIES = [
    (0,    18.5, "Bajo peso"),
    (18.5, 24.9, "Peso normal"),
    (24.9, 29.9, "Sobrepeso"),
    (29.9, 34.9, "Obesidad grado I"),
    (34.9, 39.9, "Obesidad grado II"),
    (39.9, 999,  "Obesidad grado III"),
]


# ──────────────────────────────────────────────
#  Funciones de cálculo
# ──────────────────────────────────────────────

def calcular_imc(peso_kg: float, altura_cm: float) -> tuple[float, str]:
    """
    Calcula el IMC y devuelve (valor, categoría).

    IMC = peso (kg) / altura² (m)
    """
    altura_m = altura_cm / 100
    imc = peso_kg / (altura_m ** 2)
    categoria = next(
        (cat for lo, hi, cat in IMC_CATEGORIES if lo <= imc < hi),
        "Desconocido"
    )
    return round(imc, 2), categoria


def calcular_tmb(peso_kg: float, altura_cm: float, edad: int, sexo: str) -> float:
    """
    Tasa Metabólica Basal — Harris-Benedict revisada (Mifflin-St Jeor).

    Hombres: TMB = 10×peso + 6.25×altura − 5×edad + 5
    Mujeres: TMB = 10×peso + 6.25×altura − 5×edad − 161
    """
    base = 10 * peso_kg + 6.25 * altura_cm - 5 * edad
    if sexo == "masculino":
        return round(base + 5, 2)
    else:
        return round(base - 161, 2)


def calcular_tdee(tmb: float, nivel_actividad: str) -> float:
    """
    Gasto Energético Diario Total.

    TDEE = TMB × factor_actividad
    """
    factor = ACTIVITY_FACTORS.get(nivel_actividad, 1.2)
    return round(tmb * factor, 2)


def calcular_calorias_objetivo(tdee: float, objetivo: str) -> float:
    """
    Ajusta el TDEE según el objetivo del usuario.
    """
    ajuste = CALORIC_ADJUSTMENTS.get(objetivo, 0)
    return round(tdee + ajuste, 2)


def calcular_macronutrientes(calorias: float, objetivo: str) -> dict:
    """
    Distribuye las calorías en macronutrientes según el objetivo.

    Retorna un dict con gramos de proteína, carbohidratos y grasas.

    Distribuciones recomendadas (% kcal):
      - perdida_grasa:    P 35% | C 40% | G 25%
      - aumento_muscular: P 30% | C 50% | G 20%
      - definicion:       P 40% | C 35% | G 25%
      - recomposicion:    P 35% | C 40% | G 25%
      - mantenimiento:    P 25% | C 50% | G 25%
    """
    distribuciones = {
        "perdida_grasa":    (0.35, 0.40, 0.25),
        "aumento_muscular": (0.30, 0.50, 0.20),
        "definicion":       (0.40, 0.35, 0.25),
        "recomposicion":    (0.35, 0.40, 0.25),
        "mantenimiento":    (0.25, 0.50, 0.25),
    }
    p_pct, c_pct, g_pct = distribuciones.get(objetivo, (0.30, 0.45, 0.25))

    # 1 g proteína = 4 kcal | 1 g carbohidrato = 4 kcal | 1 g grasa = 9 kcal
    proteinas   = round((calorias * p_pct) / 4, 1)
    carbos      = round((calorias * c_pct) / 4, 1)
    grasas      = round((calorias * g_pct) / 9, 1)

    return {
        "proteinas":     proteinas,
        "carbohidratos": carbos,
        "grasas":        grasas,
        "p_pct":         int(p_pct * 100),
        "c_pct":         int(c_pct * 100),
        "g_pct":         int(g_pct * 100),
    }


def run_calculations(profile: UserProfile) -> None:
    """
    Ejecuta todos los cálculos y los almacena directamente en el perfil.
    """
    profile.imc, profile.imc_category = calcular_imc(profile.weight, profile.height)
    profile.tmb = calcular_tmb(profile.weight, profile.height, profile.age, profile.sex)
    profile.tdee = calcular_tdee(profile.tmb, profile.activity_level)
    profile.target_calories = calcular_calorias_objetivo(profile.tdee, profile.objective)
