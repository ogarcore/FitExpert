"""
training.py
===========
Rutinas de entrenamiento — v2.0

Genera microciclos SEMANALES por días específicos, respetando:
  - Ventanas de recuperación de 48-72h por grupo muscular
  - Filtros de lesiones (rodilla, lumbar, hombro)
  - Filtros de equipamiento (mancuernas, bandas, calistenia)
  - Restricciones biomecánicas por edad e IMC
  - Variedad en la selección de ejercicios
"""

import random
from user_profile import UserProfile


# ──────────────────────────────────────────────
#  Biblioteca de Ejercicios con variantes seguras
# ──────────────────────────────────────────────

# Formato: (nombre, series×reps, músculo objetivo, [lesiones_contraindicadas], [equipamiento_requerido])
# lesiones_contraindicadas: si el usuario tiene esa lesión, se excluye este ejercicio
# equipamiento_requerido: [] = solo peso corporal

EXERCISE_LIBRARY = {

    # ── PIERNAS (CUÁDRICEPS / GLÚTEOS) ───────────────────────────────────────

    "sentadilla_libre":        ("Sentadilla libre con barra",         "4×10",  "Cuádriceps/Glúteos", ["lumbar", "rodilla"], ["barra"]),
    "prensa_piernas":          ("Prensa de piernas",                  "4×12",  "Cuádriceps/Glúteos", [],                   ["maquina"]),
    "sentadilla_goblet":       ("Sentadilla goblet con mancuerna",    "3×12",  "Cuádriceps/Glúteos", ["rodilla"],          ["mancuernas"]),
    "sentadilla_corporal":     ("Sentadilla con peso corporal",       "4×15",  "Cuádriceps/Glúteos", ["rodilla"],          []),
    "zancada_estatica":        ("Zancada estática",                   "3×10c/lado", "Cuádriceps/Glúteos", ["rodilla"],     []),
    "extension_piernas":       ("Extensión de piernas en máquina",    "4×15",  "Cuádriceps",         [],                   ["maquina"]),
    "sentadilla_bulgara":      ("Sentadilla búlgara",                 "3×10c/lado", "Cuádriceps/Glúteos", ["rodilla"],     ["mancuernas"]),
    "hipthrust_barra":         ("Hip thrust con barra",               "4×12",  "Glúteos",            ["lumbar"],           ["barra"]),
    "hipthrust_corporal":      ("Hip thrust con peso corporal",       "4×15",  "Glúteos",            [],                   []),
    "puente_gluteo":           ("Puente de glúteos",                  "4×15",  "Glúteos",            [],                   []),

    # ── ISQUIOTIBIALES ───────────────────────────────────────────────────────

    "peso_muerto":             ("Peso muerto convencional",           "4×8",   "Isquiotibiales/Espalda", ["lumbar"],       ["barra"]),
    "curl_femoral":            ("Curl femoral en máquina",            "4×12",  "Isquiotibiales",     [],                   ["maquina"]),
    "peso_muerto_rumano":      ("Peso muerto rumano con mancuernas",  "4×10",  "Isquiotibiales",     ["lumbar"],           ["mancuernas"]),
    "nordic_curl":             ("Nordic curl (curl nórdico)",         "3×6",   "Isquiotibiales",     ["rodilla"],          []),
    "sentadilla_sumo":         ("Sentadilla sumo",                    "4×12",  "Isquiotibiales/Aductores", ["rodilla"],    []),

    # ── PECHO ─────────────────────────────────────────────────────────────────

    "press_banca_barra":       ("Press de banca con barra",           "4×8",   "Pecho",              ["hombro"],           ["barra"]),
    "press_banca_mancuernas":  ("Press de banca con mancuernas",      "4×10",  "Pecho",              ["hombro"],           ["mancuernas"]),
    "flexiones":               ("Flexiones de brazos",                "4×12",  "Pecho/Tríceps",      ["hombro"],           []),
    "flexiones_inclinadas":    ("Flexiones inclinadas",               "3×12",  "Pecho bajo",         ["hombro"],           []),
    "aperturas_mancuernas":    ("Aperturas con mancuernas",           "3×12",  "Pecho",              ["hombro"],           ["mancuernas"]),
    "fondos_pecho":            ("Fondos en paralelas (inclinado)",    "3×10",  "Pecho",              ["hombro"],           []),
    "press_cable":             ("Press en cable cruzado",             "3×15",  "Pecho",              ["hombro"],           ["maquina"]),

    # ── ESPALDA ───────────────────────────────────────────────────────────────

    "remo_barra":              ("Remo con barra",                     "4×8",   "Espalda media",      ["lumbar"],           ["barra"]),
    "remo_mancuerna":          ("Remo con mancuerna a una mano",      "4×10c/lado", "Espalda/Bíceps", [],                 ["mancuernas"]),
    "jalon_polea":             ("Jalón al pecho en polea",            "4×12",  "Dorsal",             [],                   ["maquina"]),
    "dominadas":               ("Dominadas",                          "4×max", "Dorsal/Bíceps",      ["hombro"],           ["barra_dominadas"]),
    "remo_corporal":           ("Remo invertido (con mesa o barra baja)", "4×10", "Espalda media",  [],                   []),
    "facepull":                ("Face pull en polea",                 "3×15",  "Romboides/Rotadores", [],                ["maquina"]),
    "remo_banda":              ("Remo con banda elástica",            "4×12",  "Espalda media",      [],                   ["bandas_elasticas"]),

    # ── HOMBROS ───────────────────────────────────────────────────────────────

    "press_militar":           ("Press militar con barra",            "4×8",   "Hombros",            ["hombro"],           ["barra"]),
    "press_mancuernas_hombro": ("Press de hombros con mancuernas",    "4×10",  "Hombros",            ["hombro"],           ["mancuernas"]),
    "elevaciones_laterales":   ("Elevaciones laterales con mancuernas","3×15", "Deltoides lateral",  ["hombro"],           ["mancuernas"]),
    "rotacion_externa":        ("Rotación externa con banda",         "3×15",  "Manguito rotador",   [],                   ["bandas_elasticas"]),
    "elevacion_frontal":       ("Elevación frontal con mancuerna",    "3×12",  "Deltoides anterior", ["hombro"],           ["mancuernas"]),
    "press_arnold":            ("Press Arnold",                       "4×10",  "Hombros completo",   ["hombro"],           ["mancuernas"]),

    # ── BÍCEPS ────────────────────────────────────────────────────────────────

    "curl_barra":              ("Curl de bíceps con barra",           "4×10",  "Bíceps",             [],                   ["barra"]),
    "curl_mancuernas":         ("Curl de mancuernas alternado",       "4×10c/lado", "Bíceps",         [],                ["mancuernas"]),
    "curl_martillo":           ("Curl martillo con mancuernas",       "3×12",  "Bíceps/Braquial",    [],                   ["mancuernas"]),
    "curl_banda":              ("Curl de bíceps con banda elástica",  "4×12",  "Bíceps",             [],                   ["bandas_elasticas"]),

    # ── TRÍCEPS ───────────────────────────────────────────────────────────────

    "press_frances":           ("Press francés con barra",            "3×10",  "Tríceps",            [],                   ["barra"]),
    "extension_triceps":       ("Extensión de tríceps en polea",      "4×12",  "Tríceps",            [],                   ["maquina"]),
    "fondos_triceps":          ("Fondos en banco para tríceps",       "4×12",  "Tríceps",            ["hombro"],           []),
    "kickback_triceps":        ("Kickback de tríceps con mancuerna",  "3×12",  "Tríceps",            [],                   ["mancuernas"]),

    # ── CORE ──────────────────────────────────────────────────────────────────

    "plancha":                 ("Plancha abdominal",                  "3×45s", "Core",               [],                   []),
    "crunch":                  ("Crunch abdominal",                   "3×20",  "Abdomen",            ["lumbar"],           []),
    "plancha_lateral":         ("Plancha lateral",                    "3×30sc/lado", "Oblicuos",     [],                  []),
    "elevacion_piernas":       ("Elevación de piernas colgando",      "3×12",  "Abdomen bajo",       ["lumbar"],           []),
    "mountain_climbers":       ("Mountain climbers",                  "3×30",  "Core/Cardio",        ["rodilla"],          []),
    "dead_bug":                ("Dead bug",                           "3×12c/lado", "Core profundo", [],                  []),
    "rueda_abdominal":         ("Rueda abdominal (rollout)",          "3×10",  "Core",               ["lumbar"],           []),

    # ── CARDIO / FUNCIONAL ────────────────────────────────────────────────────

    "jumping_jacks":           ("Jumping jacks",                      "3×40",  "Cardio",             ["rodilla"],          []),
    "saltos_cuerda":           ("Saltos a la cuerda",                 "3×2min", "Cardio",            ["rodilla"],          []),
    "bicicleta_estatica":      ("Bicicleta estática",                 "20 min", "Cardio bajo impacto", [],                ["maquina"]),
    "remo_maquina":            ("Remo en máquina",                    "15 min", "Cardio/Espalda",    [],                  ["maquina"]),
    "caminata_inclinada":      ("Caminata en cinta a 10% inclinación","25 min", "Cardio bajo impacto", [],               ["maquina"]),
    "burpees":                 ("Burpees",                            "3×10",  "Cardio",             ["rodilla", "lumbar"], []),

    # ── MOVILIDAD / SARCOPENIA ────────────────────────────────────────────────

    "movilidad_cadera":        ("Rotaciones de cadera",               "2×10c/lado", "Movilidad",     [],                  []),
    "stretching_isquiotibiales":("Estiramiento isquiotibiales",       "3×30s", "Flexibilidad",      [],                   []),
    "equilibrio_unilateral":   ("Equilibrio unipodal",                "3×20s c/lado", "Equilibrio",  [],                 []),
    "sentadilla_asistida":     ("Sentadilla asistida (con apoyo)",    "3×10",  "Funcional",          [],                   []),
    "marcha_elevada":          ("Marcha con elevación de rodillas",   "3×20",  "Funcional",          [],                   []),
    "flexion_pared":           ("Flexión contra la pared",            "3×12",  "Pecho/Funcional",    [],                   []),
}


# ──────────────────────────────────────────────
#  Helpers de filtrado
# ──────────────────────────────────────────────

def _pick_exercises(keys: list, profile: UserProfile, n: int = 5) -> list:
    """
    Selecciona n ejercicios de la lista dada, filtrando por lesiones y equipamiento.
    Garantiza variedad usando selección aleatoria sin repetición.
    """
    injuries  = profile.injuries or []
    equipment = profile.equipment or []
    place     = profile.training_place

    # En gimnasio, las máquinas siempre están disponibles
    available_equipment = list(equipment)
    if place == "gimnasio":
        available_equipment += ["maquina", "barra", "mancuernas", "barra_dominadas"]

    safe = []
    for key in keys:
        if key not in EXERCISE_LIBRARY:
            continue
        name, reps, muscle, contraindications, required_eq = EXERCISE_LIBRARY[key]

        # Filtro de lesiones
        if any(inj in contraindications for inj in injuries):
            continue

        # Filtro de equipamiento (si se requiere algo específico, debe estar disponible)
        if required_eq and not any(eq in available_equipment for eq in required_eq):
            continue

        safe.append((name, reps, muscle))

    # Selección aleatoria sin repetición para garantizar variedad
    random.shuffle(safe)
    return safe[:n]


def _apply_biomechanical_filters(exercises_keys: list, profile: UserProfile) -> list:
    """Elimina ejercicios contraindicados por restricciones biomecánicas de edad/IMC."""
    age = profile.age
    imc = profile.imc

    # Adultos mayores o niños: no pliometría ni cargas pesadas
    if age > 70 or age < 16:
        forbidden = ["jumping_jacks", "saltos_cuerda", "burpees", "sentadilla_libre",
                     "peso_muerto", "press_banca_barra", "press_militar",
                     "nordic_curl", "fondos_pecho"]
        return [k for k in exercises_keys if k not in forbidden]

    # Obesidad mórbida: no impacto en rodillas
    if imc >= 40:
        forbidden = ["jumping_jacks", "saltos_cuerda", "burpees", "nordic_curl",
                     "mountain_climbers"]
        return [k for k in exercises_keys if k not in forbidden]

    return exercises_keys


# ──────────────────────────────────────────────
#  Plantillas de microciclos semanales
#  Formato: lista de dicts {dia, grupo, ejercicios_keys, es_descanso}
# ──────────────────────────────────────────────

WEEKLY_TEMPLATES = {

    # 3 días / semana — Full Body
    "full_body_3d": [
        {"dia": "Lunes",    "grupo": "Cuerpo Completo",  "keys": [
            "sentadilla_corporal", "prensa_piernas", "sentadilla_goblet",
            "press_banca_mancuernas", "flexiones", "aperturas_mancuernas",
            "remo_mancuerna", "jalon_polea", "remo_corporal",
            "curl_mancuernas", "curl_banda", "fondos_triceps", "kickback_triceps",
            "plancha", "dead_bug", "crunch",
        ], "descanso": False},
        {"dia": "Martes",   "grupo": "Descanso Activo",  "keys": [], "descanso": True},
        {"dia": "Miércoles","grupo": "Cuerpo Completo",  "keys": [
            "hipthrust_corporal", "puente_gluteo", "zancada_estatica",
            "flexiones_inclinadas", "fondos_pecho", "press_cable",
            "remo_banda", "facepull", "remo_corporal",
            "curl_martillo", "curl_banda", "extension_triceps", "fondos_triceps",
            "plancha_lateral", "mountain_climbers", "elevacion_piernas",
        ], "descanso": False},
        {"dia": "Jueves",   "grupo": "Descanso Activo",  "keys": [], "descanso": True},
        {"dia": "Viernes",  "grupo": "Cuerpo Completo + Cardio", "keys": [
            "sentadilla_bulgara", "hipthrust_corporal",
            "flexiones", "aperturas_mancuernas",
            "jalon_polea", "remo_mancuerna",
            "press_mancuernas_hombro", "elevaciones_laterales",
            "curl_mancuernas", "kickback_triceps",
            "plancha", "crunch", "caminata_inclinada",
        ], "descanso": False},
        {"dia": "Sábado",   "grupo": "Descanso",         "keys": [], "descanso": True},
        {"dia": "Domingo",  "grupo": "Descanso",         "keys": [], "descanso": True},
    ],

    # 4 días — Push / Pull / Legs / Full
    "ppl_4d": [
        {"dia": "Lunes",    "grupo": "Empuje (Pecho · Hombros · Tríceps)", "keys": [
            "press_banca_barra", "press_banca_mancuernas", "flexiones", "flexiones_inclinadas", "fondos_pecho",
            "press_militar", "press_mancuernas_hombro", "elevaciones_laterales", "elevacion_frontal",
            "extension_triceps", "fondos_triceps", "kickback_triceps", "press_frances",
        ], "descanso": False},
        {"dia": "Martes",   "grupo": "Jalón (Espalda · Bíceps)", "keys": [
            "remo_barra", "remo_mancuerna", "jalon_polea", "dominadas", "remo_banda", "facepull",
            "curl_barra", "curl_mancuernas", "curl_martillo", "curl_banda",
        ], "descanso": False},
        {"dia": "Miércoles","grupo": "Descanso Activo",  "keys": [], "descanso": True},
        {"dia": "Jueves",   "grupo": "Piernas (Cuádriceps · Isquiotibiales · Glúteos)", "keys": [
            "sentadilla_libre", "prensa_piernas", "sentadilla_goblet", "sentadilla_bulgara",
            "zancada_estatica", "extension_piernas",
            "peso_muerto_rumano", "curl_femoral", "nordic_curl",
            "hipthrust_barra", "hipthrust_corporal", "puente_gluteo",
        ], "descanso": False},
        {"dia": "Viernes",  "grupo": "Cuerpo Completo + Core", "keys": [
            "flexiones", "remo_corporal", "sentadilla_corporal",
            "press_mancuernas_hombro", "curl_mancuernas", "fondos_triceps",
            "plancha", "plancha_lateral", "dead_bug", "crunch", "elevacion_piernas",
        ], "descanso": False},
        {"dia": "Sábado",   "grupo": "Cardio / Descanso activo", "keys": [
            "bicicleta_estatica", "caminata_inclinada", "remo_maquina",
        ], "descanso": True},
        {"dia": "Domingo",  "grupo": "Descanso completo", "keys": [], "descanso": True},
    ],

    # 5-6 días — PPL doble
    "ppl_6d": [
        {"dia": "Lunes",    "grupo": "Empuje A (Pecho · Tríceps)", "keys": [
            "press_banca_barra", "press_banca_mancuernas", "aperturas_mancuernas", "flexiones_inclinadas",
            "extension_triceps", "fondos_triceps", "press_frances", "kickback_triceps",
        ], "descanso": False},
        {"dia": "Martes",   "grupo": "Jalón A (Espalda ancha · Bíceps)", "keys": [
            "dominadas", "jalon_polea", "remo_barra", "remo_mancuerna", "facepull",
            "curl_barra", "curl_mancuernas", "curl_martillo",
        ], "descanso": False},
        {"dia": "Miércoles","grupo": "Piernas A (Cuádriceps · Glúteos)", "keys": [
            "sentadilla_libre", "prensa_piernas", "sentadilla_bulgara", "extension_piernas",
            "hipthrust_barra", "puente_gluteo", "zancada_estatica",
        ], "descanso": False},
        {"dia": "Jueves",   "grupo": "Empuje B (Hombros · Pecho alto)", "keys": [
            "press_militar", "press_arnold", "elevaciones_laterales", "elevacion_frontal",
            "flexiones", "fondos_pecho", "press_cable",
        ], "descanso": False},
        {"dia": "Viernes",  "grupo": "Jalón B (Espalda media · Romboides)", "keys": [
            "remo_barra", "remo_banda", "facepull", "remo_corporal",
            "curl_banda", "curl_martillo",
        ], "descanso": False},
        {"dia": "Sábado",   "grupo": "Piernas B (Isquiotibiales · Core)", "keys": [
            "peso_muerto", "peso_muerto_rumano", "curl_femoral", "nordic_curl", "sentadilla_sumo",
            "plancha", "plancha_lateral", "elevacion_piernas", "dead_bug", "rueda_abdominal",
        ], "descanso": False},
        {"dia": "Domingo",  "grupo": "Descanso completo", "keys": [], "descanso": True},
    ],

    # Movilidad (adultos mayores >70 o menores de 16)
    "movilidad_3d": [
        {"dia": "Lunes",    "grupo": "Movilidad y Fuerza Suave", "keys": [
            "movilidad_cadera", "sentadilla_asistida", "flexion_pared",
            "marcha_elevada", "equilibrio_unilateral", "stretching_isquiotibiales",
            "puente_gluteo", "dead_bug", "plancha", "rotacion_externa",
        ], "descanso": False},
        {"dia": "Martes",   "grupo": "Descanso activo (caminata)", "keys": [], "descanso": True},
        {"dia": "Miércoles","grupo": "Movilidad y Coordinación", "keys": [
            "marcha_elevada", "equilibrio_unilateral", "movilidad_cadera",
            "flexion_pared", "plancha_lateral", "stretching_isquiotibiales",
            "hipthrust_corporal", "sentadilla_asistida", "remo_banda",
        ], "descanso": False},
        {"dia": "Jueves",   "grupo": "Descanso activo", "keys": [], "descanso": True},
        {"dia": "Viernes",  "grupo": "Funcional + Equilibrio", "keys": [
            "sentadilla_asistida", "flexion_pared", "puente_gluteo",
            "dead_bug", "equilibrio_unilateral", "marcha_elevada",
            "remo_banda", "curl_banda", "rotacion_externa",
        ], "descanso": False},
        {"dia": "Sábado",   "grupo": "Descanso", "keys": [], "descanso": True},
        {"dia": "Domingo",  "grupo": "Descanso", "keys": [], "descanso": True},
    ],

    # Casa avanzado — 5 días
    "casa_avanzado_5d": [
        {"dia": "Lunes",    "grupo": "Empuje (Pecho · Hombros · Tríceps)", "keys": [
            "flexiones", "flexiones_inclinadas", "fondos_pecho", "aperturas_mancuernas",
            "press_mancuernas_hombro", "elevaciones_laterales", "press_arnold",
            "fondos_triceps", "kickback_triceps", "extension_triceps",
        ], "descanso": False},
        {"dia": "Martes",   "grupo": "Jalón (Espalda · Bíceps)", "keys": [
            "dominadas", "remo_corporal", "remo_mancuerna", "remo_banda",
            "curl_mancuernas", "curl_martillo", "curl_banda",
        ], "descanso": False},
        {"dia": "Miércoles","grupo": "Piernas A", "keys": [
            "sentadilla_corporal", "sentadilla_goblet", "sentadilla_bulgara",
            "zancada_estatica", "hipthrust_corporal", "puente_gluteo",
        ], "descanso": False},
        {"dia": "Jueves",   "grupo": "Descanso activo + Core", "keys": [
            "plancha", "plancha_lateral", "dead_bug", "mountain_climbers",
            "elevacion_piernas", "rueda_abdominal",
        ], "descanso": False},
        {"dia": "Viernes",  "grupo": "Cuerpo completo + Cardio", "keys": [
            "flexiones", "remo_corporal", "sentadilla_corporal",
            "hipthrust_corporal", "fondos_triceps", "curl_banda",
            "bicicleta_estatica", "caminata_inclinada",
        ], "descanso": False},
        {"dia": "Sábado",   "grupo": "Descanso", "keys": [], "descanso": True},
        {"dia": "Domingo",  "grupo": "Descanso", "keys": [], "descanso": True},
    ],
}


# ──────────────────────────────────────────────
#  Selector de plantilla
# ──────────────────────────────────────────────

def _select_template(profile: UserProfile) -> tuple[str, str, str]:
    """
    Selecciona la plantilla de microciclo adecuada según el perfil.
    Retorna (template_key, nombre_rutina, tipo_rutina)
    """
    age  = profile.age
    imc  = profile.imc
    exp  = profile.experience
    place = profile.training_place

    # Restricciones biomecánicas primero
    if age > 70 or age < 16 or imc >= 40:
        return ("movilidad_3d",
                "Rutina de Movilidad y Fuerza Funcional",
                "Movilidad · Prevención · Bajo impacto")

    # Casa
    if place == "casa":
        if exp in ("intermedio", "avanzado"):
            return ("casa_avanzado_5d",
                    "Split Avanzado en Casa — 5 días",
                    "Calistenia y mancuernas (Push/Pull/Legs)")
        else:
            return ("full_body_3d",
                    "Circuito Cuerpo Completo en Casa — 3 días",
                    "Full Body (principiante)")

    # Gimnasio
    if exp == "principiante":
        return ("full_body_3d",
                "Full Body Gimnasio — 3 días",
                "Full Body (principiante)")
    elif exp == "intermedio":
        return ("ppl_4d",
                "Split Push · Pull · Legs — 4 días",
                "PPL (intermedio)")
    else:
        return ("ppl_6d",
                "Split PPL Doble — 6 días",
                "PPL doble frecuencia (avanzado)")


# ──────────────────────────────────────────────
#  Función principal
# ──────────────────────────────────────────────

def generate_training_plan(profile: UserProfile) -> dict:
    """
    Genera el microciclo semanal completo para el usuario.

    Aplica:
      - Filtros biomecánicos por edad e IMC
      - Filtros de lesiones
      - Filtros de equipamiento
      - Selección aleatoria para garantizar variedad

    Retorna un dict con el microciclo completo por días.
    """
    template_key, nombre, tipo = _select_template(profile)
    template = WEEKLY_TEMPLATES[template_key]

    semana = []
    exercises_per_session = 5 if profile.experience == "principiante" else 6

    for day_config in template:
        dia      = day_config["dia"]
        grupo    = day_config["grupo"]
        keys     = day_config["keys"]
        descanso = day_config["descanso"]

        if descanso or not keys:
            semana.append({
                "dia":        dia,
                "grupo":      grupo,
                "descanso":   True,
                "ejercicios": [],
                "duracion":   "—",
                "descanso_entre_series": "—",
                "nota":       "Caminata ligera o stretching opcional (20–30 min)." if "activo" in grupo.lower() else "Descanso completo. Prioriza el sueño y la hidratación.",
            })
            continue

        # Aplicar filtros biomecánicos y seleccionar ejercicios
        filtered_keys = _apply_biomechanical_filters(keys, profile)
        ejercicios    = _pick_exercises(filtered_keys, profile, n=exercises_per_session)

        # Duración estimada según experiencia
        if profile.experience == "principiante":
            duracion  = "45–55 minutos"
            descanso_s = "60–90 seg entre series"
        elif profile.experience == "intermedio":
            duracion  = "55–70 minutos"
            descanso_s = "90–120 seg entre series"
        else:
            duracion  = "70–90 minutos"
            descanso_s = "2–3 min en compuestos | 60–90 seg en aislamiento"

        semana.append({
            "dia":        dia,
            "grupo":      grupo,
            "descanso":   False,
            "ejercicios": ejercicios,   # lista de (nombre, series×reps, músculo)
            "duracion":   duracion,
            "descanso_entre_series": descanso_s,
            "nota":       _get_session_note(grupo, profile),
        })

    dias_entrenamiento = sum(1 for d in semana if not d["descanso"])

    return {
        "nombre":   nombre,
        "tipo":     tipo,
        "dias":     f"{dias_entrenamiento} días de entrenamiento / semana",
        "semana":   semana,
        # Retrocompatibilidad con campos anteriores
        "sesiones": [d for d in semana if not d["descanso"]],
        "cardio_extra": _get_cardio_recommendation(profile),
        "notas": _get_general_notes(profile),
    }


def _get_session_note(grupo: str, profile: UserProfile) -> str:
    if "Empuje" in grupo:
        return "Calienta el manguito rotador antes de empezar. Movilidad de hombros 5 min."
    elif "Jalón" in grupo or "Pull" in grupo:
        return "Activa la espalda con remo light en polea antes de las series de trabajo."
    elif "Pierna" in grupo:
        return "Calienta con sentadillas corporales 2×15 y movilidad de cadera."
    elif "Core" in grupo:
        return "Ejecuta los ejercicios de core al final de la sesión, con técnica perfecta."
    elif "Movilidad" in grupo:
        return "Trabaja lento y controlado. La movilidad mejora con constancia, no con intensidad."
    return "Respeta los tiempos de descanso. La recuperación es parte del entrenamiento."


def _get_cardio_recommendation(profile: UserProfile) -> str:
    if profile.objective in ("perdida_grasa", "definicion"):
        return "2–3 sesiones semanales de cardio moderado (30–45 min): bicicleta, caminata inclinada o elíptica."
    elif profile.objective == "aumento_muscular":
        return "1–2 sesiones suaves de cardio (20 min) para salud cardiovascular sin comprometer la recuperación."
    elif profile.age > 70 or profile.age < 16:
        return "Caminatas diarias de 20–30 minutos a ritmo cómodo."
    return "2 sesiones de cardio moderado (25–35 min) por semana para mantenimiento cardiovascular."


def _get_general_notes(profile: UserProfile) -> str:
    notes = []
    if "lumbar" in profile.injuries:
        notes.append("Lesión lumbar: sentadilla libre y peso muerto reemplazados por alternativas seguras.")
    if "rodilla" in profile.injuries:
        notes.append("Lesión de rodilla: sentadillas profundas eliminadas; usar extensión en máquina.")
    if "hombro" in profile.injuries:
        notes.append("Lesión de hombro: ejercicios overhead eliminados; priorizar rotación externa.")
    if profile.age > 70:
        notes.append("Rutina adaptada para adulto mayor: sin impacto articular, énfasis en prevención de sarcopenia.")
    if profile.age < 16:
        notes.append("Menor de edad: sin cargas pesadas. Solo calistenia, movilidad y coordinación.")
    if profile.imc >= 40:
        notes.append("Obesidad mórbida: eliminados ejercicios pliométricos para proteger las rodillas.")
    if not notes:
        notes.append("Aplica sobrecarga progresiva: aumenta peso o repeticiones cada 2–3 semanas.")
    return " | ".join(notes)
