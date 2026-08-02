"""
nutrition.py
============
Planes alimenticios del Sistema Experto — v2.0

Genera planes con:
  - Filtros dietéticos (vegano, vegetariano, pescetariano)
  - Filtros de alergias (lactosa, gluten, nueces, etc.)
  - Frecuencia de comidas ajustable (3, 4 o 5 comidas al día)
  - Distribución de macronutrientes por objetivo
"""

import random
from user_profile import UserProfile
from calculations import calcular_macronutrientes


# ──────────────────────────────────────────────
#  Catálogos de comida por objetivo y tipo de dieta
# ──────────────────────────────────────────────

# Cada entrada es lista de opciones; se seleccionan aleatoriamente para variedad

MEAL_CATALOG = {

    # ── PÉRDIDA DE GRASA ─────────────────────────────────────────────────────

    "perdida_grasa": {
        "omnivoro": {
            "desayuno": [
                "Avena con leche descremada y frutas del bosque",
                "Huevos revueltos (3 claras + 1 yema) con espinacas y tomate",
                "Yogur griego natural con granola sin azúcar y kiwi",
                "Tortilla de claras con champiñones y pimiento",
                "Smoothie de proteína con leche descremada, espinaca y plátano",
            ],
            "almuerzo": [
                "Pechuga de pollo a la plancha con arroz integral y ensalada verde",
                "Salmón al horno con brócoli al vapor y batata cocida",
                "Atún en agua con pasta integral, tomate cherry y aceite de oliva",
                "Pavo a la plancha con quinoa y espárragos",
                "Merluza al horno con verduras asadas y arroz integral",
            ],
            "cena": [
                "Tortilla de claras de huevo con verduras salteadas",
                "Ensalada de pollo desmenuzado con lechuga, pepino y limón",
                "Crema de verduras con una porción de pollo o tofu",
                "Salmón a la plancha con ensalada mixta",
                "Pechuga de pavo con brócoli al vapor",
            ],
            "snacks": [
                "Manzana + 15 g de almendras",
                "Yogur griego sin azúcar",
                "Zanahorias crudas con hummus",
                "1 huevo duro",
                "Palitos de apio con queso cottage",
                "Nueces (30 g) + 1 fruta pequeña",
            ],
        },
        "vegetariano": {
            "desayuno": [
                "Avena con leche y frutas del bosque",
                "Yogur griego con granola sin azúcar y kiwi",
                "Tortilla de claras con espinacas y queso fresco",
                "Tostada integral con aguacate y huevo pochado",
                "Smoothie de yogur, espinaca y fresas",
            ],
            "almuerzo": [
                "Lentejas estofadas con verduras y arroz integral",
                "Ensalada de garbanzos con tomate, pepino y queso feta",
                "Revuelto de tofu con verduras y arroz integral",
                "Sopa de verduras con huevo duro y pan integral",
                "Bowl de quinoa con verduras asadas y huevo cocido",
            ],
            "cena": [
                "Tortilla de claras con champiñones y espinacas",
                "Ensalada de quinoa con remolacha y queso fresco",
                "Crema de calabaza con yogur y semillas",
                "Revuelto de huevo con verduras de temporada",
                "Bowl de edamame con arroz integral y soya",
            ],
            "snacks": [
                "Yogur griego sin azúcar",
                "Manzana con queso cottage",
                "Zanahorias con hummus",
                "Puñado de frutos secos",
                "Tostada integral con queso fresco",
            ],
        },
        "vegano": {
            "desayuno": [
                "Avena con bebida de avena y frutas del bosque",
                "Smoothie bowl de plátano, espinaca y semillas de chía",
                "Tostada integral con aguacate y tomate",
                "Yogur de soya con granola sin azúcar y fresas",
                "Porridge de avena con leche de almendra y arándanos",
            ],
            "almuerzo": [
                "Lentejas estofadas con arroz integral y ensalada verde",
                "Bowl de tofu a la plancha con brócoli y quinoa",
                "Ensalada de garbanzos, tomate, pepino y aceite de oliva",
                "Tempeh salteado con verduras y arroz integral",
                "Curry de legumbres con arroz basmati",
            ],
            "cena": [
                "Crema de calabaza con semillas de calabaza tostadas",
                "Ensalada de quinoa con aguacate y tomate cherry",
                "Revuelto de tofu con champiñones y espinacas",
                "Sopa de lentejas rojas con cúrcuma y limón",
                "Bowl de edamame con arroz integral y salsa tamari",
            ],
            "snacks": [
                "Manzana con mantequilla de almendra",
                "Hummus con palitos de zanahoria y apio",
                "Puñado de nueces y arándanos secos",
                "Yogur de soya sin azúcar",
                "Dátiles con mantequilla de maní (pequeña porción)",
            ],
        },
        "pescetariano": {
            "desayuno": [
                "Avena con leche y frutas del bosque",
                "Tostada integral con salmón ahumado y aguacate",
                "Yogur griego con granola y kiwi",
                "Huevos revueltos con espinacas y tomate",
                "Smoothie de proteína con leche, espinaca y plátano",
            ],
            "almuerzo": [
                "Salmón a la plancha con arroz integral y brócoli",
                "Atún en agua con ensalada mixta y tomate",
                "Merluza al horno con verduras asadas",
                "Ceviche de gambas con aguacate y tortillas de maíz",
                "Bowl de atún con quinoa, pepino y edamame",
            ],
            "cena": [
                "Salmón a la plancha con ensalada mixta",
                "Tortilla de claras con gambas y verduras",
                "Crema de verduras con mejillones al vapor",
                "Ensalada de atún con lechuga, pepino y limón",
                "Merluza al vapor con espárragos",
            ],
            "snacks": [
                "Yogur griego sin azúcar",
                "Manzana + 15 g de almendras",
                "Atún en lata con galletas de arroz",
                "Zanahorias con hummus",
                "1 huevo duro",
            ],
        },
    },

    # ── AUMENTO MUSCULAR ──────────────────────────────────────────────────────

    "aumento_muscular": {
        "omnivoro": {
            "desayuno": [
                "Tortilla de 4 huevos enteros con avena y plátano",
                "Batido de proteína con leche entera, avena, mantequilla de maní y plátano",
                "Tostadas integrales con aguacate, huevos revueltos y zumo natural",
                "Tortilla de 3 huevos con avena cocida y fruta",
                "Yogur griego con granola, frutos secos y miel",
            ],
            "almuerzo": [
                "Arroz blanco con pechuga de pollo (200 g) y vegetales salteados",
                "Pasta con atún, aceite de oliva, tomate y queso rallado",
                "Carne de res magra con patata cocida y ensalada con aceite",
                "Arroz integral con salmón y verduras al wok",
                "Pollo al horno con quinoa, aguacate y ensalada",
            ],
            "cena": [
                "Salmón con quinoa y espárragos al horno",
                "Pollo al horno con arroz integral y brócoli con mantequilla",
                "Ternera con patata y vegetales, vaso de leche entera",
                "Tortilla de 3 huevos con patata y verduras salteadas",
                "Pavo con arroz y ensalada con aceite de oliva",
            ],
            "snacks": [
                "Batido de proteína post-entreno",
                "Pan integral con mantequilla de maní y plátano",
                "Requesón con miel y nueces",
                "Frutos secos y fruta",
                "Queso cottage con crackers integrales",
                "Huevos duros (2) con arroz",
            ],
        },
        "vegetariano": {
            "desayuno": [
                "Tortilla de 4 huevos con avena y plátano",
                "Batido de proteína de suero con leche, avena y plátano",
                "Tostadas con mantequilla de maní, huevos revueltos y fruta",
                "Yogur griego (250 g) con granola, nueces y miel",
                "Pancakes de avena y huevo con fruta y miel",
            ],
            "almuerzo": [
                "Lentejas estofadas con arroz blanco y ensalada",
                "Bowl de garbanzos con quinoa, aguacate y queso feta",
                "Pasta con salsa de tomate, ricotta y queso parmesano",
                "Revuelto de tofu firme con verduras y arroz integral",
                "Sopa de legumbres con patata y pan integral",
            ],
            "cena": [
                "Tortilla de 3 huevos con patata, cebolla y queso",
                "Quinoa con tofu a la plancha y verduras salteadas",
                "Pasta con huevo y queso parmesano (cacio e pepe)",
                "Revuelto de tempeh con arroz y verduras",
                "Bowl de edamame con arroz, aguacate y soya",
            ],
            "snacks": [
                "Batido de proteína de suero con leche",
                "Queso cottage con crackers integrales y miel",
                "Pan integral con mantequilla de maní y plátano",
                "Requesón con nueces y fruta",
                "Yogur griego con granola",
            ],
        },
        "vegano": {
            "desayuno": [
                "Batido de proteína vegana con leche de soya, avena y plátano",
                "Tostadas integrales con mantequilla de maní, plátano y semillas",
                "Porridge de avena con leche de soya, frutos secos y miel de agave",
                "Smoothie bowl de proteína vegana, frutas y granola",
                "Tortilla de tofu con verduras y tostadas integrales",
            ],
            "almuerzo": [
                "Arroz blanco con tempeh a la plancha y verduras salteadas",
                "Bowl de lentejas, quinoa, aguacate y ensalada",
                "Pasta con salsa de tomate, tofu desmenuzado y levadura nutricional",
                "Curry de garbanzos con arroz basmati y pan naan",
                "Seitán salteado con arroz integral y brócoli",
            ],
            "cena": [
                "Tofu firme a la plancha con quinoa y verduras al wok",
                "Bowl de arroz integral, edamame, aguacate y algas",
                "Tempeh con patata cocida y ensalada con aceite de oliva",
                "Sopa de lentejas rojas con arroz y espinacas",
                "Pasta con salsa de anacardos y levadura nutricional",
            ],
            "snacks": [
                "Batido de proteína vegana post-entreno",
                "Pan integral con mantequilla de maní y plátano",
                "Puñado grande de frutos secos variados y dátiles",
                "Hummus con pan pita integral",
                "Yogur de soya con granola y miel de agave",
            ],
        },
        "pescetariano": {
            "desayuno": [
                "Tostadas con salmón ahumado, huevo pochado y aguacate",
                "Batido de proteína con leche, plátano y avena",
                "Tortilla de 4 huevos con espinacas y salmón",
                "Yogur griego con granola, nueces y miel",
                "Avena con leche entera, frutos secos y miel",
            ],
            "almuerzo": [
                "Salmón al horno con arroz blanco y ensalada con aceite",
                "Pasta con atún, aceite de oliva y queso parmesano",
                "Arroz integral con gambas salteadas y verduras",
                "Bowl de atún, quinoa, aguacate y tomate",
                "Merluza con patata cocida y ensalada",
            ],
            "cena": [
                "Salmón a la plancha con quinoa y espárragos",
                "Tortilla de huevo con gambas y verduras",
                "Lubina al horno con arroz integral y brócoli",
                "Dorada a la plancha con patata cocida",
                "Poke bowl de atún, arroz, aguacate y edamame",
            ],
            "snacks": [
                "Batido de proteína post-entreno",
                "Atún con crackers integrales",
                "Huevos duros con fruta",
                "Yogur griego con nueces y miel",
                "Pan integral con mantequilla de maní y plátano",
            ],
        },
    },

    # ── DEFINICIÓN ────────────────────────────────────────────────────────────

    "definicion": {
        "omnivoro": {
            "desayuno": [
                "Claras de huevo (5) con avena y arándanos",
                "Yogur griego con semillas de chía y fresas",
                "Tortilla de claras con espinacas y café negro",
                "Smoothie de proteína con leche descremada y fruta",
                "Avena con agua, canela y 1 cucharada de proteína",
            ],
            "almuerzo": [
                "Pechuga de pollo a la plancha con arroz integral (porción reducida) y brócoli",
                "Salmón con ensalada mixta y quinoa",
                "Ensalada de atún con hojas verdes, tomate y pepino",
                "Pavo a la plancha con arroz integral y espárragos",
                "Merluza con verduras asadas y ensalada",
            ],
            "cena": [
                "Pechuga de pollo hervida con ensalada de pepino y tomate",
                "Tortilla de claras con espinacas y champiñones",
                "Atún en agua con lechuga y una pequeña porción de arroz integral",
                "Salmón a la plancha con ensalada verde",
                "Pechuga de pavo con brócoli al vapor",
            ],
            "snacks": [
                "Pepino en rodajas con sal de ajo",
                "Yogur griego 0% grasa",
                "Clara de huevo cocida",
                "Té verde sin azúcar",
                "Palitos de apio",
                "Fruta baja en azúcar (fresa, kiwi)",
            ],
        },
        "vegano": {
            "desayuno": [
                "Avena con agua o bebida de almendra sin azúcar y fresas",
                "Smoothie de proteína vegana con espinaca y plátano",
                "Yogur de soya 0% con semillas de chía y arándanos",
                "Tostada de arroz con aguacate y tomate",
                "Porridge de avena con bebida de avena y fruta",
            ],
            "almuerzo": [
                "Ensalada de garbanzos, tomate, pepino y limón",
                "Bowl de tofu a la plancha con quinoa y verduras",
                "Sopa de lentejas rojas con espinacas",
                "Tempeh con arroz integral y brócoli",
                "Ensalada de quinoa con aguacate y semillas",
            ],
            "cena": [
                "Crema de calabaza sin nata con semillas de calabaza",
                "Ensalada de quinoa con pepino, tomate cherry y limón",
                "Sopa de verduras con tofu suave",
                "Bowl de edamame con arroz integral y algas",
                "Revuelto de tofu con espinacas y champiñones",
            ],
            "snacks": [
                "Pepino con limón y chile",
                "Palitos de zanahoria con hummus light",
                "Fruta baja en azúcar (fresas, arándanos)",
                "Té verde o infusión sin azúcar",
                "Semillas de calabaza tostadas (30 g)",
            ],
        },
        "vegetariano": {
            "desayuno": [
                "Claras de huevo con avena y arándanos",
                "Yogur griego 0% con semillas de chía y fresas",
                "Tortilla de claras con espinacas y queso fresco",
                "Smoothie de yogur, espinaca y frutas bajas en azúcar",
                "Tostada integral con queso fresco y tomate",
            ],
            "almuerzo": [
                "Ensalada de garbanzos con queso feta, tomate y pepino",
                "Sopa de lentejas con verduras y arroz integral",
                "Revuelto de huevo con espinacas y champiñones",
                "Bowl de quinoa con verduras asadas y queso fresco",
                "Tortilla de claras con brócoli y pimiento",
            ],
            "cena": [
                "Yogur griego con pepino y hierbas (tzatziki) con tostadas de arroz",
                "Ensalada de huevo cocido con lechuga, tomate y limón",
                "Crema de verduras con queso cottage",
                "Tortilla de claras con champiñones",
                "Sopa de verduras con huevo",
            ],
            "snacks": [
                "Yogur griego 0% sin azúcar",
                "Fruta baja en azúcar (kiwi, fresa)",
                "Queso cottage con palitos de apio",
                "Clara de huevo cocida",
                "Té verde sin azúcar",
            ],
        },
        "pescetariano": {
            "desayuno": [
                "Claras de huevo con avena y arándanos",
                "Yogur griego con semillas de chía y fresas",
                "Tostada de arroz con salmón ahumado y pepino",
                "Smoothie de proteína con leche descremada",
                "Avena con agua y 1 cucharada de proteína",
            ],
            "almuerzo": [
                "Atún en agua con ensalada de hojas verdes y tomate",
                "Salmón a la plancha con arroz integral y espárragos",
                "Merluza al horno con brócoli al vapor",
                "Ensalada de gambas con lechuga, pepino y limón",
                "Ceviche de pescado blanco con tomate y cilantro",
            ],
            "cena": [
                "Salmón a la plancha con ensalada verde",
                "Atún en agua con lechuga y arroz integral (pequeña porción)",
                "Tortilla de claras con gambas",
                "Merluza al vapor con espárragos",
                "Ensalada de surimi con lechuga y tomate",
            ],
            "snacks": [
                "Yogur griego 0% sin azúcar",
                "Atún en lata con pepino",
                "Fruta baja en azúcar",
                "Clara de huevo cocida",
                "Té verde sin azúcar",
            ],
        },
    },
}

# Usar definición como base para recomposición y mantenimiento
MEAL_CATALOG["recomposicion"] = MEAL_CATALOG["aumento_muscular"]
MEAL_CATALOG["mantenimiento"] = {
    diet: {
        meal: (MEAL_CATALOG["perdida_grasa"].get(diet, {}).get(meal, [])[:2]
               + MEAL_CATALOG["aumento_muscular"].get(diet, {}).get(meal, [])[:2])
        for meal in ["desayuno", "almuerzo", "cena", "snacks"]
    }
    for diet in ["omnivoro", "vegetariano", "vegano", "pescetariano"]
}


# ──────────────────────────────────────────────
#  Alimentos excluidos por alergia
# ──────────────────────────────────────────────

ALLERGEN_KEYWORDS = {
    "lactosa":  ["leche", "lácteo", "queso", "yogur", "ricotta", "mantequilla", "requesón",
                 "nata", "crema", "suero", "cottage", "kéfir"],
    "gluten":   ["pan", "tostada", "pasta", "trigo", "cebada", "centeno", "granola",
                 "galleta", "crackers", "naan", "pita", "avena"],  # avena contaminada
    "nueces":   ["nueces", "almendras", "cacahuetes", "maní", "anacardos", "pistachos"],
    "soya":     ["tofu", "soya", "soja", "edamame", "tempeh", "tamari", "miso"],
    "huevo":    ["huevo", "clara", "tortilla", "revuelto", "pochado"],
}


def _item_is_safe(item: str, allergies: list) -> bool:
    """Verifica que un alimento no contenga ingredientes alérgenos."""
    item_lower = item.lower()
    for allergen in allergies:
        keywords = ALLERGEN_KEYWORDS.get(allergen, [])
        for kw in keywords:
            if kw in item_lower:
                return False
    return True


def _filter_meal_list(meal_list: list, allergies: list) -> list:
    """Filtra una lista de opciones de comida eliminando las que contienen alérgenos."""
    safe = [item for item in meal_list if _item_is_safe(item, allergies)]
    return safe if safe else ["Consulta con un nutricionista para opciones personalizadas según tus restricciones."]


# ──────────────────────────────────────────────
#  Función principal
# ──────────────────────────────────────────────

def generate_nutrition_plan(profile: UserProfile) -> dict:
    """
    Genera el plan nutricional completo para el usuario.

    Aplica filtros dietéticos (vegano, vegetariano, etc.) y de alergias.
    Ajusta la frecuencia de comidas (3, 4 o 5 comidas al día).
    Selecciona opciones variadas aleatoriamente del catálogo.

    Retorna un dict con:
      - calorias_objetivo
      - macros
      - plan (con las comidas del día)
      - hidratacion
    """
    objetivo   = profile.objective
    diet_type  = profile.diet_type or "omnivoro"
    allergies  = profile.allergies or []
    freq       = profile.meal_frequency or 3

    # Obtener catálogo según objetivo y tipo de dieta
    obj_catalog  = MEAL_CATALOG.get(objetivo, MEAL_CATALOG["mantenimiento"])
    diet_catalog = obj_catalog.get(diet_type, obj_catalog.get("omnivoro", {}))

    # Filtrar por alergias y seleccionar variedad aleatoria
    def pick(meal_key: str) -> str:
        options = diet_catalog.get(meal_key, ["Consulta opciones con un nutricionista."])
        safe    = _filter_meal_list(options, allergies)
        return random.choice(safe)

    plan = {
        "desayuno": [pick("desayuno")],
        "almuerzo": [pick("almuerzo")],
        "cena":     [pick("cena")],
        "snacks":   [],
        "hidratacion": _get_hidratacion(objetivo),
    }

    # Distribución según frecuencia de comidas
    if freq >= 4:
        plan["snacks"].append(pick("snacks"))          # media mañana
    if freq >= 5:
        plan["snacks"].append(pick("snacks"))          # merienda tarde
    if freq >= 4 and not plan["snacks"]:
        plan["snacks"].append(pick("snacks"))

    if not plan["snacks"]:
        plan["snacks"] = ["Snacks integrados en las comidas principales (3 comidas/día)"]

    macros = calcular_macronutrientes(profile.target_calories, objetivo)

    return {
        "calorias_objetivo": profile.target_calories,
        "macros":            macros,
        "plan":              plan,
        "frecuencia":        freq,
        "tipo_dieta":        diet_type,
        "alergias_activas":  allergies,
    }


def _get_hidratacion(objetivo: str) -> str:
    tabla = {
        "perdida_grasa":    "2.5–3 litros de agua. Evitar bebidas azucaradas y alcohol.",
        "aumento_muscular": "3–4 litros de agua. Batido post-entrenamiento en los 30 min post-sesión.",
        "definicion":       "3 litros de agua. Reducir sodio para evitar retención de líquidos.",
        "recomposicion":    "2.5–3 litros de agua diarios.",
        "mantenimiento":    "2–2.5 litros de agua diarios.",
    }
    return tabla.get(objetivo, "2–3 litros de agua diarios.")
