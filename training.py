"""
training.py
===========
Rutinas de entrenamiento — v3.0 (auditoría completa)

Genera microciclos SEMANALES por días específicos, respetando:
  - Ventanas de recuperación de 48-72h por grupo muscular
  - Matriz de lesiones: cada lesión declara qué ejercicios excluye,
    qué movimientos conviene evitar y qué alternativas seguras la cubren
  - Filtro de equipamiento (mancuernas, bandas, calistenia…)
  - Restricciones biomecánicas por edad e IMC
  - Variedad en la selección de ejercicios

Cambios respecto a v2:
  - EXERCISE_LIBRARY pasa de tuplas a registros estructurados con
    metadata (músculo, impacto, equipamiento, lesiones contraindicadas y
    alternativa segura por ejercicio).
  - Matriz de lesiones INJURY_MATRIX cubre las 10 zonas de INJURY_OPTIONS
    (lumbar, cervical, rodilla, hombro, codo, muñeca, tobillo, cadera,
    dolor general, movilidad reducida).
  - Corrección de orden en la recomendación de cardio: la edad/estado se
    evalúa ANTES que el objetivo (un menor o un adulto mayor no recibe una
    recomendación de "déficit" solo por tener ese objetivo).
  - Blindaje de seguridad: si hay banderas rojas (dolor torácico, mareo…)
    o una lesión aguda en curso, el plan NO genera ejercicios: devuelve una
    guía de consulta profesional (coherente con las reglas SEG-RF-*).
  - Trazabilidad: el plan expone en `alternativas_aplicadas` cada
    sustitución de ejercicio por lesión, para explicar las decisiones.
"""

import random
from user_profile import UserProfile


# ──────────────────────────────────────────────
#  Biblioteca de Ejercicios (registros estructurados)
# ──────────────────────────────────────────────
# Campos:
#   nombre     — nombre legible
#   series     — series × reps (texto)
#   musculo    — grupos musculares objetivo
#   impacto    — alto | medio | bajo  (carga articular)
#   lesiones   — zonas de INJURY_OPTIONS contraindicadas para este ejercicio
#   equipamiento — equipamiento requerido ([] = solo peso corporal)
#   alternativa— clave del ejercicio sustituto seguro si hay lesión

EXERCISE_LIBRARY: dict = {

    # ── PIERNAS (CUÁDRICEPS / GLÚTEOS) ───────────────────────────────────────

    "sentadilla_libre": {
        "nombre": "Sentadilla libre con barra", "series": "4×10",
        "musculo": "Cuádriceps/Glúteos", "impacto": "alto",
        "lesiones": ["lumbar", "rodilla", "tobillo", "cadera", "dolor_general"],
        "equipamiento": ["barra"], "alternativa": "sentadilla_goblet",
    },
    "prensa_piernas": {
        "nombre": "Prensa de piernas", "series": "4×12",
        "musculo": "Cuádriceps/Glúteos", "impacto": "medio",
        "lesiones": ["rodilla", "tobillo", "dolor_general", "movilidad"],
        "equipamiento": ["maquina"], "alternativa": "sentadilla_corporal",
    },
    "sentadilla_goblet": {
        "nombre": "Sentadilla goblet con mancuerna", "series": "3×12",
        "musculo": "Cuádriceps/Glúteos", "impacto": "medio",
        "lesiones": ["rodilla", "tobillo", "dolor_general"],
        "equipamiento": ["mancuernas"], "alternativa": "sentadilla_corporal",
    },
    "sentadilla_corporal": {
        "nombre": "Sentadilla con peso corporal", "series": "4×15",
        "musculo": "Cuádriceps/Glúteos", "impacto": "bajo",
        "lesiones": ["rodilla", "dolor_general", "movilidad"],
        "equipamiento": [], "alternativa": "sentadilla_asistida",
    },
    "zancada_estatica": {
        "nombre": "Zancada estática", "series": "3×10c/lado",
        "musculo": "Cuádriceps/Glúteos", "impacto": "medio",
        "lesiones": ["rodilla", "tobillo", "cadera", "dolor_general"],
        "equipamiento": [], "alternativa": "puente_gluteo",
    },
    "extension_piernas": {
        "nombre": "Extensión de piernas en máquina", "series": "4×15",
        "musculo": "Cuádriceps", "impacto": "medio",
        "lesiones": ["rodilla", "dolor_general"],
        "equipamiento": ["maquina"], "alternativa": "puente_gluteo",
    },
    "sentadilla_bulgara": {
        "nombre": "Sentadilla búlgara", "series": "3×10c/lado",
        "musculo": "Cuádriceps/Glúteos", "impacto": "alto",
        "lesiones": ["rodilla", "tobillo", "cadera", "dolor_general", "movilidad"],
        "equipamiento": ["mancuernas"], "alternativa": "sentadilla_goblet",
    },
    "hipthrust_barra": {
        "nombre": "Hip thrust con barra", "series": "4×12",
        "musculo": "Glúteos", "impacto": "medio",
        "lesiones": ["lumbar", "cadera", "dolor_general"],
        "equipamiento": ["barra"], "alternativa": "hipthrust_corporal",
    },
    "hipthrust_corporal": {
        "nombre": "Hip thrust con peso corporal", "series": "4×15",
        "musculo": "Glúteos", "impacto": "bajo",
        "lesiones": ["lumbar", "cadera", "dolor_general"],
        "equipamiento": [], "alternativa": "puente_gluteo",
    },
    "puente_gluteo": {
        "nombre": "Puente de glúteos", "series": "4×15",
        "musculo": "Glúteos", "impacto": "bajo",
        "lesiones": ["lumbar", "cadera"],
        "equipamiento": [], "alternativa": "dead_bug",
    },

    # ── ISQUIOTIBIALES ───────────────────────────────────────────────────────

    "peso_muerto": {
        "nombre": "Peso muerto convencional", "series": "4×8",
        "musculo": "Isquiotibiales/Espalda", "impacto": "alto",
        "lesiones": ["lumbar", "cervical", "dolor_general", "movilidad"],
        "equipamiento": ["barra"], "alternativa": "peso_muerto_rumano",
    },
    "curl_femoral": {
        "nombre": "Curl femoral en máquina", "series": "4×12",
        "musculo": "Isquiotibiales", "impacto": "bajo",
        "lesiones": ["rodilla", "dolor_general"],
        "equipamiento": ["maquina"], "alternativa": "puente_gluteo",
    },
    "peso_muerto_rumano": {
        "nombre": "Peso muerto rumano con mancuernas", "series": "4×10",
        "musculo": "Isquiotibiales", "impacto": "medio",
        "lesiones": ["lumbar", "cervical", "dolor_general"],
        "equipamiento": ["mancuernas"], "alternativa": "curl_femoral",
    },
    "nordic_curl": {
        "nombre": "Nordic curl (curl nórdico)", "series": "3×6",
        "musculo": "Isquiotibiales", "impacto": "medio",
        "lesiones": ["rodilla", "tobillo", "dolor_general"],
        "equipamiento": [], "alternativa": "curl_femoral",
    },
    "sentadilla_sumo": {
        "nombre": "Sentadilla sumo", "series": "4×12",
        "musculo": "Isquiotibiales/Aductores", "impacto": "alto",
        "lesiones": ["rodilla", "tobillo", "cadera", "dolor_general"],
        "equipamiento": [], "alternativa": "sentadilla_corporal",
    },

    # ── PECHO ─────────────────────────────────────────────────────────────────

    "press_banca_barra": {
        "nombre": "Press de banca con barra", "series": "4×8",
        "musculo": "Pecho", "impacto": "alto",
        "lesiones": ["hombro", "codo", "muneca", "cervical", "dolor_general"],
        "equipamiento": ["barra"], "alternativa": "press_banca_mancuernas",
    },
    "press_banca_mancuernas": {
        "nombre": "Press de banca con mancuernas", "series": "4×10",
        "musculo": "Pecho", "impacto": "medio",
        "lesiones": ["hombro", "codo", "muneca", "dolor_general"],
        "equipamiento": ["mancuernas"], "alternativa": "flexiones_inclinadas",
    },
    "flexiones": {
        "nombre": "Flexiones de brazos", "series": "4×12",
        "musculo": "Pecho/Tríceps", "impacto": "medio",
        "lesiones": ["hombro", "codo", "muneca", "dolor_general"],
        "equipamiento": [], "alternativa": "flexiones_inclinadas",
    },
    "flexiones_inclinadas": {
        "nombre": "Flexiones inclinadas", "series": "3×12",
        "musculo": "Pecho bajo", "impacto": "bajo",
        "lesiones": ["hombro", "codo", "muneca"],
        "equipamiento": [], "alternativa": "flexion_pared",
    },
    "aperturas_mancuernas": {
        "nombre": "Aperturas con mancuernas", "series": "3×12",
        "musculo": "Pecho", "impacto": "bajo",
        "lesiones": ["hombro", "dolor_general"],
        "equipamiento": ["mancuernas"], "alternativa": "flexiones_inclinadas",
    },
    "fondos_pecho": {
        "nombre": "Fondos en paralelas (inclinado)", "series": "3×10",
        "musculo": "Pecho", "impacto": "alto",
        "lesiones": ["hombro", "codo", "muneca", "dolor_general"],
        "equipamiento": [], "alternativa": "press_banca_mancuernas",
    },
    "press_cable": {
        "nombre": "Press en cable cruzado", "series": "3×15",
        "musculo": "Pecho", "impacto": "bajo",
        "lesiones": ["hombro", "dolor_general"],
        "equipamiento": ["maquina"], "alternativa": "flexiones_inclinadas",
    },

    # ── ESPALDA ───────────────────────────────────────────────────────────────

    "remo_barra": {
        "nombre": "Remo con barra", "series": "4×8",
        "musculo": "Espalda media", "impacto": "alto",
        "lesiones": ["lumbar", "cervical", "muneca", "dolor_general", "movilidad"],
        "equipamiento": ["barra"], "alternativa": "remo_mancuerna",
    },
    "remo_mancuerna": {
        "nombre": "Remo con mancuerna a una mano", "series": "4×10c/lado",
        "musculo": "Espalda/Bíceps", "impacto": "medio",
        "lesiones": ["lumbar", "hombro", "dolor_general"],
        "equipamiento": ["mancuernas"], "alternativa": "remo_banda",
    },
    "jalon_polea": {
        "nombre": "Jalón al pecho en polea", "series": "4×12",
        "musculo": "Dorsal", "impacto": "bajo",
        "lesiones": ["hombro", "codo", "muneca", "dolor_general"],
        "equipamiento": ["maquina"], "alternativa": "remo_banda",
    },
    "dominadas": {
        "nombre": "Dominadas", "series": "4×max",
        "musculo": "Dorsal/Bíceps", "impacto": "alto",
        "lesiones": ["hombro", "codo", "muneca", "cervical", "dolor_general"],
        "equipamiento": ["barra_dominadas"], "alternativa": "jalon_polea",
    },
    "remo_corporal": {
        "nombre": "Remo invertido (con mesa o barra baja)", "series": "4×10",
        "musculo": "Espalda media", "impacto": "bajo",
        "lesiones": ["hombro", "muneca", "dolor_general"],
        "equipamiento": [], "alternativa": "remo_banda",
    },
    "facepull": {
        "nombre": "Face pull en polea", "series": "3×15",
        "musculo": "Romboides/Rotadores", "impacto": "bajo",
        "lesiones": ["hombro", "cervical", "dolor_general"],
        "equipamiento": ["maquina"], "alternativa": "rotacion_externa",
    },
    "remo_banda": {
        "nombre": "Remo con banda elástica", "series": "4×12",
        "musculo": "Espalda media", "impacto": "bajo",
        "lesiones": ["hombro", "dolor_general"],
        "equipamiento": ["bandas_elasticas"], "alternativa": "remo_corporal",
    },

    # ── HOMBROS ───────────────────────────────────────────────────────────────

    "press_militar": {
        "nombre": "Press militar con barra", "series": "4×8",
        "musculo": "Hombros", "impacto": "alto",
        "lesiones": ["hombro", "cervical", "codo", "muneca", "dolor_general"],
        "equipamiento": ["barra"], "alternativa": "press_mancuernas_hombro",
    },
    "press_mancuernas_hombro": {
        "nombre": "Press de hombros con mancuernas", "series": "4×10",
        "musculo": "Hombros", "impacto": "medio",
        "lesiones": ["hombro", "cervical", "dolor_general"],
        "equipamiento": ["mancuernas"], "alternativa": "elevaciones_laterales",
    },
    "elevaciones_laterales": {
        "nombre": "Elevaciones laterales con mancuernas", "series": "3×15",
        "musculo": "Deltoides lateral", "impacto": "bajo",
        "lesiones": ["hombro", "dolor_general"],
        "equipamiento": ["mancuernas"], "alternativa": "rotacion_externa",
    },
    "rotacion_externa": {
        "nombre": "Rotación externa con banda", "series": "3×15",
        "musculo": "Manguito rotador", "impacto": "bajo",
        "lesiones": ["hombro", "dolor_general"],
        "equipamiento": ["bandas_elasticas"], "alternativa": "facepull",
    },
    "elevacion_frontal": {
        "nombre": "Elevación frontal con mancuerna", "series": "3×12",
        "musculo": "Deltoides anterior", "impacto": "bajo",
        "lesiones": ["hombro", "cervical", "dolor_general"],
        "equipamiento": ["mancuernas"], "alternativa": "rotacion_externa",
    },
    "press_arnold": {
        "nombre": "Press Arnold", "series": "4×10",
        "musculo": "Hombros completo", "impacto": "medio",
        "lesiones": ["hombro", "cervical", "dolor_general"],
        "equipamiento": ["mancuernas"], "alternativa": "elevaciones_laterales",
    },

    # ── BÍCEPS ────────────────────────────────────────────────────────────────

    "curl_barra": {
        "nombre": "Curl de bíceps con barra", "series": "4×10",
        "musculo": "Bíceps", "impacto": "bajo",
        "lesiones": ["codo", "muneca", "dolor_general"],
        "equipamiento": ["barra"], "alternativa": "curl_mancuernas",
    },
    "curl_mancuernas": {
        "nombre": "Curl de mancuernas alternado", "series": "4×10c/lado",
        "musculo": "Bíceps", "impacto": "bajo",
        "lesiones": ["codo", "muneca", "dolor_general"],
        "equipamiento": ["mancuernas"], "alternativa": "curl_banda",
    },
    "curl_martillo": {
        "nombre": "Curl martillo con mancuernas", "series": "3×12",
        "musculo": "Bíceps/Braquial", "impacto": "bajo",
        "lesiones": ["codo", "muneca", "dolor_general"],
        "equipamiento": ["mancuernas"], "alternativa": "curl_banda",
    },
    "curl_banda": {
        "nombre": "Curl de bíceps con banda elástica", "series": "4×12",
        "musculo": "Bíceps", "impacto": "bajo",
        "lesiones": ["codo", "dolor_general"],
        "equipamiento": ["bandas_elasticas"], "alternativa": "remo_banda",
    },

    # ── TRÍCEPS ───────────────────────────────────────────────────────────────

    "press_frances": {
        "nombre": "Press francés con barra", "series": "3×10",
        "musculo": "Tríceps", "impacto": "medio",
        "lesiones": ["codo", "hombro", "dolor_general"],
        "equipamiento": ["barra"], "alternativa": "extension_triceps",
    },
    "extension_triceps": {
        "nombre": "Extensión de tríceps en polea", "series": "4×12",
        "musculo": "Tríceps", "impacto": "bajo",
        "lesiones": ["codo", "hombro", "dolor_general"],
        "equipamiento": ["maquina"], "alternativa": "kickback_triceps",
    },
    "fondos_triceps": {
        "nombre": "Fondos en banco para tríceps", "series": "4×12",
        "musculo": "Tríceps", "impacto": "medio",
        "lesiones": ["hombro", "codo", "muneca", "dolor_general"],
        "equipamiento": [], "alternativa": "extension_triceps",
    },
    "kickback_triceps": {
        "nombre": "Kickback de tríceps con mancuerna", "series": "3×12",
        "musculo": "Tríceps", "impacto": "bajo",
        "lesiones": ["codo", "muneca", "dolor_general"],
        "equipamiento": ["mancuernas"], "alternativa": "extension_triceps",
    },

    # ── CORE ──────────────────────────────────────────────────────────────────

    "plancha": {
        "nombre": "Plancha abdominal", "series": "3×45s",
        "musculo": "Core", "impacto": "bajo",
        "lesiones": ["lumbar", "cervical", "muneca", "dolor_general"],
        "equipamiento": [], "alternativa": "dead_bug",
    },
    "crunch": {
        "nombre": "Crunch abdominal", "series": "3×20",
        "musculo": "Abdomen", "impacto": "bajo",
        "lesiones": ["lumbar", "cervical", "dolor_general"],
        "equipamiento": [], "alternativa": "plancha",
    },
    "plancha_lateral": {
        "nombre": "Plancha lateral", "series": "3×30sc/lado",
        "musculo": "Oblicuos", "impacto": "bajo",
        "lesiones": ["hombro", "codo", "lumbar", "dolor_general"],
        "equipamiento": [], "alternativa": "dead_bug",
    },
    "elevacion_piernas": {
        "nombre": "Elevación de piernas colgando", "series": "3×12",
        "musculo": "Abdomen bajo", "impacto": "bajo",
        "lesiones": ["lumbar", "hombro", "dolor_general"],
        "equipamiento": [], "alternativa": "dead_bug",
    },
    "mountain_climbers": {
        "nombre": "Mountain climbers", "series": "3×30",
        "musculo": "Core/Cardio", "impacto": "alto",
        "lesiones": ["rodilla", "hombro", "muneca", "dolor_general"],
        "equipamiento": [], "alternativa": "marcha_elevada",
    },
    "dead_bug": {
        "nombre": "Dead bug", "series": "3×12c/lado",
        "musculo": "Core profundo", "impacto": "bajo",
        "lesiones": ["lumbar", "dolor_general"],
        "equipamiento": [], "alternativa": "plancha",
    },
    "rueda_abdominal": {
        "nombre": "Rueda abdominal (rollout)", "series": "3×10",
        "musculo": "Core", "impacto": "alto",
        "lesiones": ["lumbar", "hombro", "muneca", "dolor_general", "movilidad"],
        "equipamiento": [], "alternativa": "dead_bug",
    },

    # ── CARDIO / FUNCIONAL ────────────────────────────────────────────────────

    "jumping_jacks": {
        "nombre": "Jumping jacks", "series": "3×40",
        "musculo": "Cardio", "impacto": "alto",
        "lesiones": ["rodilla", "tobillo", "dolor_general"],
        "equipamiento": [], "alternativa": "marcha_elevada",
    },
    "saltos_cuerda": {
        "nombre": "Saltos a la cuerda", "series": "3×2min",
        "musculo": "Cardio", "impacto": "alto",
        "lesiones": ["rodilla", "tobillo", "dolor_general"],
        "equipamiento": [], "alternativa": "bicicleta_estatica",
    },
    "bicicleta_estatica": {
        "nombre": "Bicicleta estática", "series": "20 min",
        "musculo": "Cardio bajo impacto", "impacto": "bajo",
        "lesiones": ["rodilla", "tobillo", "dolor_general"],
        "equipamiento": ["maquina"], "alternativa": "caminata_inclinada",
    },
    "remo_maquina": {
        "nombre": "Remo en máquina", "series": "15 min",
        "musculo": "Cardio/Espalda", "impacto": "bajo",
        "lesiones": ["lumbar", "rodilla", "dolor_general"],
        "equipamiento": ["maquina"], "alternativa": "marcha_elevada",
    },
    "caminata_inclinada": {
        "nombre": "Caminata en cinta a 10% inclinación", "series": "25 min",
        "musculo": "Cardio bajo impacto", "impacto": "bajo",
        "lesiones": ["rodilla", "dolor_general", "movilidad"],
        "equipamiento": ["maquina"], "alternativa": "marcha_elevada",
    },
    "burpees": {
        "nombre": "Burpees", "series": "3×10",
        "musculo": "Cardio", "impacto": "alto",
        "lesiones": ["rodilla", "lumbar", "hombro", "muneca", "dolor_general"],
        "equipamiento": [], "alternativa": "marcha_elevada",
    },

    # ── MOVILIDAD / SARCOPENIA ────────────────────────────────────────────────

    "movilidad_cadera": {
        "nombre": "Rotaciones de cadera", "series": "2×10c/lado",
        "musculo": "Movilidad", "impacto": "bajo",
        "lesiones": ["cadera", "dolor_general"],
        "equipamiento": [], "alternativa": "marcha_elevada",
    },
    "stretching_isquiotibiales": {
        "nombre": "Estiramiento isquiotibiales", "series": "3×30s",
        "musculo": "Flexibilidad", "impacto": "bajo",
        "lesiones": ["lumbar", "dolor_general"],
        "equipamiento": [], "alternativa": "movilidad_cadera",
    },
    "equilibrio_unilateral": {
        "nombre": "Equilibrio unipodal", "series": "3×20s c/lado",
        "musculo": "Equilibrio", "impacto": "bajo",
        "lesiones": ["tobillo", "rodilla", "dolor_general", "movilidad"],
        "equipamiento": [], "alternativa": "sentadilla_asistida",
    },
    "sentadilla_asistida": {
        "nombre": "Sentadilla asistida (con apoyo)", "series": "3×10",
        "musculo": "Funcional", "impacto": "bajo",
        "lesiones": ["rodilla", "dolor_general", "movilidad"],
        "equipamiento": [], "alternativa": "puente_gluteo",
    },
    "marcha_elevada": {
        "nombre": "Marcha con elevación de rodillas", "series": "3×20",
        "musculo": "Funcional", "impacto": "bajo",
        "lesiones": ["rodilla", "tobillo", "dolor_general"],
        "equipamiento": [], "alternativa": "movilidad_cadera",
    },
    "flexion_pared": {
        "nombre": "Flexión contra la pared", "series": "3×12",
        "musculo": "Pecho/Funcional", "impacto": "bajo",
        "lesiones": ["hombro", "codo", "muneca"],
        "equipamiento": [], "alternativa": "rotacion_externa",
    },
}


# ──────────────────────────────────────────────
#  Matriz de lesiones (INJURY_MATRIX)
# ──────────────────────────────────────────────
# Cubre las 10 claves de INJURY_OPTIONS. Para cada lesión:
#   nombre            — zona afectada (legible)
#   movimientos_evitar— patrones de movimiento a evitar
#   ejercicios_clave  — claves de EXERCISE_LIBRARY contraindicadas
#   alternativas      — claves seguras recomendadas en su lugar
#   consejo           — recomendación humana de precaución
#   referencia_medica — nota de derivación si la molestia persiste

INJURY_MATRIX: dict = {
    "lumbar": {
        "nombre": "Zona lumbar (espalda baja)",
        "movimientos_evitar": [
            "Flexión lumbar bajo carga (peso muerto, remo con barra)",
            "Crunch / flexiones completas del tronco",
            "Impacto (saltos, burpees)",
        ],
        "ejercicios_clave": [
            "peso_muerto", "peso_muerto_rumano", "remo_barra", "sentadilla_libre",
            "hipthrust_barra", "crunch", "elevacion_piernas", "rueda_abdominal",
            "burpees", "remo_maquina", "plancha", "plancha_lateral",
        ],
        "alternativas": ["dead_bug", "puente_gluteo", "remo_mancuerna",
                         "remo_banda", "sentadilla_corporal", "marcha_elevada"],
        "consejo": ("Prioriza la estabilidad del core (dead bug, puente de "
                    "glúteos) y evita toda flexión lumbar bajo carga hasta "
                    "resolver la molestia."),
        "referencia_medica": ("Si el dolor irradia a la pierna o persiste más "
                              "de 2 semanas, consulta a un médico."),
    },
    "cervical": {
        "nombre": "Cuello / cervical",
        "movimientos_evitar": [
            "Cargas axiales sobre la columna (sentadilla libre, press militar)",
            "Ejercicios que tensen el cuello bajo carga",
        ],
        "ejercicios_clave": ["press_militar", "peso_muerto", "dominadas",
                             "crunch", "facepull", "press_banca_barra",
                             "elevacion_frontal"],
        "alternativas": ["elevaciones_laterales", "remo_banda", "dead_bug",
                         "flexiones_inclinadas"],
        "consejo": ("Mantén la cabeza neutra durante todo el ejercicio y evita "
                    "girar el cuello mientras hay tensión."),
        "referencia_medica": ("Ante dolor cervical con hormigueo en brazos, "
                              "consulta médica."),
    },
    "rodilla": {
        "nombre": "Rodilla",
        "movimientos_evitar": [
            "Sentadillas profundas y zancadas con carga",
            "Impacto (saltos, carrera en superficies duras)",
            "Nordic curl y mountain climbers",
        ],
        "ejercicios_clave": [
            "sentadilla_libre", "sentadilla_goblet", "sentadilla_corporal",
            "sentadilla_bulgara", "zancada_estatica", "sentadilla_sumo",
            "extension_piernas", "nordic_curl", "mountain_climbers",
            "jumping_jacks", "saltos_cuerda", "burpees", "prensa_piernas",
            "equilibrio_unilateral", "marcha_elevada", "bicicleta_estatica",
            "caminata_inclinada", "sentadilla_asistida", "remo_maquina",
        ],
        "alternativas": ["puente_gluteo", "hipthrust_corporal", "dead_bug",
                         "curl_femoral"],
        "consejo": ("Refuerza cuádriceps con trabajo de cadena posterior "
                    "(glúteos) y evita el rango profundo de flexión de rodilla "
                    "hasta que la molestia ceda."),
        "referencia_medica": ("Si hay hinchazón, bloqueo o dolor nocturno, "
                              "consulta a un traumatólogo."),
    },
    "hombro": {
        "nombre": "Hombro",
        "movimientos_evitar": [
            "Elevaciones por encima de la cabeza con carga (press militar)",
            "Aperturas con carga excesiva",
            "Dominadas y fondos profundos",
        ],
        "ejercicios_clave": [
            "press_banca_barra", "press_banca_mancuernas", "press_militar",
            "press_mancuernas_hombro", "press_arnold", "elevaciones_laterales",
            "elevacion_frontal", "flexiones", "fondos_pecho", "dominadas",
            "aperturas_mancuernas", "remo_mancuerna", "jalon_polea",
            "remo_corporal", "facepull", "fondos_triceps", "plancha_lateral",
            "elevacion_piernas", "mountain_climbers", "rueda_abdominal",
            "burpees", "flexion_pared", "press_frances",
        ],
        "alternativas": ["rotacion_externa", "flexiones_inclinadas",
                         "kickback_triceps", "remo_banda", "curl_banda",
                         "curl_mancuernas", "caminata_inclinada"],
        "consejo": ("Trabaja el manguito rotador (rotación externa con banda) "
                    "antes de cualquier empuje y evita el rango doloroso."),
        "referencia_medica": ("Si el hombro cede (sensación de dislocación) o "
                              "el dolor es nocturno, consulta a un médico."),
    },
    "codo": {
        "nombre": "Codo",
        "movimientos_evitar": [
            "Flexo-extensión forzada del codo con carga máxima",
            "Curl y press con agarre en supinación dolorosa",
        ],
        "ejercicios_clave": ["press_banca_barra", "dominadas", "fondos_pecho",
                             "press_militar", "curl_barra", "curl_mancuernas",
                             "curl_martillo", "curl_banda", "press_frances",
                             "fondos_triceps", "flexiones", "jalon_polea",
                             "flexion_pared", "press_banca_mancuernas"],
        "alternativas": ["kickback_triceps", "extension_triceps", "remo_banda",
                         "facepull", "puente_gluteo"],
        "consejo": ("Prioriza la zona media del rango, sin bloquear ni forzar "
                    "la extensión; reduce la carga si aparece dolor."),
        "referencia_medica": ("El dolor de codo que persiste más de 3 semanas "
                              "(epicondilitis) merece valoración."),
    },
    "muneca": {
        "nombre": "Muñeca",
        "movimientos_evitar": [
            "Apoyo de peso sobre muñeca extendida (flexiones, plancha)",
            "Curl y press con muñeca en flexión forzada",
        ],
        "ejercicios_clave": ["flexiones", "flexiones_inclinadas", "plancha",
                             "dominadas", "press_banca_barra", "press_militar",
                             "curl_barra", "curl_mancuernas", "curl_martillo",
                             "kickback_triceps", "fondos_triceps",
                             "press_banca_mancuernas", "fondos_pecho",
                             "jalon_polea", "remo_barra", "rueda_abdominal",
                             "mountain_climbers", "burpees", "flexion_pared",
                             "remo_corporal"],
        "alternativas": ["curl_banda", "remo_banda", "dead_bug", "puente_gluteo",
                         "rotacion_externa", "marcha_elevada"],
        "consejo": ("Utiliza muñequeras de apoyo o agarres neutrales y evita "
                    "cargar sobre la muñeca en posición extendida."),
        "referencia_medica": ("Si hay hinchazón, chasquidos o pérdida de fuerza "
                              "de agarre, consulta a un médico."),
    },
    "tobillo": {
        "nombre": "Tobillo",
        "movimientos_evitar": [
            "Impacto (saltos, cuerda, burpees)",
            "Sentadillas con talón despegado y cambios de dirección bruscos",
        ],
        "ejercicios_clave": ["sentadilla_libre", "sentadilla_bulgara",
                             "sentadilla_sumo", "zancada_estatica",
                             "jumping_jacks", "saltos_cuerda", "burpees",
                             "equilibrio_unilateral", "marcha_elevada",
                             "nordic_curl", "prensa_piernas"],
        "alternativas": ["puente_gluteo", "hipthrust_corporal",
                         "bicicleta_estatica", "movilidad_cadera",
                         "curl_femoral"],
        "consejo": ("Trabajo de propiocepción y movilidad de tobillo antes de "
                    "cualquier carga; evita impacto durante la molestia."),
        "referencia_medica": ("Si hubo un esguince reciente con inestabilidad "
                              "persistente, consulta a un médico."),
    },
    "cadera": {
        "nombre": "Cadera",
        "movimientos_evitar": [
            "Flexión profunda de cadera bajo carga (sentadilla búlgara)",
            "Zancadas amplias y trabajo de aductores forzado",
        ],
        "ejercicios_clave": ["sentadilla_libre", "zancada_estatica",
                             "sentadilla_bulgara", "sentadilla_sumo",
                             "hipthrust_barra", "hipthrust_corporal",
                             "puente_gluteo", "movilidad_cadera"],
        "alternativas": ["dead_bug", "marcha_elevada", "sentadilla_asistida",
                         "equilibrio_unilateral", "stretching_isquiotibiales"],
        "consejo": ("Prioriza movilidad de cadera y estabilidad de pelvis "
                    "(dead bug) antes de trabajar rangos profundos."),
        "referencia_medica": ("El dolor de cadera lateral en adultos mayores "
                              "puede indicar bursitis: valoración médica."),
    },
    "dolor_general": {
        "nombre": "Dolor articular generalizado",
        "movimientos_evitar": [
            "Ejercicios de alto impacto y pliometría",
            "Cargas máximas y rangos extremos de movilidad",
        ],
        "ejercicios_clave": [
            "sentadilla_libre", "sentadilla_goblet", "sentadilla_corporal",
            "prensa_piernas", "zancada_estatica", "extension_piernas",
            "sentadilla_bulgara", "sentadilla_sumo", "peso_muerto",
            "peso_muerto_rumano", "nordic_curl", "curl_femoral",
            "press_banca_barra", "press_banca_mancuernas", "flexiones",
            "aperturas_mancuernas", "fondos_pecho", "remo_barra",
            "remo_mancuerna", "jalon_polea", "dominadas", "facepull",
            "press_militar", "press_mancuernas_hombro", "elevaciones_laterales",
            "elevacion_frontal", "press_arnold", "curl_barra", "curl_mancuernas",
            "curl_martillo", "curl_banda", "press_frances", "extension_triceps",
            "fondos_triceps", "kickback_triceps", "plancha", "crunch",
            "plancha_lateral", "elevacion_piernas", "mountain_climbers",
            "rueda_abdominal", "jumping_jacks", "saltos_cuerda",
            "remo_maquina", "caminata_inclinada", "burpees", "equilibrio_unilateral",
            "sentadilla_asistida", "rotacion_externa", "stretching_isquiotibiales",
        ],
        "alternativas": ["movilidad_cadera", "marcha_elevada", "dead_bug",
                         "puente_gluteo", "flexion_pared"],
        "consejo": ("Prioriza movilidad, técnica y rangos cómodos. Ante dolor "
                    "articular generalizado persistente, busca valoración "
                    "médica antes de aumentar la intensidad."),
        "referencia_medica": ("El dolor articular inflamatorio (rigidez matinal "
                              "prolongada) requiere evaluación médica."),
    },
    "movilidad": {
        "nombre": "Movilidad reducida",
        "movimientos_evitar": [
            "Ejercicios que exijan rangos profundos de partida",
            "Cargas elevadas con técnica comprometida",
        ],
        "ejercicios_clave": ["sentadilla_corporal", "prensa_piernas",
                             "sentadilla_bulgara", "peso_muerto", "remo_barra",
                             "sentadilla_libre", "rueda_abdominal",
                             "equilibrio_unilateral"],
        "alternativas": ["sentadilla_asistida", "marcha_elevada",
                         "movilidad_cadera", "flexion_pared", "dead_bug"],
        "consejo": ("Adapta los rangos con asistencia y prioriza la movilidad "
                    "articular antes de la carga."),
        "referencia_medica": ("Si la movilidad se reduce de forma súbita o "
                              "progresiva, consulta a un médico."),
    },
}


# ──────────────────────────────────────────────
#  Helpers de filtrado
# ──────────────────────────────────────────────

def _available_equipment(profile: UserProfile) -> list:
    equipment = list(profile.equipment or [])
    # En gimnasio, las máquinas siempre están disponibles
    if profile.training_place == "gimnasio":
        equipment += ["maquina", "barra", "mancuernas", "barra_dominadas"]
    return equipment


def _pick_exercises(keys: list, profile: UserProfile, n: int = 5) -> dict:
    """
    Selecciona n ejercicios de la lista dada aplicando:
      - matriz de lesiones (excluye y sustituye con alternativa segura)
      - filtro de equipamiento
      - restricciones biomecánicas de edad/IMC
      - variedad aleatoria sin repetición

    Retorna {"elegidos": [...], "alternativas": [...]} con trazabilidad.
    """
    injuries  = profile.injuries or []
    available = _available_equipment(profile)
    forbidden_age = _age_imc_forbidden_keys(profile)

    excluded_by_injury: dict = {}   # clave -> motivo
    alternatives_idx: list = []     # (sustituido, por, sustituto)

    safe_tuples = []
    for key in keys:
        if key not in EXERCISE_LIBRARY:
            continue
        entry = EXERCISE_LIBRARY[key]

        # 1) Restricciones biomecánicas de edad / IMC
        if key in forbidden_age:
            continue

        # 2) Filtro de equipamiento
        req = entry.get("equipamiento") or []
        if req and not any(eq in available for eq in req):
            continue

        # 3) Matriz de lesiones
        contraindicado = [inj for inj in injuries if inj in entry.get("lesiones", [])]
        if contraindicado:
            excluded_by_injury[key] = contraindicado[0]
            alt_key = _safe_alternative(key, injuries, available, forbidden_age)
            if alt_key and (alt_key, key) not in alternatives_idx:
                alt = EXERCISE_LIBRARY[alt_key]
                alternatives_idx.append((key, alt_key, contraindicado[0]))
                safe_tuples.append((alt["nombre"], alt["series"], alt["musculo"]))
            continue

        safe_tuples.append((entry["nombre"], entry["series"], entry["musculo"]))

    # Sin repetición y con variedad
    random.shuffle(safe_tuples)
    chosen = safe_tuples[:n]

    notas_lesion = []
    for original, sustituto, lesion in alternatives_idx:
        notas_lesion.append(
            f"«{EXERCISE_LIBRARY.get(original, {}).get('nombre', original)}» "
            f"sustituido por «{EXERCISE_LIBRARY[sustituto]['nombre']}» por tu "
            f"lesión ({_lesion_label(lesion)})."
        )

    return {"elegidos": chosen, "alternativas": notas_lesion}


def _lesion_label(lesion_key: str) -> str:
    """Nombre legible de la zona lesionada («rodilla» → «Rodilla»)."""
    entry = INJURY_MATRIX.get(lesion_key)
    if not entry:
        return lesion_key
    return entry["nombre"]


def _safe_alternative(key: str, injuries: list, available: list,
                      forbidden_age: list) -> str | None:
    """Devuelve una alternativa segura del ejercicio excluido por lesión,
    comprobando que no esté tampoco contraindicada ni exija equipamiento
    no disponible."""
    entry = EXERCISE_LIBRARY.get(key, {})
    alt_key = entry.get("alternativa")
    if not alt_key or alt_key not in EXERCISE_LIBRARY:
        return None
    alt = EXERCISE_LIBRARY[alt_key]
    if alt_key in forbidden_age:
        return None
    if any(inj in alt.get("lesiones", []) for inj in injuries):
        return None
    req = alt.get("equipamiento") or []
    if req and not any(eq in available for eq in req):
        return None
    return alt_key


# Movimientos seguros de bajo impacto usados como último recurso para que
# ninguna sesión quede vacía (lesiones múltiples o restricciones cruzadas).
FALLBACK_BASIC = ["dead_bug", "puente_gluteo", "marcha_elevada",
                  "movilidad_cadera", "flexion_pared", "sentadilla_asistida",
                  "equilibrio_unilateral", "stretching_isquiotibiales",
                  "plancha", "remo_banda", "curl_banda"]


def _age_imc_forbidden_keys(profile: UserProfile) -> set:
    """Restricciones biomecánicas por edad/IMC (sin pliometría ni cargas
    pesadas en menores, adultos mayores o IMC ≥ 40)."""
    age = profile.age
    imc = profile.imc
    forbidden = set()

    if age > 70 or 0 < age < 16 or imc >= 40:
        forbidden = {
            "jumping_jacks", "saltos_cuerda", "burpees", "sentadilla_libre",
            "peso_muerto", "press_banca_barra", "press_militar",
            "nordic_curl", "fondos_pecho", "mountain_climbers",
        }
    if imc >= 40:
        forbidden.update({"sentadilla_bulgara", "zancada_estatica"})
    return forbidden


# ──────────────────────────────────────────────
#  Plantillas de microciclos semanales
#  Formato: lista de dicts {dia, grupo, keys, descanso}
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
    Retorna (template_key, nombre_rutina, tipo_rutina).
    """
    age  = profile.age
    imc  = profile.imc
    exp  = profile.experience
    place = profile.training_place

    # Restricciones biomecánicas primero (edad / obesidad mórbida)
    if age > 70 or 0 < age < 16 or imc >= 40:
        return ("movilidad_3d",
                "Rutina de Movilidad y Fuerza Funcional",
                "Movilidad · Prevención · Bajo impacto")

    # Casa
    if place == "casa":
        if exp in ("intermedio", "avanzado"):
            return ("casa_avanzado_5d",
                    "Split Avanzado en Casa — 5 días",
                    "Calistenia y mancuernas (Push/Pull/Legs)")
        return ("full_body_3d",
                "Circuito Cuerpo Completo en Casa — 3 días",
                "Full Body (principiante)")

    # Gimnasio
    if exp == "principiante":
        return ("full_body_3d",
                "Full Body Gimnasio — 3 días",
                "Full Body (principiante)")
    if exp == "intermedio":
        return ("ppl_4d",
                "Split Push · Pull · Legs — 4 días",
                "PPL (intermedio)")
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
      - Matriz de lesiones con alternativas seguras
      - Filtros de equipamiento
      - Selección aleatoria para garantizar variedad

    Si el perfil presenta banderas rojas (dolor torácico, mareo…) o una
    lesión aguda en curso, no se generan ejercicios: se recomienda la
    consulta profesional (coherente con SEG-RF-* de la base de conocimiento).
    """
    # ── Blindaje de seguridad ─────────────────────────────────────────────
    red_flags = profile.red_flags or []
    aguda = profile.injury_severity == "aguda"
    if red_flags or aguda:
        motivo = []
        if red_flags:
            motivo.append("presencia de señales de alarma (consulta médica previa necesaria)")
        if aguda:
            motivo.append("lesión aguda en curso")
        return {
            "nombre":   "No entrenar hasta evaluación profesional",
            "tipo":     "Consulta médica · Sin ejercicio prescrito",
            "dias":     "0 días de entrenamiento / semana",
            "semana":   [{
                "dia": d, "grupo": "Evaluación médica",
                "descanso": True, "ejercicios": [],
                "duracion": "—", "descanso_entre_series": "—",
                "nota": "Consulta a un profesional de la salud antes de retomar la actividad física.",
            } for d in ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")],
            "sesiones": [],
            "cardio_extra": "Sin sesiones de cardio hasta evaluación médica.",
            "notas": (f"Plan suspendido por {', '.join(motivo)}. El sistema "
                      "no prescribe ejercicio con estas condiciones."),
            "alternativas_aplicadas": [],
            "motivo_suspension": motivo,
        }

    template_key, nombre, tipo = _select_template(profile)
    template = WEEKLY_TEMPLATES[template_key]

    semana = []
    exercises_per_session = 5 if profile.experience == "principiante" else 6
    todas_alternativas: list = []

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
                "nota": ("Caminata ligera o stretching opcional (20–30 min)."
                         if "activo" in grupo.lower()
                         else "Descanso completo. Prioriza el sueño y la hidratación."),
            })
            continue

        resultado = _pick_exercises(keys, profile, n=exercises_per_session)
        ejercicios = resultado["elegidos"]
        todas_alternativas.extend(resultado["alternativas"])

        # Nunca dejar una sesión vacía: si las restricciones excluyeron todo,
        # cubrir con movimientos seguros de bajo impacto aún disponibles
        # (FALLBACK_BASIC).
        destino_note = "sin fallback"
        if not ejercicios:
            fallback = _pick_exercises(
                FALLBACK_BASIC, profile, n=max(3, exercises_per_session - 2)
            )
            ejercicios = fallback["elegidos"]
            todas_alternativas.extend(fallback["alternativas"])
            if ejercicios:
                destino_note = (
                    "Sesión cubierta con variantes seguras de bajo impacto por tus "
                    "restricciones declaradas."
                )
            else:
                # Fallback agotado también (restricciones cruzadas extremas):
                # el día se convierte en prescripción de descanso + derivación,
                # nunca en una sesión vacía.
                semana.append({
                    "dia":        dia,
                    "grupo":      "Descanso / evaluación profesional",
                    "descanso":   True,
                    "ejercicios": [],
                    "duracion":   "—",
                    "descanso_entre_series": "—",
                    "nota": ("Tus restricciones (múltiples lesiones y limitaciones) "
                             "agotan las opciones seguras de esta sesión. Se "
                             "prescribe descanso y valoración profesional antes "
                             "de entrenar."),
                })
                continue

        # Duración estimada según experiencia
        if profile.experience == "principiante":
            duracion, descanso_s = "45–55 minutos", "60–90 seg entre series"
        elif profile.experience == "intermedio":
            duracion, descanso_s = "55–70 minutos", "90–120 seg entre series"
        else:
            duracion, descanso_s = "70–90 minutos", "2–3 min en compuestos | 60–90 seg en aislamiento"

        semana.append({
            "dia":        dia,
            "grupo":      grupo,
            "descanso":   False,
            "ejercicios": ejercicios,   # lista de (nombre, series×reps, músculo)
            "duracion":   duracion,
            "descanso_entre_series": descanso_s,
            "nota":       _get_session_note(grupo, profile) + (
                " " + destino_note if destino_note != "sin fallback" else ""
            ),
        })

    dias_entrenamiento = sum(1 for d in semana if not d["descanso"])

    # Deduplicar avisos de sustitución (pueden repetirse entre días/fallback)
    todas_alternativas = list(dict.fromkeys(todas_alternativas))

    return {
        "nombre":   nombre,
        "tipo":     tipo,
        "dias":     f"{dias_entrenamiento} días de entrenamiento / semana",
        "semana":   semana,
        # Retrocompatibilidad con campos anteriores
        "sesiones": [d for d in semana if not d["descanso"]],
        "cardio_extra": _get_cardio_recommendation(profile),
        "notas": _get_general_notes(profile),
        # Nueva trazabilidad
        "alternativas_aplicadas": todas_alternativas,
        "lesiones_consideradas": [INJURY_MATRIX.get(i, {}).get("nombre", i)
                                  for i in (profile.injuries or [])],
    }


# ──────────────────────────────────────────────
#  Notas humanizadas
# ──────────────────────────────────────────────

def _get_session_note(grupo: str, profile: UserProfile) -> str:
    if "Empuje" in grupo:
        return "Calienta el manguito rotador antes de empezar. Movilidad de hombros 5 min."
    if "Jalón" in grupo or "Pull" in grupo:
        return "Activa la espalda con remo light en polea antes de las series de trabajo."
    if "Pierna" in grupo:
        return "Calienta con sentadillas corporales 2×15 y movilidad de cadera."
    if "Core" in grupo:
        return "Ejecuta los ejercicios de core al final de la sesión, con técnica perfecta."
    if "Movilidad" in grupo:
        return "Trabaja lento y controlado. La movilidad mejora con constancia, no con intensidad."
    return "Respeta los tiempos de descanso. La recuperación es parte del entrenamiento."


def _get_cardio_recommendation(profile: UserProfile) -> str:
    """
    Recomendación de cardio. PRIMERO se evalúa edad/estado (un menor o un
    adulto mayor recibe una recomendación adaptada aunque su objetivo sea
    pérdida de grasa); DESPUÉS el objetivo. Corrección de la v2, que
    priorizaba el objetivo (auditoría: NUT-01 vs cardio en menores).
    """
    # Seguridad y edad primero
    if profile.red_flags:
        return "Ninguna sesión de cardio hasta evaluación médica."
    if profile.age > 70:
        return ("Caminatas diarias de 20–30 minutos a ritmo cómodo. Evitar "
                "esfuerzos que impidan mantener una conversación.")
    if 0 < profile.age < 16:
        return ("40–60 minutos diarios de actividad física moderada a vigorosa "
                "por día (OMS, adolescentes 5–17 años), incluyendo juego activo, "
                "no deporte competitivo de alta intensidad.")
    if profile.injury_severity == "aguda":
        return "Sin cardio hasta tratar la lesión aguda."

    # Objetivo (solo en población adulta sin señales de alarma)
    if profile.objective in ("perdida_grasa", "definicion"):
        return ("2–3 sesiones semanales de cardio moderado (30–45 min): "
                "bicicleta, caminata inclinada o elíptica.")
    if profile.objective == "aumento_muscular":
        return ("1–2 sesiones suaves de cardio (20 min) para salud "
                "cardiovascular sin comprometer la recuperación.")
    return ("2 sesiones de cardio moderado (25–35 min) por semana para "
            "mantenimiento cardiovascular.")


def _get_general_notes(profile: UserProfile) -> str:
    notes = []
    for inj in profile.injuries or []:
        entry = INJURY_MATRIX.get(inj)
        if entry:
            notes.append(f"{entry['nombre']}: {entry['consejo']}")
    if profile.injury_severity == "aguda":
        notes.append("Lesión aguda: el plan se ha suspendido; consulta profesional.")
    if profile.age > 70:
        notes.append("Rutina adaptada para adulto mayor: sin impacto articular, "
                     "énfasis en prevención de sarcopenia.")
    if 0 < profile.age < 16:
        notes.append("Menor de edad: sin cargas pesadas. Solo calistenia, "
                     "movilidad y coordinación.")
    if profile.imc >= 40:
        notes.append("Obesidad mórbida: eliminados ejercicios pliométricos para "
                     "proteger las rodillas.")
    if not notes:
        notes.append("Aplica sobrecarga progresiva: aumenta peso o repeticiones "
                     "cada 2–3 semanas.")
    return " | ".join(notes)