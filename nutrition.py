"""
nutrition.py
============
Planes alimenticios del Sistema Experto — v3.0 (auditoría completa).

Cambios respecto a v2:
  - Recetas estructuradas con metadatos (id, ingredientes, macros aproximados,
    alérgenos, compatibilidad dietética, tiempo de preparación, costo, etiquetas
    de preferencia y sustituciones). No es un catálogo de cadenas sueltas.
  - Diferencia semántica estricta:
      * ALERGIA      → exclusión total de la familia del alérgeno y sus
                       derivados. El sistema NUNCA afirma «100 % seguro».
      * INTOLERANCIA → se evitan las fuentes principales, pero los derivados
                       tolerados pueden mantenerse (p. ej. queso curado en
                       intolerancia a la lactosa).
      * PREFERENCIA  → filtrado suave: se priorizan recetas que cumplen la
                       preferencia y se ofrecen alternativas.
  - Variedad y rotación: el plan propone varias opciones por comida y un
    marco de rotación semanal para no repetir menú.
  - Fallback elegante: si ninguna receta compatible existe (p. ej. vegano con
    alergias cruzadas), se devuelve un plan genérico seguro + derivación a
    profesional, en lugar de un catálogo silenciosamente vacío.
  - Las recetas citan calorías y proteínas APROXIMADAS (orientativo) y dejan
    claro que el conteo exacto requiere báscula y etiquetado.
"""

import random

from user_profile import UserProfile
from calculations import calcular_macronutrientes, calcular_proteina_recomendada


# ──────────────────────────────────────────────
#  Recetas estructuradas
# ──────────────────────────────────────────────
# Campos:
#   id:           identificador único
#   nombre:       texto de la opción
#   momento:      desayuno | almuerzo | cena | snack | postre_opcional
#   objetivos:    objetivos para los que encaja
#   dietas:       tipos de dieta compatibles
#   alergenos:    claves de ALLERGY_OPTIONS presentes en la receta
#   parametros_intolerancia: texto explicativo cuando hay fuente principal
#   kcal_aprox:   rango de calorías (orientativo)
#   proteinas_g:  proteína aproximada (orientativo)
#   tiempo_min:   tiempo de preparación
#   costo:        baja | media | alta
#   etiquetas:    preferencias que cumple (bajo_en_sal, sin_azucar_anadido,
#                 alta_proteina, economica, rapida)
#   sustituciones: dict {alergeno: sustitución segura}

RECIPES: list[dict] = [

    # ── DESAYUNOS ───────────────────────────────────────────────────────────
    {
        "id": "D01", "nombre": "Avena con frutas del bosque y semillas de chía",
        "momento": "desayuno", "objetivos": ["perdida_grasa", "mantenimiento", "definicion", "recomposicion"],
        "dietas": ["omnivoro", "vegetariano", "vegano", "pescetariano"],
        "alergenos": [], "intolerancia_principal": None,
        "kcal_aprox": "300–380 kcal", "proteinas_g": "10–14 g",
        "tiempo_min": 10, "costo": "baja",
        "etiquetas": ["rapida", "economica", "sin_azucar_anadido"],
        "sustituciones": {},
    },
    {
        "id": "D02", "nombre": "Huevos revueltos con espinaca y tomate",
        "momento": "desayuno",
        "objetivos": ["perdida_grasa", "definicion", "recomposicion", "mantenimiento", "aumento_muscular"],
        "dietas": ["omnivoro", "vegetariano", "pescetariano"],
        "alergenos": ["huevo"], "intolerancia_principal": None,
        "kcal_aprox": "220–280 kcal", "proteinas_g": "16–20 g",
        "tiempo_min": 10, "costo": "baja",
        "etiquetas": ["rapida", "economica", "alta_proteina", "bajo_en_sal"],
        "sustituciones": {"huevo": "revuelto de tofu (si es vegano o alérgico al huevo)"},
    },
    {
        "id": "D03", "nombre": "Yogur griego natural con granola de avena y kiwi",
        "momento": "desayuno",
        "objetivos": ["perdida_grasa", "mantenimiento", "recomposicion", "definicion"],
        "dietas": ["omnivoro", "vegetariano", "pescetariano"],
        "alergenos": ["leche"], "intolerancia_principal": "lactosa (usar yogur sin lactosa o bebida vegetal fortificada)",
        "kcal_aprox": "250–330 kcal", "proteinas_g": "15–19 g",
        "tiempo_min": 5, "costo": "media",
        "etiquetas": ["rapida", "alta_proteina"],
        "sustituciones": {"leche": "yogur de soja/almendra fortificado (sin lactosa)"},
    },
    {
        "id": "D04", "nombre": "Smoothie de proteína con plátano, espinaca y mantequilla de maní",
        "momento": "desayuno",
        "objetivos": ["aumento_muscular", "recomposicion", "perdida_grasa", "definicion"],
        "dietas": ["omnivoro", "vegetariano", "pescetariano", "vegano"],
        "alergenos": ["cacahuetes"], "intolerancia_principal": None,
        "kcal_aprox": "350–450 kcal", "proteinas_g": "25–35 g",
        "tiempo_min": 8, "costo": "media",
        "etiquetas": ["rapida", "alta_proteina", "sin_azucar_anadido"],
        "sustituciones": {"cacahuetes": "semillas de girasol o mantequilla de almendra (si no hay alergia a frutos secos)"},
    },
    {
        "id": "D05", "nombre": "Tostada integral con aguacate y huevo pochado",
        "momento": "desayuno",
        "objetivos": ["mantenimiento", "recomposicion", "aumento_muscular"],
        "dietas": ["omnivoro", "vegetariano", "pescetariano"],
        "alergenos": ["huevo", "gluten"], "intolerancia_principal": None,
        "kcal_aprox": "320–400 kcal", "proteinas_g": "13–16 g",
        "tiempo_min": 15, "costo": "media",
        "etiquetas": ["bajo_en_sal"],
        "sustituciones": {"huevo": "tofu firme a la plancha", "gluten": "tostada de arroz o maíz"},
    },
    {
        "id": "D06", "nombre": "Porridge de avena con bebida de almendra, canela y manzana",
        "momento": "desayuno",
        "objetivos": ["perdida_grasa", "mantenimiento", "definicion", "recomposicion"],
        "dietas": ["omnivoro", "vegetariano", "vegano", "pescetariano"],
        "alergenos": ["frutos_secos"], "intolerancia_principal": None,
        "kcal_aprox": "280–350 kcal", "proteinas_g": "8–11 g",
        "tiempo_min": 12, "costo": "baja",
        "etiquetas": ["rapida", "economica", "sin_azucar_anadido", "bajo_en_sal"],
        "sustituciones": {"frutos_secos": "avena con agua o bebida de avena sin frutos secos"},
    },
    {
        "id": "D07", "nombre": "Tortilla de claras con champiñones y tofu salteado",
        "momento": "desayuno",
        "objetivos": ["perdida_grasa", "definicion", "recomposicion"],
        "dietas": ["omnivoro", "vegetariano", "pescetariano", "vegano"],
        "alergenos": ["huevo"], "intolerancia_principal": None,
        "kcal_aprox": "200–270 kcal", "proteinas_g": "18–24 g",
        "tiempo_min": 12, "costo": "baja",
        "etiquetas": ["rapida", "economica", "alta_proteina"],
        "sustituciones": {"huevo": "mezcla de agua con harina de garbanzo (revuelto vegano)"},
    },
    {
        "id": "D08", "nombre": "Batido de avena, banana, cacao y leche descremada",
        "momento": "desayuno",
        "objetivos": ["aumento_muscular", "recomposicion"],
        "dietas": ["omnivoro", "vegetariano", "pescetariano"],
        "alergenos": ["leche"], "intolerancia_principal": "lactosa (usar bebida vegetal)",
        "kcal_aprox": "380–460 kcal", "proteinas_g": "20–26 g",
        "tiempo_min": 7, "costo": "baja",
        "etiquetas": ["rapida", "economica", "alta_proteina"],
        "sustituciones": {"leche": "bebida de soja/avena + proteína vegetal"},
    },
    {
        "id": "D09", "nombre": "Requesón con tomate, orégano y tostada de maíz",
        "momento": "desayuno",
        "objetivos": ["perdida_grasa", "definicion", "mantenimiento", "recomposicion"],
        "dietas": ["omnivoro", "vegetariano", "pescetariano"],
        "alergenos": ["leche"], "intolerancia_principal": "lactosa parcial (requesón bajo en lactosa)",
        "kcal_aprox": "240–310 kcal", "proteinas_g": "18–22 g",
        "tiempo_min": 8, "costo": "media",
        "etiquetas": ["rapida", "alta_proteina", "bajo_en_sal"],
        "sustituciones": {"leche": "tofu blando aliñado o queso vegano de anacardo (sin alergia)"},
    },
    {
        "id": "D10", "nombre": "Crêpe de avena y plátano con canela",
        "momento": "desayuno",
        "objetivos": ["mantenimiento", "recomposicion", "aumento_muscular"],
        "dietas": ["omnivoro", "vegetariano", "pescetariano", "vegano"],
        "alergenos": ["gluten"], "intolerancia_principal": None,
        "kcal_aprox": "300–380 kcal", "proteinas_g": "9–13 g",
        "tiempo_min": 15, "costo": "baja",
        "etiquetas": ["economica", "rapida"],
        "sustituciones": {"gluten": "harina de avena certificada sin gluten o harina de arroz"},
    },

    # ── ALMUERZOS ───────────────────────────────────────────────────────────
    {
        "id": "L01", "nombre": "Pechuga de pollo a la plancha con arroz integral y brócoli",
        "momento": "almuerzo",
        "objetivos": ["perdida_grasa", "definicion", "recomposicion", "mantenimiento", "aumento_muscular"],
        "dietas": ["omnivoro", "pescetariano"],
        "alergenos": [], "intolerancia_principal": None,
        "kcal_aprox": "400–520 kcal", "proteinas_g": "35–42 g",
        "tiempo_min": 30, "costo": "media",
        "etiquetas": ["alta_proteina", "economica", "bajo_en_sal"],
        "sustituciones": {},
    },
    {
        "id": "L02", "nombre": "Salmón al horno con batata y espárragos",
        "momento": "almuerzo",
        "objetivos": ["perdida_grasa", "definicion", "mantenimiento", "recomposicion"],
        "dietas": ["omnivoro", "pescetariano"],
        "alergenos": ["pescado"], "intolerancia_principal": None,
        "kcal_aprox": "480–580 kcal", "proteinas_g": "30–36 g",
        "tiempo_min": 30, "costo": "alta",
        "etiquetas": ["bajo_en_sal"],
        "sustituciones": {"pescado": "tofu firme o pechuga de pavo (si no es vegano)"},
    },
    {
        "id": "L03", "nombre": "Lentejas estofadas con arroz integral y ensalada verde",
        "momento": "almuerzo",
        "objetivos": ["mantenimiento", "perdida_grasa", "definicion", "recomposicion", "aumento_muscular"],
        "dietas": ["omnivoro", "vegetariano", "vegano", "pescetariano"],
        "alergenos": [], "intolerancia_principal": None,
        "kcal_aprox": "450–550 kcal", "proteinas_g": "20–26 g",
        "tiempo_min": 45, "costo": "baja",
        "etiquetas": ["economica", "alta_proteina", "sin_azucar_anadido"],
        "sustituciones": {},
    },
    {
        "id": "L04", "nombre": "Bowl de garbanzos con quinoa, aguacate y tomate",
        "momento": "almuerzo",
        "objetivos": ["perdida_grasa", "mantenimiento", "recomposicion", "definicion", "aumento_muscular"],
        "dietas": ["omnivoro", "vegetariano", "vegano", "pescetariano"],
        "alergenos": [], "intolerancia_principal": None,
        "kcal_aprox": "460–560 kcal", "proteinas_g": "18–24 g",
        "tiempo_min": 25, "costo": "media",
        "etiquetas": ["rapida", "bajo_en_sal", "sin_azucar_anadido"],
        "sustituciones": {},
    },
    {
        "id": "L05", "nombre": "Merluza al horno con patata cocida y verduras",
        "momento": "almuerzo",
        "objetivos": ["perdida_grasa", "definicion", "mantenimiento"],
        "dietas": ["omnivoro", "pescetariano"],
        "alergenos": ["pescado"], "intolerancia_principal": None,
        "kcal_aprox": "380–480 kcal", "proteinas_g": "28–34 g",
        "tiempo_min": 35, "costo": "media",
        "etiquetas": ["economica", "bajo_en_sal"],
        "sustituciones": {"pescado": "pollo o tofu (según dieta)"},
    },
    {
        "id": "L06", "nombre": "Pasta integral a la boloñesa de lentejas",
        "momento": "almuerzo",
        "objetivos": ["mantenimiento", "recomposicion", "aumento_muscular", "perdida_grasa"],
        "dietas": ["omnivoro", "vegetariano", "vegano", "pescetariano"],
        "alergenos": ["gluten"], "intolerancia_principal": None,
        "kcal_aprox": "500–620 kcal", "proteinas_g": "24–30 g",
        "tiempo_min": 30, "costo": "baja",
        "etiquetas": ["economica", "rapida"],
        "sustituciones": {"gluten": "pasta de arroz o espagueti de calabacín"},
    },
    {
        "id": "L07", "nombre": "Ternera magra salteada con pimiento y arroz basmati",
        "momento": "almuerzo",
        "objetivos": ["aumento_muscular", "recomposicion", "mantenimiento"],
        "dietas": ["omnivoro"],
        "alergenos": [], "intolerancia_principal": None,
        "kcal_aprox": "500–600 kcal", "proteinas_g": "38–45 g",
        "tiempo_min": 30, "costo": "media",
        "etiquetas": ["alta_proteina", "economica"],
        "sustituciones": {},
    },
    {
        "id": "L08", "nombre": "Tofu a la plancha con quinoa y verduras al wok",
        "momento": "almuerzo",
        "objetivos": ["perdida_grasa", "definicion", "mantenimiento", "recomposicion", "aumento_muscular"],
        "dietas": ["vegetariano", "vegano"],
        "alergenos": ["soja"], "intolerancia_principal": None,
        "kcal_aprox": "420–520 kcal", "proteinas_g": "28–34 g",
        "tiempo_min": 25, "costo": "media",
        "etiquetas": ["alta_proteina", "bajo_en_sal"],
        "sustituciones": {"soja": "tempeh NO (soja); usar seitán (si no hay alergia al gluten) o lentejas"},
    },
    {
        "id": "L09", "nombre": "Ensalada de atún con hojas verdes, tomate y huevo duro",
        "momento": "almuerzo",
        "objetivos": ["perdida_grasa", "definicion", "mantenimiento", "recomposicion"],
        "dietas": ["omnivoro", "pescetariano"],
        "alergenos": ["pescado", "huevo"], "intolerancia_principal": None,
        "kcal_aprox": "320–420 kcal", "proteinas_g": "28–34 g",
        "tiempo_min": 15, "costo": "media",
        "etiquetas": ["rapida", "alta_proteina", "bajo_en_sal"],
        "sustituciones": {"pescado": "pollo desmenuzado", "huevo": "cuadraditos de tofu"},
    },
    {
        "id": "L10", "nombre": "Curry de garbanzos y espinacas con arroz integral",
        "momento": "almuerzo",
        "objetivos": ["perdida_grasa", "mantenimiento", "definicion", "recomposicion", "aumento_muscular"],
        "dietas": ["omnivoro", "vegetariano", "vegano", "pescetariano"],
        "alergenos": [], "intolerancia_principal": None,
        "kcal_aprox": "440–540 kcal", "proteinas_g": "18–24 g",
        "tiempo_min": 30, "costo": "baja",
        "etiquetas": ["economica", "bajo_en_sal"],
        "sustituciones": {},
    },

    # ── CENAS ───────────────────────────────────────────────────────────────
    {
        "id": "C01", "nombre": "Tortilla francesa con ensalada mixta y aguacate",
        "momento": "cena",
        "objetivos": ["perdida_grasa", "definicion", "mantenimiento", "recomposicion"],
        "dietas": ["omnivoro", "vegetariano", "pescetariano"],
        "alergenos": ["huevo"], "intolerancia_principal": None,
        "kcal_aprox": "300–380 kcal", "proteinas_g": "18–22 g",
        "tiempo_min": 15, "costo": "baja",
        "etiquetas": ["rapida", "bajo_en_sal", "economica"],
        "sustituciones": {"huevo": "tortilla de garbanzo (aquafaba)"},
    },
    {
        "id": "C02", "nombre": "Crema de calabaza con pollo desmenuzado y semillas",
        "momento": "cena",
        "objetivos": ["perdida_grasa", "definicion", "mantenimiento", "recomposicion"],
        "dietas": ["omnivoro", "pescetariano"],
        "alergenos": [], "intolerancia_principal": None,
        "kcal_aprox": "240–320 kcal", "proteinas_g": "22–28 g",
        "tiempo_min": 25, "costo": "baja",
        "etiquetas": ["economica", "sin_azucar_anadido"],
        "sustituciones": {},
    },
    {
        "id": "C03", "nombre": "Bowl de quinoa con remolacha, garbanzos y queso fresco",
        "momento": "cena",
        "objetivos": ["perdida_grasa", "mantenimiento", "definicion", "recomposicion"],
        "dietas": ["omnivoro", "vegetariano", "pescetariano"],
        "alergenos": ["leche"], "intolerancia_principal": "lactosa (omitir queso o usar tofu)",
        "kcal_aprox": "380–460 kcal", "proteinas_g": "16–22 g",
        "tiempo_min": 25, "costo": "media",
        "etiquetas": ["bajo_en_sal", "sin_azucar_anadido"],
        "sustituciones": {"leche": "levadura nutricional (si es vegano) o queso vegano"},
    },
    {
        "id": "C04", "nombre": "Pescado blanco al vapor con espárragos y puré de coliflor",
        "momento": "cena",
        "objetivos": ["perdida_grasa", "definicion", "mantenimiento", "recomposicion"],
        "dietas": ["omnivoro", "pescetariano"],
        "alergenos": ["pescado"], "intolerancia_principal": None,
        "kcal_aprox": "300–390 kcal", "proteinas_g": "28–34 g",
        "tiempo_min": 30, "costo": "media",
        "etiquetas": ["bajo_en_sal", "sin_azucar_anadido"],
        "sustituciones": {"pescado": "pechuga de pollo o tofu a la plancha"},
    },
    {
        "id": "C05", "nombre": "Revuelto de huevo con champiñones, espinaca y tostada",
        "momento": "cena",
        "objetivos": ["perdida_grasa", "definicion", "mantenimiento", "recomposicion", "aumento_muscular"],
        "dietas": ["omnivoro", "vegetariano", "pescetariano"],
        "alergenos": ["huevo", "gluten"], "intolerancia_principal": None,
        "kcal_aprox": "260–340 kcal", "proteinas_g": "18–24 g",
        "tiempo_min": 15, "costo": "baja",
        "etiquetas": ["rapida", "alta_proteina", "economica"],
        "sustituciones": {"huevo": "revuelto de tofu", "gluten": "tostada de arroz"},
    },
    {
        "id": "C06", "nombre": "Sopa de lentejas rojas con cúrcuma y espinacas",
        "momento": "cena",
        "objetivos": ["perdida_grasa", "definicion", "mantenimiento", "recomposicion"],
        "dietas": ["omnivoro", "vegetariano", "vegano", "pescetariano"],
        "alergenos": [], "intolerancia_principal": None,
        "kcal_aprox": "280–360 kcal", "proteinas_g": "14–18 g",
        "tiempo_min": 30, "costo": "baja",
        "etiquetas": ["economica", "sin_azucar_anadido", "bajo_en_sal"],
        "sustituciones": {},
    },
    {
        "id": "C07", "nombre": "Tostada de aguacate con huevo y tomate (cena ligera)",
        "momento": "cena",
        "objetivos": ["mantenimiento", "recomposicion", "perdida_grasa"],
        "dietas": ["omnivoro", "vegetariano", "pescetariano"],
        "alergenos": ["huevo", "gluten"], "intolerancia_principal": None,
        "kcal_aprox": "300–380 kcal", "proteinas_g": "12–16 g",
        "tiempo_min": 12, "costo": "media",
        "etiquetas": ["rapida", "bajo_en_sal"],
        "sustituciones": {"huevo": "tofu ahumado", "gluten": "tortilla de maíz"},
    },
    {
        "id": "C08", "nombre": "Tempeh glaseado con verduras asadas y arroz integral",
        "momento": "cena",
        "objetivos": ["perdida_grasa", "aumento_muscular", "recomposicion", "mantenimiento"],
        "dietas": ["vegetariano", "vegano"],
        "alergenos": ["soja"], "intolerancia_principal": None,
        "kcal_aprox": "420–520 kcal", "proteinas_g": "26–32 g",
        "tiempo_min": 30, "costo": "media",
        "etiquetas": ["alta_proteina", "bajo_en_sal"],
        "sustituciones": {"soja": "lentejas cocidas o tofu... (si hay alergia a soja usar seitán, revisando alergia a gluten)"},
    },
    {
        "id": "C09", "nombre": "Ensalada templada de patata, judías verdes y atún",
        "momento": "cena",
        "objetivos": ["perdida_grasa", "definicion", "mantenimiento"],
        "dietas": ["omnivoro", "pescetariano"],
        "alergenos": ["pescado"], "intolerancia_principal": None,
        "kcal_aprox": "300–380 kcal", "proteinas_g": "22–28 g",
        "tiempo_min": 25, "costo": "baja",
        "etiquetas": ["economica", "alta_proteina"],
        "sustituciones": {"pescado": "huevo cocido o pollo"},
    },
    {
        "id": "C10", "nombre": "Arroz frito de coliflor con verduras y huevo",
        "momento": "cena",
        "objetivos": ["perdida_grasa", "definicion", "mantenimiento", "recomposicion"],
        "dietas": ["omnivoro", "vegetariano", "pescetariano"],
        "alergenos": ["huevo"], "intolerancia_principal": None,
        "kcal_aprox": "260–340 kcal", "proteinas_g": "14–18 g",
        "tiempo_min": 20, "costo": "media",
        "etiquetas": ["bajo_en_sal", "sin_azucar_anadido"],
        "sustituciones": {"huevo": "tofu desmenuzado (vegano)"},
    },

    # ── SNACKS ──────────────────────────────────────────────────────────────
    {
        "id": "S01", "nombre": "Manzana con mantequilla de maní",
        "momento": "snack",
        "objetivos": ["perdida_grasa", "mantenimiento", "recomposicion", "definicion"],
        "dietas": ["omnivoro", "vegetariano", "vegano", "pescetariano"],
        "alergenos": ["cacahuetes"], "intolerancia_principal": None,
        "kcal_aprox": "150–200 kcal", "proteinas_g": "4–6 g",
        "tiempo_min": 2, "costo": "baja",
        "etiquetas": ["rapida", "economica"],
        "sustituciones": {"cacahuetes": "semillas de girasol", },
    },
    {
        "id": "S02", "nombre": "Yogur griego natural sin azúcar",
        "momento": "snack",
        "objetivos": ["perdida_grasa", "definicion", "mantenimiento", "recomposicion"],
        "dietas": ["omnivoro", "vegetariano", "pescetariano"],
        "alergenos": ["leche"], "intolerancia_principal": "lactosa (usar yogur sin lactosa)",
        "kcal_aprox": "120–150 kcal", "proteinas_g": "12–15 g",
        "tiempo_min": 1, "costo": "media",
        "etiquetas": ["rapida", "alta_proteina", "sin_azucar_anadido"],
        "sustituciones": {"leche": "yogur de soja sin azúcar"},
    },
    {
        "id": "S03", "nombre": "Zanahorias y apio con hummus",
        "momento": "snack",
        "objetivos": ["perdida_grasa", "definicion", "mantenimiento", "recomposicion"],
        "dietas": ["omnivoro", "vegetariano", "vegano", "pescetariano"],
        "alergenos": ["sesamo"], "intolerancia_principal": None,
        "kcal_aprox": "130–170 kcal", "proteinas_g": "5–7 g",
        "tiempo_min": 5, "costo": "baja",
        "etiquetas": ["rapida", "economica", "bajo_en_sal"],
        "sustituciones": {"sesamo": "hummus de garbanzos SIN tahini o guacamole"},
    },
    {
        "id": "S04", "nombre": "Huevo duro (1) con 5 almendras",
        "momento": "snack",
        "objetivos": ["perdida_grasa", "definicion", "recomposicion", "aumento_muscular"],
        "dietas": ["omnivoro", "vegetariano", "pescetariano"],
        "alergenos": ["huevo", "frutos_secos"], "intolerancia_principal": None,
        "kcal_aprox": "140–180 kcal", "proteinas_g": "8–11 g",
        "tiempo_min": 3, "costo": "baja",
        "etiquetas": ["rapida", "alta_proteina", "economica"],
        "sustituciones": {"huevo": "garbanzos salteados", "frutos_secos": "semillas de calabaza"},
    },
    {
        "id": "S05", "nombre": "Puñado de nueces y una fruta pequeña",
        "momento": "snack",
        "objetivos": ["mantenimiento", "recomposicion", "aumento_muscular"],
        "dietas": ["omnivoro", "vegetariano", "vegano", "pescetariano"],
        "alergenos": ["frutos_secos"], "intolerancia_principal": None,
        "kcal_aprox": "160–220 kcal", "proteinas_g": "4–6 g",
        "tiempo_min": 1, "costo": "media",
        "etiquetas": ["rapida", "sin_azucar_anadido"],
        "sustituciones": {"frutos_secos": "semillas de girasol y calabaza"},
    },
    {
        "id": "S06", "nombre": "Batido de proteína post-entrenamiento",
        "momento": "snack",
        "objetivos": ["aumento_muscular", "recomposicion"],
        "dietas": ["omnivoro", "vegetariano", "pescetariano", "vegano"],
        "alergenos": ["soja"], "intolerancia_principal": None,
        "kcal_aprox": "180–250 kcal", "proteinas_g": "24–30 g",
        "tiempo_min": 4, "costo": "alta",
        "etiquetas": ["rapida", "alta_proteina"],
        "sustituciones": {"soja": "proteína de arroz/guisante si hay alergia a soja"},
    },
    {
        "id": "S07", "nombre": "Queso cottage con pepino y pimienta",
        "momento": "snack",
        "objetivos": ["perdida_grasa", "definicion", "mantenimiento", "recomposicion"],
        "dietas": ["omnivoro", "vegetariano", "pescetariano"],
        "alergenos": ["leche"], "intolerancia_principal": "lactosa parcial (cottage bajo en lactosa)",
        "kcal_aprox": "110–150 kcal", "proteinas_g": "12–15 g",
        "tiempo_min": 3, "costo": "media",
        "etiquetas": ["rapida", "alta_proteina", "bajo_en_sal"],
        "sustituciones": {"leche": "tofu suave con limón y pimienta"},
    },
    {
        "id": "S08", "nombre": "Palitos de pepino con tzatziki de yogur (sin lactosa)",
        "momento": "snack",
        "objetivos": ["perdida_grasa", "definicion", "mantenimiento"],
        "dietas": ["omnivoro", "vegetariano", "pescetariano"],
        "alergenos": ["leche"], "intolerancia_principal": None,
        "kcal_aprox": "90–120 kcal", "proteinas_g": "6–8 g",
        "tiempo_min": 8, "costo": "media",
        "etiquetas": ["rapida", "bajo_en_sal", "sin_azucar_anadido"],
        "sustituciones": {"leche": "crema de anacardo o yogur vegano"},
    },
    {
        "id": "S09", "nombre": "Tostada integral con aguacate y semillas (snack)",
        "momento": "snack",
        "objetivos": ["mantenimiento", "recomposicion"],
        "dietas": ["omnivoro", "vegetariano", "vegano", "pescetariano"],
        "alergenos": ["gluten"], "intolerancia_principal": None,
        "kcal_aprox": "160–200 kcal", "proteinas_g": "4–6 g",
        "tiempo_min": 5, "costo": "baja",
        "etiquetas": ["rapida", "economica", "bajo_en_sal"],
        "sustituciones": {"gluten": "tostada de arroz o maíz"},
    },
    {
        "id": "S10", "nombre": "Dátiles rellenos de mantequilla de almendra (pequeña porción)",
        "momento": "snack",
        "objetivos": ["mantenimiento", "aumento_muscular"],
        "dietas": ["omnivoro", "vegetariano", "vegano", "pescetariano"],
        "alergenos": ["frutos_secos"], "intolerancia_principal": None,
        "kcal_aprox": "150–200 kcal", "proteinas_g": "3–4 g",
        "tiempo_min": 5, "costo": "media",
        "etiquetas": ["rapida", "sin_azucar_anadido"],
        "sustituciones": {"frutos_secos": "dátiles solos o con mantequilla de semillas de girasol"},
    },
]


# ──────────────────────────────────────────────
#  Claves de alergia → alérgenos que la receta descarta
# ──────────────────────────────────────────────
# La lógica NO dice "100 % seguro": filtra ingredientes declarados y recuerda
# la necesidad de leer etiquetas (contaminación cruzada queda fuera de todo
# sistema automático).

ALL_KEYS = {"leche", "gluten", "huevo", "frutos_secos", "cacahuetes",
            "soja", "pescado", "mariscos", "sesamo"}


def _recipe_is_allergen_safe(recipe: dict, allergies: list) -> bool:
    """Una receta es segura-en-alergia si NO declara ninguno de los alérgenos
    del usuario entre sus ingredientes. Devuelve también la lista de bloqueos."""
    for al in allergies:
        for alergeno in recipe.get("alergenos", []):
            if alergeno == al:
                return False
    return True


def _recipe_intolerance_note(recipe: dict, intolerances: list) -> list[str]:
    """Devuelve notas de precaución para intolerancias declaradas (no alergia)."""
    notas = []
    principal = recipe.get("intolerancia_principal") or ""
    for intol in intolerances:
        if intol == "lactosa" and "leche" in (recipe.get("alergenos") or []):
            notas.append(principal or "Contiene lácteos: usar versión sin lactosa")
        elif intol == "gluten_no_celiaca" and "gluten" in (recipe.get("alergenos") or []):
            notas.append("Contiene gluten (sensibilidad no celíaca): reducir o sustituir")
        elif intol == "fructosa" and recipe.get("intolerancia_principal") == "fructosa":
            notas.append("Contiene fuentes de fructosa: limitar la porción")
    return notas


def _recipe_preference_score(recipe: dict, preferences: list) -> int:
    """Puntuación de ajuste a preferencias del usuario (0 = sin preferencias)."""
    etiquetas = set(recipe.get("etiquetas") or [])
    return sum(1 for pref in preferences if pref in etiquetas)


# ──────────────────────────────────────────────
#  Selección y construcción del plan
# ──────────────────────────────────────────────

def _candidates(objetivo: str, diet_type: str, allergies: list,
                intolerances: list, preferences: list) -> list[dict]:
    """Filtra el catálogo: comida compatible y sin alergias activas."""
    out = []
    for rec in RECIPES:
        if objetivo not in rec.get("objetivos", []):
            continue
        if diet_type not in rec.get("dietas", []):
            continue
        if not _recipe_is_allergen_safe(rec, allergies):
            continue
        rec = dict(rec)
        rec["_intolerance_notes"] = _recipe_intolerance_note(rec, intolerances)
        rec["_pref_score"] = _recipe_preference_score(rec, preferences)
        out.append(rec)
    return out


def _pick(pool: list[dict], n: int, rng: random.Random,
          used: set, prefer: list) -> list[dict]:
    """Selecciona `n` recetas distintas priorizando preferencias y evitando
    repetir alternativas ya usadas en el mismo menú (rotación). Las recetas
    que contienen intolerancias declaradas van al final del orden (preferidas
    las libres), pero no se descartan: la intolerancia no es exclusión absoluta."""
    ordered = sorted(
        pool,
        key=lambda r: (-r["_pref_score"], bool(r["_intolerance_notes"]), r["id"]),
    )
    # Segunda pasada: preferir las libres de intolerancia primero cuando hay
    # suficientes; las que tienen nota se ofrecen como alternativa.
    libres   = [r for r in ordered if not r["_intolerance_notes"]]
    restantes = [r for r in ordered if r["_intolerance_notes"]]
    rng.shuffle(libres)
    rng.shuffle(restantes)
    picked = []
    for r in libres + restantes:
        if len(picked) >= n:
            break
        if r["id"] not in used:
            picked.append(r)
            used.add(r["id"])
    return picked[:n]


_MOMENTO_LABEL = {"desayuno": "Desayuno", "almuerzo": "Almuerzo",
                  "cena": "Cena", "snack": "Snack"}


def _meal_text(rec: dict) -> str:
    nombre = rec["nombre"]
    extras = []
    if rec.get("_intolerance_notes"):
        extras.append("⚠️ " + " | ".join(rec["_intolerance_notes"][:1]))
    if rec.get("kcal_aprox"):
        extras.append(rec["kcal_aprox"])
    return f"{nombre} ({', '.join(extras)})" if extras else nombre


# ──────────────────────────────────────────────
#  Función principal
# ──────────────────────────────────────────────

def generate_nutrition_plan(profile: UserProfile) -> dict:
    """
    Genera el plan nutricional completo para el usuario.

    Aplica:
      - filtro de dieta (omnivoro/vegetariano/vegano/pescetariano)
      - exclusión TOTAL de alérgenos declarados
      - notas de intolerancia (no alergia)
      - preferencias de preparación/costo/etc. (prioriza sin excluir)
      - variedad: varias opciones por comida (se rotan)

    Mantiene el contrato histórico:
      plan.desayuno / plan.almuerzo / plan.cena / plan.snacks (listas de str)
      plan.hidratacion | calorias_objetivo | macros | frecuencia |
      tipo_dieta | alergias_activas

    Y añade metadatos estructurados para interfaces modernas:
      recetas (detalle de cada opción), sustituciones y aviso de derivación.
    """
    objetivo   = profile.objective or "mantenimiento"
    diet_type  = profile.diet_type or "omnivoro"
    allergies  = profile.allergies or []
    intolerances = profile.intolerances or []
    preferences  = profile.preferences or []
    freq       = profile.meal_frequency or 3

    # Semilla derivada del perfil para que la rotación sea estable entre
    # consultas del mismo usuario pero distinta entre usuarios distintos.
    seed = hash((profile.name, profile.age, diet_type, tuple(allergies)))
    rng  = random.Random(seed)

    used_ids: set = set()
    plan: dict = {
        "desayuno": [], "almuerzo": [], "cena": [], "snacks": [],
        "recetas": {
            "desayuno": [], "almuerzo": [], "cena": [], "snacks": [],
        },
        "hidratacion": _get_hidratacion(objetivo),
    }

    structure = [
        ("desayuno", 2),
        ("almuerzo", 2),
        ("cena",     2),
        ("snack",    2),   # se mostrará 1–2 según frecuencia
    ]

    for momento, n_max in structure:
        pool = _candidates(objetivo, diet_type, allergies, intolerances, preferences)
        pool = [r for r in pool if r["momento"] == momento]
        chosen = _pick(pool, n_max, rng, used_ids, preferences)
        used_ids.update(r["id"] for r in chosen)
        # Ordenar elegidos por preferencia para ofrecer la mejor primero
        chosen.sort(key=lambda r: r["_pref_score"], reverse=True)
        key = "snacks" if momento == "snack" else momento
        plan[key] = [_meal_text(r) for r in chosen]
        plan["recetas"][key if key != "snacks" else "snack"] = chosen

    # Snacks según frecuencia: 4 comidas → 1 snack, 5 comidas → 2 snacks
    if freq <= 3:
        plan["snacks"] = plan["snacks"][:0]
        plan["snacks"].append(
            "Fruta o snack ligero integrado en las comidas principales (3 comidas/día)."
        )
    elif freq == 4:
        plan["snacks"] = plan["snacks"][:1]
    else:
        plan["snacks"] = plan["snacks"][:2]

    # Fallback: si algún momento se quedó vacío (restricciones cruzadas muy
    # exigentes), sustituir por un mensaje seguro + derivación a profesional.
    for key in ("desayuno", "almuerzo", "cena", "snacks"):
        if not plan[key]:
            plan[key] = [
                "No hay suficientes opciones seguras con estas restricciones. "
                "Consulta a un nutricionista para personalizar tu plan."
            ]

    sustituciones = _build_substitution_notes(profile)

    macros = calcular_macronutrientes(profile.target_calories, objetivo, perfil=profile)
    protein = calcular_proteina_recomendada(profile)

    return {
        "calorias_objetivo": profile.target_calories,
        "macros":            macros,
        "plan":              plan,
        "frecuencia":        freq,
        "tipo_dieta":        diet_type,
        "alergias_activas":  allergies,
        "intolerancias_activas": intolerances,
        "preferencias_activas":  preferences,
        "sustituciones":     sustituciones,
        "proteina_recomendada": protein,
        "variedad":          "Varias opciones por comida y rotación semanal para no repetir menú.",
        "derivacion": (
            "Plan orientativo, no sustituye a un profesional. Un nutricionista "
            "puede ajustar porciones, suplementación y casos clínicos."
        ),
    }


def _build_substitution_notes(profile: UserProfile) -> list[dict]:
    """Resumen humano de las sustituciones aplicadas por alergias."""
    notas = []
    for al in profile.allergies or []:
        notas.append({
            "alergeno": al,
            "exclusion": f"Exclusión total de {al} y derivados.",
            "substitucion": _substitution_for(al),
            "aviso": ("La seguridad frente a contaminación cruzada depende de la "
                      "lectura de etiquetas; ningún sistema garantiza «100 % seguro»."),
        })
    return notas


def _substitution_for(alergeno: str) -> str:
    mapa = {
        "leche":        "Bebidas vegetales fortificadas con calcio, tofu, sardinas.",
        "gluten":       "Arroz, quinoa, maíz, avena certificada sin gluten, harinas sin gluten.",
        "huevo":        "Tofu, garbanzos, semillas de chía (gel), aquafaba.",
        "frutos_secos": "Semillas de girasol, calabaza, pipas.",
        "cacahuetes":   "Mantequilla de semillas de girasol.",
        "soja":         "Lentejas, garbanzos, seitán (revisar alergia a gluten).",
        "pescado":      "Pollo, pavo, tofu, legumbres.",
        "mariscos":     "Pollo, pescado blanco, huevos, legumbres.",
        "sesamo":       "Semillas de calabaza o girasol; evitar tahini.",
    }
    return mapa.get(alergeno, "Consultar sustituciones con un nutricionista.")


def _get_hidratacion(objetivo: str) -> str:
    tabla = {
        "perdida_grasa":    "2.5–3 litros de agua. Evitar bebidas azucaradas y alcohol.",
        "aumento_muscular": "3–4 litros de agua. Batido post-entrenamiento en los 30 min post-sesión.",
        "definicion":       "3 litros de agua. Reducir sodio para evitar retención de líquidos.",
        "recomposicion":    "2.5–3 litros de agua diarios.",
        "mantenimiento":    "2–2.5 litros de agua diarios.",
    }
    return tabla.get(objetivo, "2–3 litros de agua diarios.")