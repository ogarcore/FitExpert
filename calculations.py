"""
calculations.py
===============
Funciones matemáticas del Sistema Experto FitExpert.

Fórmulas y políticas:
  - IMC (Índice de Masa Corporal) — clasificación OMS 2022 con cortes
    correctos (18.5 / 25 / 30 / 35 / 40) y manejo seguro de entradas.
  - TMB — Mifflin-St Jeor (respaldo Harris-Benedict revisada).
  - TDEE — gasto energético diario total.
  - Calorías objetivo con POLÍTICAS DE SEGURIDAD:
      · nunca por debajo del gasto basal,
      · sin déficit para menores de edad ni bajo peso,
      · déficit limitado en adultos mayores (≥60),
      · ajustes en % del TDEE (no fijos ±500/400 kcal),
      · techos de superávit para ganancia de calidad.
  - Hidratación diaria, distribución de macronutrientes y pauta de
    proteína.

Referencias:
  - OMS (2022) Obesity and overweight — clasificación IMC adultos.
  - Mifflin MD et al. (1990) Am J Clin Nutr — ecuación TMB.
  - Roza AM, Shizgal HM (1984) Am J Clin Nutr — Harris-Benedict revisada.
  - ACSM Guidelines for Exercise Testing and Prescription — factores de
    actividad y rangos de composición corporal.
  - Consenso PROT-AGE (2013) JAMDA — proteína en adultos mayores.
  - AAP / OMS curvas de crecimiento — IMC infantil por percentiles.

NOTA: el IMC es una herramienta de tamizaje, NO un diagnóstico.
"""

from __future__ import annotations

import math

from user_profile import UserProfile, OBJECTIVES_WITH_DEFICIT

# ──────────────────────────────────────────────
#  Constantes
# ──────────────────────────────────────────────

ACTIVITY_FACTORS = {
    "sedentario":  1.2,
    "ligero":      1.375,
    "moderado":    1.55,
    "activo":      1.725,
    "muy_activo":  1.9,
}

# Ajuste calórico por objetivo (fracción del TDEE). Los límites de
# seguridad se aplican después en _ajustar_calorias_seguro().
CALORIC_ADJUSTMENTS_PCT = {
    "perdida_grasa":     -0.12,   # déficit moderado (12 %)
    "definicion":        -0.08,   # déficit leve (8 %)
    "aumento_muscular":   0.10,   # superávit controlado (10 %)
    "recomposicion":      0.0,
    "mantenimiento":      0.0,
}

# Compatibilidad con el contrato histórico (kcal absolutas ya NO se usan
# directamente; se aplica el % con tope y suelo).
CALORIC_ADJUSTMENTS = {
    "perdida_grasa":    -500,
    "aumento_muscular":  400,
    "definicion":       -250,
    "recomposicion":      0,
    "mantenimiento":      0,
}

# Clasificación IMC adultos (OMS 2022): cortes exactos, sin huecos.
IMC_CATEGORIES = [
    (0.0,  18.5, "Bajo peso"),
    (18.5, 25.0, "Peso normal"),
    (25.0, 30.0, "Sobrepeso"),
    (30.0, 35.0, "Obesidad grado I"),
    (35.0, 40.0, "Obesidad grado II"),
    (40.0, 999.0, "Obesidad grado III"),
]

# Límites absolutos de seguridad (kcal/día)
MIN_CALORIES_F = 1200.0
MIN_CALORIES_M = 1500.0
MAX_SURPLUS_PCT = 0.15        # superávit máximo general (15 %)
MAX_DEFICIT_PCT = 0.12        # déficit máximo general (12 %)
MAX_DEFICIT_SENIOR_PCT = 0.10  # déficit máximo en ≥60 años (10 %)
SENIOR_FLOOR_TMB = 1.2        # piso en mayores: 1.2 × TMB (consenso PROT-AGE)
AGUA_MIN_ML = 1200.0
AGUA_MAX_ML = 5000.0


# ──────────────────────────────────────────────
#  Utilidades de seguridad numérica
# ──────────────────────────────────────────────

def _safe(value, fallback: float = 0.0) -> float:
    """Convierte a float seguro: None/NaN/Inf/error → fallback."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return fallback
    if not math.isfinite(v):
        return fallback
    return v


# ──────────────────────────────────────────────
#  Cálculos básicos
# ──────────────────────────────────────────────

def calcular_imc(peso_kg: float, altura_cm: float) -> tuple[float, str]:
    """
    Calcula el IMC y devuelve (valor, categoría).

    IMC = peso (kg) / altura² (m). Entradas protegidas: con altura o
    peso no plausibles devuelve (0.0, "Sin datos") en vez de lanzar
    ZeroDivisionError o devolver NaN/Inf.
    """
    peso = _safe(peso_kg, -1.0)
    altura = _safe(altura_cm, -1.0)
    if peso <= 0 or altura <= 0:
        return 0.0, "Sin datos"
    altura_m = altura / 100.0
    imc = peso / (altura_m * altura_m)
    if not math.isfinite(imc) or imc <= 0 or imc > 300:
        return 0.0, "Sin datos"
    imc = round(imc, 2)
    categoria = next(
        (cat for lo, hi, cat in IMC_CATEGORIES if lo <= imc < hi),
        "Desconocido",
    )
    return imc, categoria


def calcular_imc_categoria(imc: float) -> str:
    """Clasificación OMS para adultos a partir de un IMC ya calculado."""
    v = _safe(imc, 0.0)
    if v <= 0:
        return "Sin datos"
    return next((cat for lo, hi, cat in IMC_CATEGORIES if lo <= v < hi),
                "Desconocido")


def calcular_tmb(peso_kg: float, altura_cm: float, edad: int, sexo: str) -> float:
    """
    Tasa Metabólica Basal — Mifflin-St Jeor.

    Hombres: TMB = 10×peso + 6.25×altura − 5×edad + 5
    Mujeres: TMB = 10×peso + 6.25×altura − 5×edad − 161

    Acepta sexo como "masculino"/"femenino" o "M"/"F". Nunca devuelve
    NaN/Inf; piso fisiológico de 800 kcal.
    """
    peso = _safe(peso_kg, 70.0)
    altura = _safe(altura_cm, 170.0)
    edad = _safe(edad, 30.0)
    base = 10.0 * peso + 6.25 * altura - 5.0 * edad
    es_hombre = str(sexo).lower() in ("masculino", "m", "hombre", "varon")
    tmb = base + 5.0 if es_hombre else base - 161.0
    if not math.isfinite(tmb):
        return 1500.0
    return round(max(tmb, 800.0), 2)


def calcular_tdee(tmb: float, nivel_actividad: str) -> float:
    """
    Gasto Energético Diario Total: TDEE = TMB × factor_actividad.
    Nivel desconocido → factor sedentario (conservador).
    """
    tmb_safe = _safe(tmb, 0.0)
    if tmb_safe <= 0:
        return 0.0
    factor = ACTIVITY_FACTORS.get((nivel_actividad or "").strip().lower(), 1.2)
    return round(tmb_safe * factor, 2)


def calcular_calorias_objetivo(perfil: UserProfile) -> float:
    """
    Calorías objetivo con políticas de seguridad (ver _ajustar_calorias_seguro).

    Devuelve las kcal/día ajustadas y deja el detalle del ajuste en el
    perfil (caloric_adjustment, adjustment_capped, adjustment_reason).
    """
    kcal, delta_kcal, capped, reason = _ajustar_calorias_seguro(perfil)
    perfil.caloric_adjustment = round(delta_kcal)
    perfil.adjustment_capped = capped
    perfil.adjustment_reason = reason
    return kcal


def _ajustar_calorias_seguro(perfil: UserProfile) -> tuple[float, float, bool, str]:
    """
    Aplica el ajuste calórico por objetivo con límites de seguridad.

    Devuelve (kcal_objetivo, delta_kcal, fue_limitado, explicación).

    Reglas:
      1. Nunca por debajo del gasto basal (TMB).
      2. Sin déficit para menores (<18) ni IMC < 18.5 (bajo peso):
         se recomienda mantenimiento/crecimiento, no restricción.
      3. Adultos mayores (≥60): déficit máximo 10 % y piso 1.2×TMB
         (prevención de sarcopenia; consenso PROT-AGE).
      4. Ajustes en % del TDEE con techo de +15 % (ganancia de calidad).
      5. Suelo absoluto: 1200 kcal (F) / 1500 kcal (M).
    """
    objetivo = (perfil.objective or "").strip().lower()
    if perfil.weight <= 0 or perfil.height <= 0:
        # Datos insuficientes: no se arriesga un valor calórico.
        return 0.0, 0.0, False, ""
    tdee = perfil.tdee or calcular_tdee(
        perfil.tmb, perfil.activity_level)
    tmb = perfil.tmb or 0.0
    if tdee <= 0:
        return 0.0, 0.0, False, ""

    delta_pct = CALORIC_ADJUSTMENTS_PCT.get(objetivo, 0.0)
    es_deficit = objetivo in OBJECTIVES_WITH_DEFICIT
    vulnerable = perfil.is_minor() or perfil.imc < 18.5
    senior = perfil.is_senior()
    capped = False
    reason = ""

    # 2. Sin déficit en población vulnerable
    if es_deficit and vulnerable:
        if perfil.is_minor():
            reason = ("No se aplica déficit calórico: en menores de edad "
                      "se prioriza el crecimiento y desarrollo (AAP/OMS).")
        else:
            reason = ("No se aplica déficit calórico: el IMC indica bajo "
                      "peso; se recomienda objetivo de mantenimiento o "
                      "ganancia de peso gradual.")
        delta_pct = 0.0
        capped = True
    elif es_deficit and senior and abs(delta_pct) > MAX_DEFICIT_SENIOR_PCT:
        delta_pct = -MAX_DEFICIT_SENIOR_PCT
        capped = True
        reason = ("Déficit limitado al 10 % del gasto diario por edad "
                  "≥60 años, para preservar masa muscular (PROT-AGE).")
    elif es_deficit and abs(delta_pct) > MAX_DEFICIT_PCT:
        delta_pct = -MAX_DEFICIT_PCT

    kcal = tdee * (1.0 + delta_pct)

    # 3. Suelos de seguridad
    suelo_absoluto = MIN_CALORIES_F if str(perfil.sex).lower().startswith("f") \
        else MIN_CALORIES_M
    suelo = max(suelo_absoluto, tmb if not senior else tmb * SENIOR_FLOOR_TMB)
    if kcal < suelo:
        kcal = suelo
        if not reason:
            capped = True
            reason = ("La ingesta sugerida se limitó al gasto basal "
                      "mínimo seguro por encima del peso en reposo.")

    # 4. Techo de superávit
    techo_pct = 0.08 if senior else MAX_SURPLUS_PCT
    techo = tdee * (1.0 + techo_pct)
    if kcal > techo:
        kcal = techo
        capped = True
        reason = ("Superávit limitado al %d %% del gasto diario para que "
                  "el aumento sea de calidad (menor acúmulo de grasa)."
                  % round(techo_pct * 100))

    kcal = round(kcal)
    return kcal, kcal - tdee, capped, reason


def calcular_ajuste_por_composicion(perfil: UserProfile, tdee: float) -> float:
    """
    Ajuste opcional según % grasa (factor de actividad de Wilmore):
    - Hombres: >15 % grasa → +100 kcal por cada 5 % adicional.
    - Mujeres: >25 % grasa → +100 kcal por cada 5 % adicional.
    Limitado a +10 % del TDEE por seguridad.
    """
    grasa = _safe(perfil.body_fat_pct, 0.0)
    tdee_safe = _safe(tdee, 0.0)
    if grasa <= 0 or tdee_safe <= 0:
        return 0.0
    umbral = 15.0 if str(perfil.sex).lower().startswith("m") else 25.0
    if grasa <= umbral:
        return 0.0
    incrementos = int((grasa - umbral) // 5) + 1
    return round(min(100.0 * incrementos, tdee_safe * 0.10))


def calcular_agua_diaria(peso_kg: float) -> float:
    """Agua diaria (ml) — 35 ml/kg/día con piso 1200 y techo 5000 ml."""
    peso = _safe(peso_kg, 0.0)
    if peso <= 0:
        return 2000.0
    agua = peso * 35.0
    return float(round(min(max(agua, AGUA_MIN_ML), AGUA_MAX_ML)))


def calcular_superficie_corporal(peso_kg: float, estatura_cm: float) -> float:
    """Superficie corporal (m²) — fórmula de Mosteller."""
    peso = _safe(peso_kg, 0.0)
    estatura = _safe(estatura_cm, 0.0)
    if peso <= 0 or estatura <= 0:
        return 0.0
    sc = math.sqrt((peso * estatura) / 3600.0)
    return round(sc, 2) if math.isfinite(sc) else 0.0


def calcular_macronutrientes(calorias: float, objetivo: str,
                             perfil: UserProfile | None = None) -> dict:
    """
    Distribuye las calorías en macronutrientes según el objetivo.

    Retorna un dict con gramos de proteína, carbohidratos y grasas
    (claves históricas proteinas/carbohidratos/grasas + p_pct/c_pct/g_pct).

    Distribuciones base (% kcal):
      - perdida_grasa:    P 35 % | C 40 % | G 25 %
      - aumento_muscular: P 30 % | C 50 % | G 20 %
      - definicion:       P 40 % | C 35 % | G 25 %
      - recomposicion:    P 35 % | C 40 % | G 25 %
      - mantenimiento:    P 25 % | C 50 % | G 25 %

    Ajustes:
      - Adultos mayores (≥60): proteína mínima 30 % (prevención de
        sarcopenia, consenso PROT-AGE).
      - Menores de edad: proporciones moderadas (P 25 % / C 50 % / G 25 %).
    """
    kcal = _safe(calorias, 0.0)
    distribuciones = {
        "perdida_grasa":    (0.35, 0.40, 0.25),
        "aumento_muscular": (0.30, 0.50, 0.20),
        "definicion":       (0.40, 0.35, 0.25),
        "recomposicion":    (0.35, 0.40, 0.25),
        "mantenimiento":    (0.25, 0.50, 0.25),
    }
    p_pct, c_pct, g_pct = distribuciones.get((objetivo or "").lower(),
                                             (0.30, 0.45, 0.25))

    if perfil is not None:
        if perfil.is_minor():
            p_pct, c_pct, g_pct = 0.25, 0.50, 0.25
        elif perfil.is_senior() and p_pct < 0.30:
            resto = (1.0 - 0.30)
            base_resto = p_pct + c_pct + g_pct - p_pct  # c_pct + g_pct
            c_pct = round(c_pct / base_resto * resto, 3) if base_resto else 0.45
            g_pct = round(1.0 - 0.30 - c_pct, 3)
            p_pct = 0.30

    # 1 g proteína = 4 kcal | 1 g carbohidrato = 4 kcal | 1 g grasa = 9 kcal
    proteinas = round((kcal * p_pct) / 4, 1) if kcal else 0.0
    carbos = round((kcal * c_pct) / 4, 1) if kcal else 0.0
    grasas = round((kcal * g_pct) / 9, 1) if kcal else 0.0

    return {
        "proteinas":     proteinas,
        "carbohidratos": carbos,
        "grasas":        grasas,
        "p_pct":         int(round(p_pct * 100)),
        "c_pct":         int(round(c_pct * 100)),
        "g_pct":         int(round(g_pct * 100)),
    }


def calcular_proteina_recomendada(perfil: UserProfile) -> str:
    """
    Pauta de proteína (g/kg/día):
    - Adultos sedentarios: 0.8 g/kg (RDA).
    - Entrenamiento de fuerza: 1.6–2.2 g/kg (ACSM/ISSN).
    - Adultos ≥60: 1.0–1.2 g/kg (prevención de sarcopenia; PROT-AGE).
    - Menores: 0.9–1.4 g/kg según edad (AAP); sin excesos.
    """
    peso = _safe(perfil.weight, 0.0)
    if peso <= 0:
        return "0.8–1.0 g/kg/día"
    if perfil.is_minor():
        base, tope = 0.9, 1.4
    elif perfil.is_senior():
        base, tope = 1.0, 1.2
    else:
        if (perfil.activity_level or "") in ("moderado", "activo", "muy_activo"):
            base, tope = 1.6, 2.2
        else:
            base, tope = 0.8, 1.0
    return (f"{base}–{tope} g/kg/día "
            f"({round(peso * base)}–{round(peso * tope)} g/día)")


def calcular_pct_grasa_de_imc(imc: float, edad: int, sexo: str) -> float:
    """
    Estimación de % grasa a partir del IMC (Deurenberg):
    %G = (1.20 × IMC) + (0.23 × edad) − (10.8 × sexo) − 5.4
    donde sexo = 1 hombres, 0 mujeres. Solo estimación orientativa.
    """
    imc_v = _safe(imc, 0.0)
    edad_v = _safe(edad, 30.0)
    if imc_v <= 0:
        return 0.0
    sexo_v = 1.0 if str(sexo).lower().startswith(("m", "h", "var")) and \
        not str(sexo).lower().startswith("f") else 0.0
    grasa = (1.20 * imc_v) + (0.23 * edad_v) - (10.8 * sexo_v) - 5.4
    if not math.isfinite(grasa):
        return 0.0
    return round(min(max(grasa, 1.0), 70.0), 1)


def clasificar_composicion_corporal(pct_grasa: float, sexo: str) -> str:
    """Valoración orientativa según rangos ACSM."""
    grasa = _safe(pct_grasa, -1.0)
    if grasa <= 0:
        return "Sin datos"
    es_hombre = str(sexo).lower().startswith(("m", "h", "var")) and \
        not str(sexo).lower().startswith("f")
    if es_hombre:
        if grasa < 6:   return "Esencialmente graso"
        if grasa < 14:  return "Atleta / fitness"
        if grasa < 18:  return "Fitness aceptable"
        if grasa < 25:  return "Promedio aceptable"
        return "Alto porcentaje de grasa"
    if grasa < 14:  return "Esencialmente graso"
    if grasa < 21:  return "Atleta / fitness"
    if grasa < 25:  return "Fitness aceptable"
    if grasa < 32:  return "Promedio aceptable"
    return "Alto porcentaje de grasa"


def clasificar_porcentaje_grasa(pct_grasa: float, sexo: str) -> str:
    """Alias histórico de clasificar_composicion_corporal."""
    return clasificar_composicion_corporal(pct_grasa, sexo)


def obtener_imc_categoria(perfil: UserProfile) -> str:
    """
    Categoría IMC según grupo de edad:
    - Menores (<18): el IMC se valora por curvas de crecimiento
      (OMS/AAP), NO por cortes de adultos → etiqueta cualitativa.
    - Adultos ≥60: se considera riesgo de bajo peso (<22) por
      sarcopenia antes que los cortes estándar.
    - Adultos 18–59: clasificación OMS.
    """
    imc = _safe(perfil.imc, 0.0)
    if imc <= 0:
        return "Sin datos"
    if perfil.is_minor():
        return "Requiere valoración por percentiles (OMS/AAP)"
    if perfil.is_senior():
        if imc < 22.0:
            return "Bajo peso (riesgo en adultos mayores)"
        if imc < 27.0:
            return "Rango aceptable en adultos mayores"
    return calcular_imc_categoria(imc)


def calcular_factor_actividad(nivel: str) -> float:
    """Factor de actividad según nivel declarado (ACSM). Alias seguro."""
    return ACTIVITY_FACTORS.get((nivel or "").strip().lower(), 1.55)


# ──────────────────────────────────────────────
#  Orquestador principal
# ──────────────────────────────────────────────

def run_calculations(profile: UserProfile) -> None:
    """
    Ejecuta todos los cálculos y los almacena directamente en el perfil.

    Orden de ejecución:
      1. IMC + categoría (con tratamiento por edad).
      2. TMB (Mifflin-St Jeor) y TDEE (factor de actividad).
      3. Calorías objetivo con políticas de seguridad (deja traza del
         ajuste en caloric_adjustment / adjustment_capped / reason).
      4. Hidratación sugerida (ml/día).

    Nunca lanza excepción: las entradas no plausibles producen valores
    seguros (0 / "Sin datos") que las UIs muestran como estado vacío.
    """
    imc, categoria = calcular_imc(profile.weight, profile.height)
    profile.imc = imc
    profile.imc_category = categoria if imc > 0 else "Sin datos"

    profile.tmb = calcular_tmb(profile.weight, profile.height,
                               profile.age, profile.sex)
    profile.tdee = calcular_tdee(profile.tmb, profile.activity_level)
    profile.target_calories = calcular_calorias_objetivo(profile)

    # Categoría especial para menores / mayores (sobreescribe la adulta)
    profile.imc_category = obtener_imc_categoria(profile)

    profile.hidratacion_ml = calcular_agua_diaria(profile.weight)
