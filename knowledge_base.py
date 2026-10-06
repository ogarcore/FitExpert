"""
knowledge_base.py
=================
Base de conocimiento del Sistema Experto FitExpert (v2 — auditoría).

Representa el conocimiento con el modelo Objeto-Atributo-Valor mediante
reglas de producción IF-THEN evaluables sobre un `UserProfile`.

Cada regla declara:
  - id            identificador único (legibles: NUT-, TRAIN-, LES-,
                  EDAD-, SEG-, BIO-, COMP-, PREF-)
  - description   nombre corto de la regla
  - condition     callable(profile) -> bool  (la premisa IF)
  - conclusion    texto de la recomendación (THEN)
  - explanation   explicación humana del razonamiento
  - category      agrupación de presentación
  - tier          nivel en la jerarquía de seguridad (ver más abajo)
  - priority      0–100, desempate dentro del mismo tier
  - severity      critica | alta | media | baja | info
  - references    fuentes fiables (OMS, AAP, ACSM, CDC, consensos…)
  - conflicts     ids/globs de reglas que esta regla SUPRIME si ambas
                  se activan (p. ej. "NUT-01" o "TRAIN-*")
  - action        qué hace el sistema cuando la regla dispara
  - alternative   alternativa ofrecida cuando se restringe algo
  - test          descripción legible de la condición (para pruebas y
                  para el módulo de explicación: "¿qué dato la activó?")

Jerarquía de resolución de conflictos (documentada y aplicada por el
motor de inferencia), de mayor a menor precedencia:

    1. SEGURIDAD           señales de alarma, alergias, lesión aguda
    2. CONTRAINDICACIONES  lesiones/limitaciones musculoesqueléticas
    3. EDAD                menores de edad y adultos mayores
    4. CONDICIÓN FÍSICA    IMC, composición corporal, sedentarismo
    5. OBJETIVO            metas calóricas y planes de entrenamiento
    6. PREFERENCIAS        dieta y gustos del usuario
    (7. SEGUIMIENTO         consejos transversales; nunca conflictan —
                           ordenado por debajo de PREFERENCIAS)

Empate dentro del mismo tier → gana la mayor `priority`; si persiste
el empate → el id alfabéticamente menor (resultado determinista).

Referencias citadas (guías reales, sin invención):
  - OMS (2020) Directrices sobre actividad física y sedentaria.
  - OMS (2022) Obesity and overweight (clasificación IMC).
  - AAP (Academy of Pediatrics) — actividad física y lesiones en
    adolescentes; fortalecimiento muscular en jóvenes.
  - ACSM Guidelines for Exercise Testing and Prescription (11ª ed.).
  - AHA/ACC (2019) Recommendations for Preparticipation Evaluation.
  - Consenso PROT-AGE (2013, JAMDA) — proteína en adultos ≥65.
  - CDC STEADI — prevención de caídas en adultos mayores.
  - WGO (World Gastroenterology Organisation) — celiaquía.
  - NIH/NIDDK — intolerancia a la lactosa.
  - AASM/SRS — sueño en adolescentes (8–10 h) y adultos (7–9 h).
"""

from typing import NamedTuple, Callable

from user_profile import UserProfile


# ──────────────────────────────────────────────
#  Jerarquía de seguridad (resolución de conflictos)
# ──────────────────────────────────────────────

TIER_ORDER: dict[str, int] = {
    "SEGURIDAD":           0,
    "CONTRAINDICACIONES":  1,
    "EDAD":                2,
    "CONDICION_FISICA":    3,
    "OBJETIVO":            4,
    "PREFERENCIAS":        5,
    "SEGUIMIENTO":         6,   # por debajo de PREFERENCIAS; no conflicta
}

TIER_LABELS: dict[str, str] = {
    "SEGURIDAD":           "Seguridad",
    "CONTRAINDICACIONES":  "Contraindicaciones",
    "EDAD":                "Edad",
    "CONDICION_FISICA":    "Condición física",
    "OBJETIVO":            "Objetivo",
    "PREFERENCIAS":        "Preferencias",
    "SEGUIMIENTO":         "Seguimiento",
}


def tier_rank(tier: str) -> int:
    """Posición en la jerarquía (menor = mayor precedencia)."""
    return TIER_ORDER.get(tier, 99)


# ──────────────────────────────────────────────
#  Estructura de una Regla
# ──────────────────────────────────────────────

class Rule(NamedTuple):
    id:          str
    description: str
    condition:   Callable[[UserProfile], bool]
    conclusion:  str
    explanation: str
    category:    str
    # ── metadatos v2 (con valores por defecto → compatibilidad) ──
    tier:        str  = "OBJETIVO"
    priority:    int  = 50
    severity:    str  = "info"        # critica | alta | media | baja | info
    references:  tuple = ()
    conflicts:   tuple = ()           # ids/globs que esta regla suprime
    action:      str  = ""
    alternative: str  = ""
    test:        str  = ""


# ──────────────────────────────────────────────
#  Base de Conocimiento
# ──────────────────────────────────────────────

RULES: list[Rule] = [

    # ══ SEGURIDAD — señales de alarma → derivación profesional ═══════════════
    # (tier SEGURIDAD: suprime cualquier recomendación de entrenamiento)

    Rule(
        id="SEG-RF-01",
        description="Dolor torácico al esfuerzo",
        condition=lambda p: "dolor_toracico" in p.red_flags,
        conclusion=("Señal de alarma: dolor o presión en el pecho al esfuerzo. "
                    "Suspender cualquier actividad y acudir a urgencias o a un "
                    "médico antes de reanudar el ejercicio."),
        explanation=(
            "El dolor torácico provocado por el esfuerzo puede indicar isquemia "
            "cardíaca. Ningún plan de ejercicio o dieta de este sistema puede "
            "priorizarse sobre una evaluación médica urgente; por eso esta regla "
            "detiene las recomendaciones de entrenamiento y deriva a un profesional."
        ),
        category="alerta", tier="SEGURIDAD", priority=100, severity="critica",
        references=("AHA/ACC (2019) Preparticipation Evaluation",
                    "ACSM Guidelines (11ª ed.) — dolor torácico al esfuerzo"),
        conflicts=("TRAIN-*",),
        action="derivar",
        alternative=("Solo después de autorización médica: caminatas suaves en "
                     "entorno supervisado, según indicación clínica."),
        test="red_flags contiene 'dolor_toracico'",
    ),
    Rule(
        id="SEG-RF-02",
        description="Mareo o pérdida de conciencia al esfuerzo",
        condition=lambda p: "mareo_desmayo" in p.red_flags,
        conclusion=("Señal de alarma: mareos o pérdida de conciencia al esfuerzo. "
                    "Detener el ejercicio y buscar evaluación médica antes de "
                    "continuar."),
        explanation=(
            "Los síncope o mareo relacionados con el esfuerzo pueden originarse en "
            "alteraciones cardíacas o arrítmicas. El sistema suspende las reglas de "
            "entrenamiento y prioriza la derivación profesional."
        ),
        category="alerta", tier="SEGURIDAD", priority=100, severity="critica",
        references=("AHA/ACC (2019) Preparticipation Evaluation",
                    "ACSM Guidelines (11ª ed.)"),
        conflicts=("TRAIN-*",),
        action="derivar",
        alternative="Reanudar solo con autorización y plan individualizado.",
        test="red_flags contiene 'mareo_desmayo'",
    ),
    Rule(
        id="SEG-RF-03",
        description="Falta de aire en reposo",
        condition=lambda p: "falta_aire_reposo" in p.red_flags,
        conclusion=("Señal de alarma: falta de aire en reposo. Consultar al médico "
                    "antes de iniciar cualquier programa de actividad física."),
        explanation=(
            "La disnea en reposo puede asociarse a patología cardiopulmonar. Este "
            "sistema es orientativo y no diagnostica: la regla prioriza la "
            "derivación y suprime las recomendaciones de entrenamiento."
        ),
        category="alerta", tier="SEGURIDAD", priority=100, severity="critica",
        references=("OMS (2020) — actividad física y salud",
                    "ACSM Guidelines (11ª ed.)"),
        conflicts=("TRAIN-*",),
        action="derivar",
        alternative="Solo con autorización médica y evaluación cardiopulmonar.",
        test="red_flags contiene 'falta_aire_reposo'",
    ),
    Rule(
        id="SEG-RF-04",
        description="Dolor articular intenso e hinchazón sin causa aparente",
        condition=lambda p: "dolor_agudo_articular" in p.red_flags,
        conclusion=("Señal de alarma: dolor articular intenso e hinchazón sin "
                    "causa aparente. Suspender el entrenamiento y acudir al "
                    "médico; no forzar la articulación."),
        explanation=(
            "Una articulación tumefacta y muy dolorosa sin mecanismo lesional "
            "conocido puede indicar artritis aguda, infección o lesión estructural. "
            "El sistema suspende el plan y deriva, en lugar de proponer ejercicios."
        ),
        category="alerta", tier="SEGURIDAD", priority=100, severity="critica",
        references=("ACSM Guidelines (11ª ed.) — signos de alarma",
                    "American College of Rheumatology — artritis aguda"),
        conflicts=("TRAIN-*",),
        action="derivar",
        alternative="Movilidad pasiva suave solo si el profesional lo autoriza.",
        test="red_flags contiene 'dolor_agudo_articular'",
    ),
    Rule(
        id="SEG-RF-05",
        description="Debilidad progresiva o pérdida de sensibilidad",
        condition=lambda p: "debilidad_progresiva" in p.red_flags,
        conclusion=("Señal de alarma: debilidad progresiva o pérdida de "
                    "sensibilidad. Derivación neurológica antes de entrenar."),
        explanation=(
            "La debilidad progresiva o los déficits sensitivos pueden originarse "
            "en patología del sistema nervioso central o periférico. Esta regla "
            "tiene la máxima prioridad: suspende el plan y exige evaluación "
            "profesional."
        ),
        category="alerta", tier="SEGURIDAD", priority=100, severity="critica",
        references=("ACSM Guidelines (11ª ed.) — signos de alarma neurológica"),
        conflicts=("TRAIN-*",),
        action="derivar",
        alternative="Reanudar con prescripción y supervisión profesional.",
        test="red_flags contiene 'debilidad_progresiva'",
    ),
    Rule(
        id="SEG-ALG-01",
        description="Alergia alimentaria — exclusión estricta",
        condition=lambda p: len(p.allergies) >= 1,
        conclusion=("Alergia alimentaria declarada: excluir el alérgeno y todos sus "
                    "derivados del plan, verificar etiquetas en cada compra y "
                    "llevar siempre el plan de acción ante anafilaxia prescrito por "
                    "el médico."),
        explanation=(
            "Una alergia alimentaria es una reacción inmunológica que puede ser "
            "grave. El plan filtra el alérgeno, pero ningún sistema informático "
            "puede garantizar ausencia de trazas o contaminación cruzada: por eso "
            "el sistema nunca afirma que un alimento sea «100 % seguro» y recomienda "
            "verificación humana y plan de acción médico."
        ),
        category="alerta", tier="SEGURIDAD", priority=90, severity="alta",
        references=("AAAAI/ACAAI — Food Allergy: A Practice Parameter",
                    "WGO — Alergias e intolerancias alimentarias"),
        action="excluir_alergeno",
        alternative="Sustituir por fuentes alimentarias equivalentes libres del alérgeno.",
        test="allergies tiene 1 o más elementos",
    ),
    Rule(
        id="SEG-ALG-02",
        description="Alergias múltiples — derivación a nutricionista",
        condition=lambda p: len(p.allergies) >= 2,
        conclusion=("Dos o más alergias alimentarias combinadas: se recomienda "
                    "planificación con un nutricionista colegiado para asegurar "
                    "un aporte nutricional completo sin riesgo."),
        explanation=(
            "Cuando convergen varias exclusiones estrictas (p. ej. gluten + leche), "
            "el riesgo de desequilibrios nutricionales o de errores de sustitución "
            "aumenta. El sistema mantiene el plan orientativo, pero deriva la "
            "planificación final a un profesional."
        ),
        category="alerta", tier="SEGURIDAD", priority=85, severity="alta",
        references=("AAAAI/ACAAI — Food Allergy Practice Parameter",
                    "Academy of Nutrition and Dietetics — dietas de eliminación"),
        conflicts=(),
        action="derivar",
        alternative="Plan de sustituciones revisado por nutricionista.",
        test="len(allergies) >= 2",
    ),
    Rule(
        id="LES-SEV-01",
        description="Lesión aguda — suspender entrenamiento",
        condition=lambda p: p.injury_severity == "aguda",
        conclusion=("Lesión aguda o dolor intenso actual: suspender el "
                    "entrenamiento de la zona afectada y del programa intenso en "
                    "general hasta evaluación por un profesional."),
        explanation=(
            "Una lesión en fase aguda se agrava con la carga. Esta regla de tier "
            "SEGURIDAD suprime las rutinas estándar (TRAIN-*) y sustituye el plan "
            "por reposo relativo de la zona y derivación; la rehabilitación debe "
            "prescribir un fisioterapeuta o médico del deporte."
        ),
        category="alerta", tier="SEGURIDAD", priority=95, severity="critica",
        references=("ACSM Guidelines (11ª ed.) — manejo de lesiones",
                    "AAP — lesiones musculoesqueléticas en adolescentes"),
        conflicts=("TRAIN-*",),
        action="suspender",
        alternative="Movilidad suave de zonas no afectadas; retomar por indicación profesional.",
        test="injury_severity == 'aguda'",
    ),

    # ══ CONTRAINDICACIONES — matriz de lesiones ═══════════════════════════════
    # (tier CONTRAINDICACIONES: riesgo → restricción → alternativa → por qué)
    # La matriz detalle lesión → ejercicios de riesgo → músculos conservados →
    # alternativas se aplica en training.py; aquí se declara la restricción.

    Rule(
        id="LES-01",
        description="Lesión lumbar — adaptar ejercicios axiales",
        condition=lambda p: "lumbar" in p.injuries,
        conclusion=("Lesión lumbar: evitar sentadilla libre con carga y peso "
                    "muerto convencional. Alternativas: prensa de piernas, "
                    "remo en polea con espalda neutra y trabajo de core antiextensión."),
        explanation=(
            "Los ejercicios axiales someten la columna lumbar a compresión y "
            "cizallamiento elevados. Con lesión lumbar se sustituyen por ejercicios "
            "de cadena cerrada con soporte (prensa, extensión de cadera) que "
            "mantienen la musculatura del core y glúteos sin sobrecargar la vértebra "
            "lesionada."
        ),
        category="lesión", tier="CONTRAINDICACIONES", priority=80, severity="alta",
        references=("ACSM Guidelines (11ª ed.) — bajo dolor lumbar",
                    "ACSM — progresión en entrenamiento de resistencia"),
        action="restringir",
        alternative="Prensa de piernas, puente de glúteos, dead bug, remo apoyado.",
        test="'lumbar' in injuries",
    ),
    Rule(
        id="LES-02",
        description="Lesión de rodilla — evitar alto impacto y cargas profundas",
        condition=lambda p: "rodilla" in p.injuries,
        conclusion=("Lesión de rodilla: evitar sentadillas profundas con carga y "
                    "ejercicios de impacto. Alternativas: extensiones de pierna "
                    "parciales, isométricas en silla, bicicleta o elíptica sin dolor."),
        explanation=(
            "Las lesiones de rodilla (menisco, LCA, tendinopatía) se agravan con "
            "cizallamiento y flexiones profundas bajo carga. El trabajo isométrico "
            "y de cadena abierta parcial conserva el cuádriceps —clave para "
            "estabilizar la rodilla— sin forzar el rango doloroso."
        ),
        category="lesión", tier="CONTRAINDICACIONES", priority=80, severity="alta",
        references=("ACSM Guidelines (11ª ed.) — cadena cinética",
                    "AAOS — rehabilitación de rodilla"),
        action="restringir",
        alternative="Isométricas de cuádriceps, bicicleta estática, extensiones parciales.",
        test="'rodilla' in injuries",
    ),
    Rule(
        id="LES-03",
        description="Lesión de hombro — evitar press y movimientos overhead",
        condition=lambda p: "hombro" in p.injuries,
        conclusion=("Lesión de hombro: eliminar press militar y elevaciones sobre "
                    "la cabeza. Alternativas: jalón al pecho, remo en polea y "
                    "rotaciones externas con banda a 0° de abducción."),
        explanation=(
            "Los movimientos overhead y el press comprimen el espacio subacromial "
            "y sobrecargan el manguito rotador lesionado. El sistema conserva la "
            "musculatura del tren superior con jalones y remos —que trabajan dorsal "
            "y romboides en plano seguro— y refuerza rotadores externos."
        ),
        category="lesión", tier="CONTRAINDICACIONES", priority=80, severity="alta",
        references=("ACSM Guidelines (11ª ed.) — complejo del hombro",
                    "AAOS — manguito rotador"),
        action="restringir",
        alternative="Jalón al pecho, remo en polea, rotaciones externas con banda.",
        test="'hombro' in injuries",
    ),
    Rule(
        id="LES-04",
        description="Lesión cervical — evitar cargas axiales sobre cuello",
        condition=lambda p: "cervical" in p.injuries,
        conclusion=("Lesión cervical: evitar peso muerto con retención de aliento "
                    "y cargas sobre la cabeza. Alternativas: trabajo de cuello "
                    "isométrico en rangos sin dolor y ejercicios de escápulas."),
        explanation=(
            "Las cargas axiales elevadas y la maniobra de Valsalva aumentan la "
            "presión sobre las vértebras cervicales. Se sustituyen por trabajo "
            "isométrico suave y control escapular, manteniendo la musculatura "
            "estabilizadora sin comprender la zona lesionada."
        ),
        category="lesión", tier="CONTRAINDICACIONES", priority=75, severity="media",
        references=("ACSM Guidelines (11ª ed.) — seguridad en cargas"),
        action="restringir",
        alternative="Isométricos cervicales sin dolor, retracción escapular, face pull ligero.",
        test="'cervical' in injuries",
    ),
    Rule(
        id="LES-05",
        description="Lesión de codo — evitar flexiones y cargas de agarre forzado",
        condition=lambda p: "codo" in p.injuries,
        conclusion=("Lesión de codo: reducir flexiones y press de banca con agarre "
                    "cerrado. Alternativas: extensión de tríceps en polea con "
                    "agarre neutro y trabajo isométrico de flexores."),
        explanation=(
            "La epicondilitis y otras lesiones de codo se reproducen con cargas "
            "concéntricas exigentes del flexor/extensor. El sistema mantiene la "
            "fuerza del brazo con trabajo isométrico y poleas, que dosifican la "
            "carga sin forzar el rango doloroso."
        ),
        category="lesión", tier="CONTRAINDICACIONES", priority=75, severity="media",
        references=("ACSM Guidelines (11ª ed.) — articulaciones de extremidades"),
        action="restringir",
        alternative="Extensión en polea, isométricos de antebrazo, grip suave.",
        test="'codo' in injuries",
    ),
    Rule(
        id="LES-06",
        description="Lesión de muñeca — evitar press de banca y planchas cargadas",
        condition=lambda p: "muneca" in p.injuries,
        conclusion=("Lesión de muñeca: evitar planchas cargadas y press con muñeca "
                    "en extensión. Alternativas: press con mancuernas en martillo, "
                    "remo con agarre neutro y movilidad de muñeca sin dolor."),
        explanation=(
            "La extensión de la muñeca bajo carga comparte el patrón de la plancha "
            "y el press clásico, perpetuando la molestia. Con agarre neutro y "
            "ejercicios de tracción se conserva la musculatura del tren superior "
            "sin exigir la articulación lesionada."
        ),
        category="lesión", tier="CONTRAINDICACIONES", priority=75, severity="media",
        references=("ACSM Guidelines (11ª ed.) — variación de agarres"),
        action="restringir",
        alternative="Press martillo, remo neutro, movilidad sin dolor.",
        test="'muneca' in injuries",
    ),
    Rule(
        id="LES-07",
        description="Lesión de tobillo — evitar saltos y cambios de dirección",
        condition=lambda p: "tobillo" in p.injuries,
        conclusion=("Lesión de tobillo: evitar saltos, carrera en intervalos y "
                    "cambios de dirección. Alternativas: bicicleta, natación, "
                    "trabajo propioceptivo de equilibrio con apoyo."),
        explanation=(
            "Los movimientos en contrario y el impacto repetido reagudizan esguinces "
            "y lesiones de tendón de Aquiles. El sistema mantiene el cardio con "
            "modalidades de bajo impacto e introduce propiocepción —que acelera la "
            "recuperación del tobillo— con apoyo seguro."
        ),
        category="lesión", tier="CONTRAINDICACIONES", priority=75, severity="media",
        references=("ACSM Guidelines (11ª ed.) — retornos al entrenamiento",
                    "IOM — esguince de tobillo"),
        action="restringir",
        alternative="Bicicleta/elíptica, equilibrio sobre dos piernas, movilidad activa.",
        test="'tobillo' in injuries",
    ),
    Rule(
        id="LES-08",
        description="Lesión de cadera — evitar flexión profunda bajo carga",
        condition=lambda p: "cadera" in p.injuries,
        conclusion=("Lesión de cadera: evitar sentadillas profundas y peso muerto "
                    "convencional. Alternativas: puente de glúteos, abducción en "
                    "polea y caminata con rango cómodo."),
        explanation=(
            "La flexión profunda de cadera bajo carga comprime la articulación y "
            "sobrecarga el labrum o el flexor lesionado. El sistema conserva "
            "glúteo medio e isquiotibiales —estabilizadores clave de la cadera— "
            "con ejercicios en decúbito y poleas que evitan el rango doloroso."
        ),
        category="lesión", tier="CONTRAINDICACIONES", priority=75, severity="media",
        references=("AAOS — artrosis y lesiones de cadera",
                    "ACSM Guidelines (11ª ed.)"),
        action="restringir",
        alternative="Puente de glúteos, abducción en polea, caminata terrestre.",
        test="'cadera' in injuries",
    ),
    Rule(
        id="LES-09",
        description="Dolor articular generalizado — priorizar bajo impacto",
        condition=lambda p: "dolor_general" in p.injuries,
        conclusion=("Dolor articular generalizado: priorizar ejercicios no "
                    "impactantes (bicicleta, natación, máquinas guiadas) y evitar "
                    "trabajo prolongado acentuado bajo carga."),
        explanation=(
            "Cuando el dolor afecta a varias articulaciones, la prioridad es "
            "mantener la función sin ampliar la inflamación. Las máquinas guiadas "
            "y el trabajo acuático sostienen fuerza y movilidad con mínima carga "
            "articular, siguiendo el principio de dosificación por tolerancia."
        ),
        category="lesión", tier="CONTRAINDICACIONES", priority=78, severity="alta",
        references=("EULAR — recomendaciones de ejercicio en artritis",
                    "ACSM Guidelines (11ª ed.)"),
        action="restringir",
        alternative="Máquinas guiadas, agua, movilidad articular diaria.",
        test="'dolor_general' in injuries",
    ),
    Rule(
        id="LES-10",
        description="Movilidad reducida — ejercicios asistidos y rango seguro",
        condition=lambda p: "movilidad" in p.injuries,
        conclusion=("Movilidad reducida: trabajar con ejercicios asistidos y rangos "
                    "sin dolor; progresar amplitud antes que carga."),
        explanation=(
            "Cuando la movilidad es limitada, añadir carga antes de recuperar "
            "rango aumenta el riesgo de compensaciones y lesiones. El sistema "
            "prioriza movilidad activa-asistida y trabajo en rangos controlados, "
            "aumentando la dificultad solo cuando el movimiento es limpio."
        ),
        category="lesión", tier="CONTRAINDICACIONES", priority=72, severity="media",
        references=("ACSM Guidelines (11ª ed.) — rango de movimiento",
                    "OMS — actividad física en personas con movilidad reducida"),
        action="restringir",
        alternative="Movilidad asistida, bandas elásticas, trabajo en silla si hace falta.",
        test="'movilidad' in injuries",
    ),
    Rule(
        id="LES-SEV-02",
        description="Molestia moderada — dosificar volumen e intensidad",
        condition=lambda p: p.injury_severity == "moderada" and len(p.injuries) > 0,
        conclusion=("Molestia frecuente al entrenar: dosificar el volumen "
                    "(−30 % series) e intensidad, y reevaluar si persiste más de "
                    "2 semanas o empeora."),
        explanation=(
            "Una molestia moderada que se repite indica que la carga actual supera "
            "la tolerancia tisular. Reducir volumen e intensidad permite seguir "
            "entrenando la musculatura no afectada mientras se conserva la "
            "articulación; si persiste, corresponde evaluación profesional."
        ),
        category="lesión", tier="CONTRAINDICACIONES", priority=70, severity="media",
        references=("ACSM Guidelines (11ª ed.) — progresión por tolerancia"),
        conflicts=(),
        action="ajustar_carga",
        alternative="Mantener entrenamiento de zonas no afectadas con menor volumen.",
        test="injury_severity == 'moderada' y hay lesiones",
    ),

    # ══ EDAD — menores de edad ═══════════════════════════════════════════════

    Rule(
        id="EDAD-01",
        description="Menor de 18 años — sin déficit ni diagnóstico por IMC adulto",
        condition=lambda p: 0 < p.age < 18,
        conclusion=("Menor de 18 años: no se aplica déficit calórico ni "
                    "clasificación de IMC de adultos. El IMC se valora con curvas "
                    "de crecimiento (percentiles OMS/AAP) por un pediatra; el "
                    "sistema propone mantenimiento, actividad diaria y alimentación "
                    "de calidad."),
        explanation=(
            "En la adolescencia el crecimiento y el desarrollo óseo exigen aporte "
            "energético suficiente: los déficits diseñados para adultos pueden "
            "comprometer el desarrollo. Además, el IMC infantil no se clasifica con "
            "los cortes de adultos (18.5/25/30), sino con curvas de crecimiento "
            "por edad y sexo. Esta regla de tier EDAD suprime las reglas de déficit "
            "(NUT-01, NUT-03)."
        ),
        category="alerta", tier="EDAD", priority=95, severity="alta",
        references=("AAP — Adolescent Nutrition and Growth",
                    "OMS/CDC — curvas de crecimiento 5–19 años"),
        conflicts=("NUT-01", "NUT-03"),
        action="proteger",
        alternative="Objetivo de mantenimiento con énfasis en actividad física y variedad alimentaria.",
        test="age < 18",
    ),
    Rule(
        id="EDAD-02",
        description="Menor de 16 años — placas de crecimiento",
        condition=lambda p: 0 < p.age < 16,
        conclusion=("Menor de 16 años: excluir cargas máximas y levantamientos "
                    "olímpicos. Trabajar técnica, movilidad, coordinación y "
                    "fuerza con carga moderada y supervisión."),
        explanation=(
            "Las placas de crecimiento (epífisis) son el punto más débil del "
            "esqueleto juvenil; las cargas máximas repetidas pueden lesionarlas. "
            "La AAP y la ACSM reconocen que el entrenamiento de fuerza supervisado "
            "y con técnica es seguro en jóvenes, siempre que se eviten esfuerzos "
            "máximos y se priorice el control motor."
        ),
        category="biomecánica", tier="EDAD", priority=90, severity="alta",
        references=("AAP — Strength Training by Children and Adolescents",
                    "ACSM — youth resistance training position"),
        conflicts=("TRAIN-*",),
        action="restringir",
        alternative="Circuito de cuerpo completo con bandas, técnica y progresión lenta.",
        test="age < 16",
    ),
    Rule(
        id="EDAD-03",
        description="Adolescente 10–13 — variedad y habilidades motoras",
        condition=lambda p: 10 <= p.age <= 13,
        conclusion=("Adolescencia temprana: priorizar variedad deportiva, juegos "
                    "y habilidades motoras; 60 min diarios de actividad moderada o "
                    "vigorosa (OMS) sin especialización precoz."),
        explanation=(
            "En esta franja el objetivo es desarrollar patrones motores básicos y "
            "el gusto por el movimiento, no el rendimiento. La OMS recomienda 60 "
            "minutos diarios de actividad variada para 5–17 años, y la especialización "
            "precoz aumenta el riesgo de lesión y de abandono."
        ),
        category="entrenamiento", tier="EDAD", priority=65, severity="media",
        references=("OMS (2020) — actividad física, 5–17 años: 60 min/día",
                    "AAP — especialización deportiva precoz"),
        conflicts=(),
        action="orientar",
        alternative="Juegos, circuitos lúdicos, 3 días de fuerza con peso corporal.",
        test="10 <= age <= 13",
    ),
    Rule(
        id="EDAD-04",
        description="Adolescente 14–17 — fuerza supervisada y sueño 8–10 h",
        condition=lambda p: 14 <= p.age <= 17,
        conclusion=("Adolescente 14–17: entrenamiento de fuerza 3 días/semana con "
                    "técnica y progresión, 60 min/día de actividad y 8–10 horas de "
                    "sueño (AASM)."),
        explanation=(
            "A partir de los 14 años el entrenamiento de fuerza con supervision y "
            "cargas submáximas es seguro y beneficioso según la AAP/ACSM. El sueño "
            "8–10 h es crítico en esta edad para la consolidación hormonal y el "
            "aprendizaje; el sistema lo prioriza sobre cualquier volumen extra."
        ),
        category="entrenamiento", tier="EDAD", priority=60, severity="media",
        references=("AAP — Strength Training by Children and Adolescents",
                    "AASM/SRS — sueño en adolescentes (8–10 h)"),
        conflicts=(),
        action="orientar",
        alternative="Full Body 3 días, cardio recreacional, rutina de sueño regular.",
        test="14 <= age <= 17",
    ),

    # ══ EDAD — adultos mayores ═══════════════════════════════════════════════

    Rule(
        id="BIO-01",
        description="Adulto mayor ≥60 — reducir impacto articular",
        condition=lambda p: p.age >= 60,
        conclusion=("Adulto mayor (≥60): excluir ejercicios de alto impacto "
                    "pliométrico y levantamientos olímpicos. Priorizar fuerza "
                    "moderada, movilidad y cardio de bajo impacto."),
        explanation=(
            "Desde los 60 años la densidad ósea y la tolerancia cartilaginosa "
            "disminuyen; el impacto repetido multiplica el riesgo de fractura por "
            "fragilidad y de lesión de cartílago. La OMS considera adulto mayor a "
            "partir de los 60 en América Latina, y las guías recomiendan mantener "
            "fuerza con cargas moderadas —lo que protege el hueso— evitando el "
            "impacto alto."
        ),
        category="biomecánica", tier="EDAD", priority=88, severity="alta",
        references=("OMS — adulto mayor (60+) y actividad física",
                    "ACSM Guidelines (11ª ed.) — aging"),
        conflicts=(),
        action="restringir",
        alternative="Caminata, bicicleta, elíptica, máquinas guiadas y bandas.",
        test="age >= 60",
    ),
    Rule(
        id="EDAD-MAY-01",
        description="Adulto ≥60 — fuerza 2–3×/semana y proteína 1.0–1.2 g/kg",
        condition=lambda p: p.age >= 60,
        conclusion=("Adulto ≥60: entrenamiento de fuerza 2–3 días/semana y "
                    "1.0–1.2 g de proteína por kg de peso al día para prevenir "
                    "sarcopenia (consenso PROT-AGE)."),
        explanation=(
            "La sarcopenia (pérdida de masa y función muscular) progresa desde los "
            "60 años y es la principal causa de fragilidad. El consenso PROT-AGE "
            "recomienda 1.0–1.2 g/kg/día de proteína —por encima de la RDA de 0.8— "
            "junto con entrenamiento de fuerza regular, la única intervención que "
            "demuestra detener la pérdida muscular."
        ),
        category="nutricion", tier="EDAD", priority=85, severity="alta",
        references=("Consenso PROT-AGE (2013, JAMDA)",
                    "ACSM — exercise & physical activity in aging"),
        conflicts=(),
        action="orientar",
        alternative="Repartir la proteína en 3–4 comidas; suplementar solo por indicación.",
        test="age >= 60",
    ),
    Rule(
        id="EDAD-MAY-02",
        description="Adulto ≥70 o problemas de equilibrio — prevención de caídas",
        condition=lambda p: p.age >= 70 or p.balance_issues,
        conclusion=("Riesgo de caídas: incluir entrenamiento de equilibrio 3 "
                    "días/semana y revisar el entorno (calzado, iluminación, "
                    "barreras). Evitar saltos y superficies inestables sin apoyo."),
        explanation=(
            "Las caídas son la primera causa de lesión en personas mayores, y el "
            "equilibrio mejora con entrenamiento específico. CDC STEADI y la OMS "
            "recomiendan trabajo de equilibrio y de fuerza de tren inferior; la "
            "declaración de problemas de equilibrio o caídas previas activa esta "
            "regla con independencia de la edad exacta."
        ),
        category="alerta", tier="EDAD", priority=92, severity="alta",
        references=("CDC STEADI — falls prevention",
                    "OMS (2020) — adultos ≥65: equilibrio 3×/semana"),
        conflicts=(),
        action="orientar",
        alternative="Tándem a pie firme, sentado-levante, caminata en terreno llano.",
        test="age >= 70 o balance_issues",
    ),
    Rule(
        id="EDAD-MAY-03",
        description="Adulto ≥75 — supervisión y volumen conservador",
        condition=lambda p: p.age >= 75,
        conclusion=("Adulto ≥75: sesiones más cortas, progresión lenta y —si hay "
                    "enfermedades crónicas— entrenamiento supervisado o en grupo "
                    "terapéutico."),
        explanation=(
            "Por encima de 75 años convergen sarcopenia, posibles enfermedades "
            "crónicas y menor reserva cardiovascular. Las guías recomiendan "
            "mantener la actividad con dosificación conservadora y, cuando existen "
            "comorbilidades, supervisión profesional: la prioridad es la seguridad "
            "y la adherencia, no la intensidad."
        ),
        category="alerta", tier="EDAD", priority=80, severity="media",
        references=("OMS (2020) — actividad física en adultos ≥65",
                    "ACSM Guidelines (11ª ed.) — comorbilidades"),
        conflicts=(),
        action="orientar",
        alternative="Caminatas, sedestación activa, fuerza con bandas y silla.",
        test="age >= 75",
    ),
    Rule(
        id="SEG-04",
        description="Tamizaje preparticipativo desde los 45 años",
        condition=lambda p: p.age >= 45,
        conclusion=("Desde los 45 años: completar el tamizaje preparticipativo "
                    "(síntomas y factores de riesgo cardiovascular) antes de "
                    "iniciar ejercicio vigoroso; revisiones periódicas."),
        explanation=(
            "La AHA/ACCM recomienda evaluar síntomas y factores de riesgo antes de "
            "actividad vigorosa en adultos, con revisión del tamizaje cada año o "
            "ante cambios de salud. El sistema no sustituye esa evaluación: la "
            "recomienda y, si aparecen síntomas (ver reglas SEG-RF-*), deriva con "
            "máxima prioridad."
        ),
        category="alerta", tier="EDAD", priority=55, severity="baja",
        references=("AHA/ACC (2019) Recommendations for Preparticipation Evaluation",
                    "ACSM Guidelines (11ª ed.) — screening"),
        conflicts=(),
        action="orientar",
        alternative="Ninguna restricción si el tamizaje es normal.",
        test="age >= 45",
    ),

    # ══ CONDICIÓN FÍSICA — IMC, composición, sedentarismo ════════════════════

    Rule(
        id="NUT-07",
        description="Bajo peso (IMC < 18.5)",
        condition=lambda p: (
            p.imc > 0
            and p.imc < (22.0 if p.is_senior() else 18.5)
            and (p.is_senior() or p.age >= 18)   # cortes de adultos: no en menores
        ),
        conclusion=("IMC por debajo del rango seguro (bajo peso: <18.5 en adultos, "
                    "<22 en adultos mayores): no aplicar déficit. Aumentar la ingesta "
                    "de forma progresiva con alimentos densos en nutrientes y "
                    "valorar evaluación médica/nutricional."),
        explanation=(
            "Un IMC < 18.5 se asocia a mayor riesgo de deficiencia inmunológica y "
            "ósea. El sistema suprime cualquier regla de déficit (NUT-01/NUT-03) "
            "porque el objetivo seguro es estabilizar o ganar peso de forma "
            "gradual, priorizando densidad nutricional antes que volumen."
        ),
        category="nutricion", tier="CONDICION_FISICA", priority=85, severity="alta",
        references=("OMS (2022) — clasificación IMC adultos",
                    "ACSM — underweight management"),
        conflicts=("NUT-01", "NUT-03"),
        action="suprimir_deficit",
        alternative="Aumento calórico gradual (+10 %) con colas nutritivas.",
        test="0 < imc < 18.5",
    ),
    Rule(
        id="NUT-08",
        description="Obesidad (IMC ≥ 30) — control médico y nutricional",
        condition=lambda p: p.imc >= 30 and p.imc > 0,
        conclusion=("IMC ≥ 30 (obesidad, OMS): el sistema orienta con un plan de "
                    "pérdida de peso gradual, pero se recomienda control médico y "
                    "nutricional, especialmente si hay hipertensión, diabetes u "
                    "otras condiciones asociadas."),
        explanation=(
            "El IMC es un indicador de tamizaje, no un diagnóstico: la obesidad se "
            "confirma evaluando composición corporal y contexto clínico. Con IMC "
            "≥ 30 las guías recomiendan intervención profesional; el sistema aporta "
            "el marco orientativo (déficit moderado, fuerza, actividad diaria) sin "
            "sustituir esa evaluación."
        ),
        category="alerta", tier="CONDICION_FISICA", priority=82, severity="alta",
        references=("OMS (2022) — Obesity and overweight",
                    "NIH/NHLBI — Clinical Guidelines on Obesity"),
        conflicts=(),
        action="orientar",
        alternative="Déficit del 10–12 %, fuerza 2–3×/semana, 7–9 h de sueño.",
        test="imc >= 30",
    ),
    Rule(
        id="NUT-08B",
        description="Sobrepeso (IMC 25–29.9)",
        condition=lambda p: 25.0 <= p.imc < 30.0,
        conclusion=("IMC 25–29.9 (sobrepeso): combinación de déficit calórico "
                    "moderado con ejercicio de fuerza y 7 000–10 000 pasos diarios "
                    "es suficiente en la mayoría de los casos."),
        explanation=(
            "El sobrepeso por IMC no implica por sí solo riesgo metabólico alto: "
            "muchas personas con IMC 25–29 tienen buena composición corporal. La "
            "OMS lo clasifica como sobrepeso y las guías coinciden en que el "
            "cambio de hábitos —no las dietas restrictivas— es la intervención más "
            "sostenible."
        ),
        category="nutricion", tier="CONDICION_FISICA", priority=60, severity="baja",
        references=("OMS (2022) — clasificación IMC",
                    "USPSTF — pérdida de peso en sobrepeso"),
        conflicts=(),
        action="orientar",
        alternative="Déficit leve (8–12 %) + fuerza + pasos diarios.",
        test="25 <= imc < 30",
    ),
    Rule(
        id="BIO-03",
        description="Obesidad grado III (IMC ≥ 40) — sin impacto articular",
        condition=lambda p: p.imc >= 40 and p.imc > 0,
        conclusion=("IMC ≥ 40: eliminar saltos e impacto en rodillas y columna. "
                    "Ejercicio de bajo impacto (acuático, bicicleta, máquinas "
                    "guiadas) y evaluación médica previa."),
        explanation=(
            "Con IMC ≥ 40 las fuerzas de reacción en saltos y carrera llegan a "
            "multiplicar varias veces el peso corporal, lo que somete rodillas, "
            "cadera y columna a cargas muy por encima de su capacidad. El "
            "entrenamiento acuático y en máquinas guiadas conserva la fuerza sin "
            "ese riesgo, y la ACSM recomienda evaluación previa en este rango."
        ),
        category="biomecánica", tier="CONDICION_FISICA", priority=84, severity="alta",
        references=("OMS (2022) — obesidad grado III",
                    "ACSM Guidelines (11ª ed.) — ejercicio en obesidad"),
        conflicts=(),
        action="restringir",
        alternative="Natación, bicicleta estática, remo y máquinas guiadas.",
        test="imc >= 40",
    ),
    Rule(
        id="SEG-01",
        description="Sedentarismo con IMC ≥ 25",
        condition=lambda p: p.activity_level == "sedentario" and p.imc >= 25,
        conclusion=("Sedentarismo con IMC ≥ 25: iniciar 30 min de caminata diaria "
                    "y progresar 10 % semanal. Evitar dietas agresivas combinadas "
                    "con inactividad."),
        explanation=(
            "La combinación de baja actividad y sobrepeso eleva el riesgo "
            "cardiovascular y metabólico. La ACSM recomienda comenzar con volúmenes "
            "bajos y progresar de forma gradual: es la estrategia con mejor "
            "adherencia y menor riesgo de lesión."
        ),
        category="seguimiento", tier="CONDICION_FISICA", priority=70, severity="media",
        references=("OMS (2020) — actividad física y conducta sedentaria",
                    "ACSM Guidelines (11ª ed.) — progresión"),
        conflicts=(),
        action="orientar",
        alternative="Caminata diaria 30 min → 45–60 min en 6–8 semanas.",
        test="activity_level == 'sedentario' e imc >= 25",
    ),
    Rule(
        id="SEG-05",
        description="Cardio para nivel sedentario o ligero",
        condition=lambda p: p.activity_level in ("sedentario", "ligero"),
        conclusion=("Incorporar 150–300 min semanales de actividad moderada (o "
                    "75–150 vigorosa) más 2 días de fuerza — recomendación OMS."),
        explanation=(
            "La OMS fija 150–300 min semanales de actividad moderada para adultos "
            "y 2 sesiones de fortalecimiento muscular. Para un nivel sedentario o "
            "ligero, alcanzar esa base produce la mayor mejora relativa de salud "
            "cardiovascular, sensibilidad a la insulina y ánimo."
        ),
        category="seguimiento", tier="CONDICION_FISICA", priority=65, severity="info",
        references=("OMS (2020) — Directrices sobre actividad física"),
        conflicts=(),
        action="orientar",
        alternative="Empezar por 75 min/semana y sumar 10 % cada semana.",
        test="activity_level en ('sedentario', 'ligero')",
    ),
    Rule(
        id="COMP-01",
        description="Porcentaje de grasa elevado para el sexo y la edad",
        condition=lambda p: (
            p.body_fat_pct > 0 and (
                (p.sex == "masculino" and p.body_fat_pct > 25) or
                (p.sex == "femenino" and p.body_fat_pct > 32)
            )
        ),
        conclusion=("Porcentaje de grasa por encima del rango de referencia (ACSM): "
                    "priorizar recomposición —fuerza + déficit leve + proteína "
                    "adecuada— más que solo bajar la báscula."),
        explanation=(
            "El IMC no distingue músculo de grasa; con % de grasa alto y peso "
            "normal u obesidad se recomienda intervenir sobre la composición: la "
            "fuerza preserva masa magra durante el déficit y mejora el gasto en "
            "reposo. Los cortes aplicados corresponden a los rangos de referencia "
            "de la ACSM para adultos."
        ),
        category="nutricion", tier="CONDICION_FISICA", priority=62, severity="media",
        references=("ACSM Guidelines (11ª ed.) — body composition ranges"),
        conflicts=(),
        action="orientar",
        alternative="Déficit 8–10 % + 1.6–2.2 g proteína/kg + fuerza 3×/semana.",
        test="body_fat_pct fuera del rango ACSM para el sexo",
    ),
    Rule(
        id="COMP-02",
        description="Grasa corporal muy baja — suprimir déficit",
        condition=lambda p: (
            p.body_fat_pct > 0 and (
                (p.sex == "masculino" and p.body_fat_pct < 5) or
                (p.sex == "femenino" and p.body_fat_pct < 12)
            )
        ),
        conclusion=("Porcentaje de grasa muy bajo: no aplicar déficit calórico "
                    "ni reducir grasas; riesgo de alteraciones hormonales y "
                    "óseas. Mantenimiento con ingesta suficiente."),
        explanation=(
            "Niveles de grasa por debajo de los rangos esenciales se asocian a "
            "amenorrea, deterioro hormonal y menor densidad ósea. Esta regla de "
            "tier CONDICIÓN FÍSICA suprime las reglas de déficit (NUT-01/NUT-03) "
            "con la misma lógica que el bajo peso."
        ),
        category="alerta", tier="CONDICION_FISICA", priority=86, severity="alta",
        references=("ACSM — body fat essential ranges",
                    "IOC — REDs (Relative Energy Deficiency in Sport)"),
        conflicts=("NUT-01", "NUT-03"),
        action="suprimir_deficit",
        alternative="Mantenimiento calórico; grasas ≥25 % de la ingesta.",
        test="body_fat_pct bajo el rango esencial para el sexo",
    ),

    # ══ OBJETIVO — metas calóricas ═══════════════════════════════════════════
    # (los valores exactos aplicados —con suelos y techos de seguridad—
    #  se calculan en calculations.py y se muestran en las métricas)

    Rule(
        id="NUT-01",
        description="Déficit calórico para pérdida de grasa",
        condition=lambda p: p.objective == "perdida_grasa",
        conclusion=("Pérdida de grasa: déficit del 12 % sobre el gasto diario "
                    "(limitado por seguridad; ver meta calórica diaria). Ritmo "
                    "esperado 0.25–0.5 kg/semana."),
        explanation=(
            "El déficit se calcula como porcentaje del TDEE —no como un valor fijo— "
            "para respetar la fisiología de cada persona: nunca baja del gasto "
            "basal ni del mínimo nutricional, y se anula en menores o bajo peso "
            "por reglas de mayor jerarquía. Un déficit del 10–12 % produce una "
            "pérdida de grasa sostenible preservando masa muscular."
        ),
        category="nutricion", tier="OBJETIVO", priority=70, severity="info",
        references=("OMS (2022) — pérdida de peso sostenible",
                    "ACSM/AND — rate of weight loss"),
        conflicts=(),
        action="ajustar_calorias",
        alternative="Si aparece fatiga o pérdida muscular, reducir déficit al 8 %.",
        test="objective == 'perdida_grasa'",
    ),
    Rule(
        id="NUT-02",
        description="Superávit calórico para aumento muscular",
        condition=lambda p: p.objective == "aumento_muscular",
        conclusion=("Aumento muscular: superávit del 10 % sobre el gasto diario "
                    "(techo 15 % por seguridad) para ganar masa con mínimo "
                    "exceso de grasa."),
        explanation=(
            "La síntesis proteica muscular necesita energía disponible, pero "
            "superávits grandes solo aumentan la grasa: la ACSM recomienda "
            "ganancias graduales (0.25–0.5 kg/semana). El sistema limita el "
            "superávit al 10–15 % del TDEE y lo reduce a la mitad en adultos "
            "mayores."
        ),
        category="nutricion", tier="OBJETIVO", priority=70, severity="info",
        references=("ACSM — progressive models in resistance training",
                    "ISSN — nutrition & hypertrophy"),
        conflicts=(),
        action="ajustar_calorias",
        alternative="Si la grasa sube rápido, bajar superávit al 5 %.",
        test="objective == 'aumento_muscular'",
    ),
    Rule(
        id="NUT-03",
        description="Déficit leve para definición muscular",
        condition=lambda p: p.objective == "definicion",
        conclusion=("Definición: déficit leve del 8 % con proteína alta "
                    "para preservar la masa muscular."),
        explanation=(
            "La definición busca reducir grasa sin perder músculo: el déficit se "
            "mantiene leve y la proteína en rango alto (35–40 % de las calorías) "
            "actúa como red de seguridad. Es la modalidad con menor riesgo de "
            "efecto rebote."
        ),
        category="nutricion", tier="OBJETIVO", priority=68, severity="info",
        references=("ISSN — protein & body composition",
                    "ACSM Guidelines (11ª ed.)"),
        conflicts=(),
        action="ajustar_calorias",
        alternative="Semana de recarga cada 8–12 semanas si el rendimiento baja.",
        test="objective == 'definicion'",
    ),
    Rule(
        id="NUT-04",
        description="Calorías de mantenimiento o recomposición",
        condition=lambda p: p.objective in ("mantenimiento", "recomposicion"),
        conclusion=("Mantenimiento/recomposición: ingerir el gasto diario "
                    "estimado, con distribución de macros según prioridad "
                    "muscular."),
        explanation=(
            "En mantenimiento las calorías igualan al gasto; en recomposición el "
            "mismo objetivo se acompaña de proteína alta y fuerza para mejorar la "
            "composición corporal sin cambios de peso neto. La diferencia entre "
            "ambos está en la estrategia, no en el número de calorías."
        ),
        category="nutricion", tier="OBJETIVO", priority=60, severity="info",
        references=("ACSM Guidelines (11ª ed.) — weight maintenance"),
        conflicts=(),
        action="ajustar_calorias",
        alternative="Si el peso cambia ±2 kg en 4 semanas, ajustar 100–200 kcal.",
        test="objective en ('mantenimiento', 'recomposicion')",
    ),
    Rule(
        id="NUT-05",
        description="Alta proteína durante déficit",
        condition=lambda p: p.objective in ("perdida_grasa", "definicion") and p.caloric_adjustment < 0,
        conclusion=("Durante el déficit: 1.6–2.2 g de proteína por kg al día "
                    "(35–40 % de las calorías) para preservar músculo y saciedad."),
        explanation=(
            "En déficit, la proteína elevada reduce la pérdida de masa magra y "
            "aumenta la saciedad —el factor nº1 de adherencia—, según consensos de "
            "la ISSN y la ACSM. El sistema la calcula por peso corporal en el plan "
            "nutricional."
        ),
        category="nutricion", tier="OBJETIVO", priority=64, severity="info",
        references=("ISSN Position Stand — protein (2017)",
                    "ACSM/AND — protein in weight loss"),
        conflicts=(),
        action="orientar",
        alternative="Si hay problemas renales, ajustar proteína con nefrólogo.",
        test="objective en ('perdida_grasa', 'definicion')",
    ),
    Rule(
        id="NUT-06",
        description="Hidratación diaria según peso",
        condition=lambda p: p.weight > 0,
        conclusion=("Hidratación sugerida según peso: "
                    "aprox. 35 ml/kg/día (piso 1.2 L, techo 5 L), más "
                    "500–750 ml por hora de ejercicio."),
        explanation=(
            "La hidratación óptima sostiene el rendimiento, la termorregulación y "
            "la recuperación. La fórmula de 35 ml/kg con suelos de seguridad evita "
            "tanto la deshidratación como el exceso hídrico (hiponatremia de "
            "ejercicio), que puede ser tan peligroso como la deshidratación."
        ),
        category="nutricion", tier="OBJETIVO", priority=55, severity="info",
        references=("ACSM/AND — posición sobre hidratación",
                    "EFSA — ingesta de agua"),
        conflicts=(),
        action="orientar",
        alternative="Ajustar según sed, color de orina y sudoración.",
        test="weight > 0",
    ),
    Rule(
        id="NUT-14",
        description="Distribución de comidas según frecuencia declarada",
        condition=lambda p: p.weight > 0 and p.meal_frequency in (3, 4, 5),
        conclusion=("Repartir la ingesta en la frecuencia elegida (3–5 comidas) "
                    "con proteína distribuida (0.3–0.4 g/kg por comida) para "
                    "saturación proteica y saciedad sostenida."),
        explanation=(
            "Distribuir la proteína en 3–4 comidas mejora la síntesis proteica "
            "muscular respecto de concentrarla en una sola, y una frecuencia "
            "regular de comidas ayuda al control de apetito. El sistema respeta "
            "la preferencia declarada (3–5 comidas) al construir el menú."
        ),
        category="nutricion", tier="OBJETIVO", priority=50, severity="info",
        references=("Journal of Nutrition (2015) — protein distribution",
                    "ISSN — meal frequency & protein"),
        conflicts=(),
        action="orientar",
        alternative="Si no hay hambre en 5 comidas, reducir a 4 sin forzar.",
        test="meal_frequency en (3, 4, 5)",
    ),
    Rule(
        id="NUT-15",
        description="Proteína según grupo de edad y actividad",
        condition=lambda p: p.weight > 0 and p.age > 0,
        conclusion=("Pauta de proteína personalizada por edad y actividad "
                    "(ver cálculo: rango g/kg/día según grupo)."),
        explanation=(
            "Las necesidades de proteína varían con la edad y la actividad: "
            "0.8 g/kg en sedentarios, 1.6–2.2 g/kg en entrenamiento de fuerza, "
            "1.0–1.2 g/kg en ≥60 años (PROT-AGE) y 0.9–1.4 g/kg en menores. El "
            "sistema calcula el rango exacto según el perfil."
        ),
        category="nutricion", tier="OBJETIVO", priority=52, severity="info",
        references=("RDA/FAO — protein intake",
                    "Consenso PROT-AGE (2013)",
                    "ISSN Position Stand — protein (2017)"),
        conflicts=(),
        action="orientar",
        alternative="Ajustar con profesional si hay enfermedad renal o hepática.",
        test="weight > 0 y age > 0",
    ),

    # ══ OBJETIVO — planes de entrenamiento ═══════════════════════════════════

    Rule(
        id="TRAIN-CASA-01",
        description="Rutina en casa — principiante — pérdida de grasa",
        condition=lambda p: (
            p.training_place == "casa"
            and p.experience == "principiante"
            and p.objective in ("perdida_grasa", "definicion", "recomposicion", "mantenimiento")
        ),
        conclusion="Rutina en casa: 3 días/semana — circuito de cuerpo completo con cardio.",
        explanation=(
            "Para principiantes en casa con objetivo de pérdida de grasa, un circuito "
            "de cuerpo completo de 3 días semanales combina fuerza y cardio, maximizando "
            "el gasto calórico sin requerir equipo especializado."
        ),
        category="entrenamiento", tier="OBJETIVO", priority=60, severity="info",
        references=("ACSM Guidelines (11ª ed.) — beginner programs"),
        action="generar_plan",
        alternative="Si no hay tiempo, 2 sesiones de cuerpo completo mantienen el estímulo.",
        test="casa + principiante + objetivo no muscular",
    ),
    Rule(
        id="TRAIN-CASA-02",
        description="Rutina en casa — principiante — músculo",
        condition=lambda p: (
            p.training_place == "casa"
            and p.experience == "principiante"
            and p.objective == "aumento_muscular"
        ),
        conclusion="Rutina en casa: 3 días/semana — entrenamiento de fuerza con peso corporal.",
        explanation=(
            "Para ganar músculo en casa siendo principiante, ejercicios de peso corporal "
            "(sentadillas, flexiones, dominadas) producen suficiente estímulo de hipertrofia "
            "cuando se ejecutan con progresión adecuada."
        ),
        category="entrenamiento", tier="OBJETIVO", priority=60, severity="info",
        references=("ACSM — resistance training in beginners"),
        action="generar_plan",
        alternative="Añadir bandas elásticas cuando 15–20 repeticiones resulten fáciles.",
        test="casa + principiante + aumento_muscular",
    ),
    Rule(
        id="TRAIN-CASA-03",
        description="Rutina en casa — intermedio / avanzado",
        condition=lambda p: (
            p.training_place == "casa"
            and p.experience in ("intermedio", "avanzado")
        ),
        conclusion="Rutina en casa: 4–5 días/semana — splits de empuje/jalar/pierna con progresión de carga.",
        explanation=(
            "Usuarios con experiencia pueden aplicar splits de mayor volumen en casa, "
            "usando variantes avanzadas de peso corporal, bandas de resistencia y "
            "overload progresivo para continuar mejorando."
        ),
        category="entrenamiento", tier="OBJETIVO", priority=60, severity="info",
        references=("ACSM — progression models in resistance training"),
        action="generar_plan",
        alternative="Si el equipo limita la progresión, priorizar densidad (menos descanso).",
        test="casa + intermedio/avanzado",
    ),
    Rule(
        id="TRAIN-GYM-01",
        description="Rutina gimnasio — principiante — pérdida de grasa",
        condition=lambda p: (
            p.training_place == "gimnasio"
            and p.experience == "principiante"
            and p.objective in ("perdida_grasa", "definicion", "mantenimiento", "recomposicion")
        ),
        conclusion="Rutina gimnasio: Full Body 3 días/semana + 2 sesiones de cardio moderado.",
        explanation=(
            "Para principiantes en gimnasio con objetivo de pérdida de grasa, el Full Body "
            "trisemanal maximiza la frecuencia de estímulo muscular mientras el cardio adicional "
            "amplía el déficit calórico."
        ),
        category="entrenamiento", tier="OBJETIVO", priority=60, severity="info",
        references=("ACSM Guidelines (11ª ed.) — frequency"),
        action="generar_plan",
        alternative="Si el cardio acumula fatiga, priorizar pasos diarios.",
        test="gimnasio + principiante + no aumento_muscular",
    ),
    Rule(
        id="TRAIN-GYM-02",
        description="Rutina gimnasio — principiante — músculo",
        condition=lambda p: (
            p.training_place == "gimnasio"
            and p.experience == "principiante"
            and p.objective == "aumento_muscular"
        ),
        conclusion="Rutina gimnasio: Full Body 3 días/semana con énfasis en ejercicios compuestos.",
        explanation=(
            "Los ejercicios compuestos (sentadilla, press banca, peso muerto, remo) "
            "activan mayor cantidad de masa muscular y estimulan la producción hormonal "
            "anabólica, ideal para principiantes que buscan hipertrofia."
        ),
        category="entrenamiento", tier="OBJETIVO", priority=60, severity="info",
        references=("ACSM — resistance training principles"),
        action="generar_plan",
        alternative="Añadir 1 serie por ejercicio cada 2 semanas si la técnica es buena.",
        test="gimnasio + principiante + aumento_muscular",
    ),
    Rule(
        id="TRAIN-GYM-03",
        description="Rutina gimnasio — intermedio",
        condition=lambda p: p.training_place == "gimnasio" and p.experience == "intermedio",
        conclusion="Rutina gimnasio: Split 4 días — Empuje / Jalar / Piernas / Cuerpo completo.",
        explanation=(
            "El split de 4 días permite mayor volumen por grupo muscular que el Full Body, "
            "favoreciendo la hipertrofia en usuarios con más de 6 meses de experiencia."
        ),
        category="entrenamiento", tier="OBJETIVO", priority=60, severity="info",
        references=("ACSM — volume & frequency for intermediates"),
        action="generar_plan",
        alternative="Si la recuperación baja, pasar a 3 días Full Body.",
        test="gimnasio + intermedio",
    ),
    Rule(
        id="TRAIN-GYM-04",
        description="Rutina gimnasio — avanzado",
        condition=lambda p: p.training_place == "gimnasio" and p.experience == "avanzado",
        conclusion="Rutina gimnasio: Split 5–6 días — PPL doble (Push-Pull-Legs x2 semana).",
        explanation=(
            "Usuarios avanzados necesitan mayor frecuencia y volumen para continuar "
            "progresando. El PPL doble (6 días) ofrece 2 estímulos semanales por grupo "
            "muscular con periodización avanzada."
        ),
        category="entrenamiento", tier="OBJETIVO", priority=60, severity="info",
        references=("ACSM — advanced programming"),
        action="generar_plan",
        alternative="Deload programado cada 4–6 semanas para gestionar la fatiga.",
        test="gimnasio + avanzado",
    ),
    Rule(
        id="TRAIN-CARDIO-01",
        description="Cardio complementario para pérdida de grasa activa",
        condition=lambda p: (
            p.objective in ("perdida_grasa", "definicion")
            and p.activity_level in ("moderado", "activo", "muy_activo")
        ),
        conclusion=("Objetivo de pérdida con nivel de actividad ya alto: mantener "
                    "150–300 min semanales de cardio moderado; no añadir volumen "
                    "extra si la recuperación es buena."),
        explanation=(
            "Cuando el usuario ya es activo, el déficit lo aporta la alimentación, "
            "no más cardio. La ACSM recomienda no escalar indefinidamente el volumen "
            "porque aumenta el riesgo de sobreentrenamiento y lesión por uso repetido."
        ),
        category="entrenamiento", tier="OBJETIVO", priority=52, severity="info",
        references=("OMS (2020) — 150–300 min/semana",
                    "ACSM — overtraining prevention"),
        conflicts=(),
        action="orientar",
        alternative="Mantener deporte preferido 2–3 veces/semana dentro del rango OMS.",
        test="objetivo déficit y actividad >= moderada",
    ),

    # ══ OBJETIVO — macronutrientes y estilo ══════════════════════════════════

    Rule(
        id="NUT-09",
        description="Plan vegano — exclusión de productos animales",
        condition=lambda p: p.diet_type == "vegano",
        conclusion=("Plan 100 % vegetal: proteínas de legumbres, tofu, tempeh y "
                    "semillas. Suplementar vitamina B12 (imprescindible) y revisar "
                    "vitamina D, hierro y omega-3."),
        explanation=(
            "Las dietas veganas bien planificadas son adecuadas a cualquier edad "
            "según la Academia de Nutrición y Dietética, pero la B12 solo se "
            "encuentra de forma fiable en alimentos animales o fortificados: su "
            "suplementación es obligatoria. El sistema también revisa hierro y "
            "calcio porque las fuentes vegetales tienen menor biodisponibilidad."
        ),
        category="nutricion", tier="PREFERENCIAS", priority=58, severity="media",
        references=("Academy of Nutrition and Dietetics — vegetarian diets",
                    "NIH ODS — vitamina B12"),
        conflicts=(),
        action="filtrar_dieta",
        alternative="Tempeh, tofu firme, lentejas, quinoa, edamame; alimentos fortificados.",
        test="diet_type == 'vegano'",
    ),
    Rule(
        id="NUT-10",
        description="Plan vegetariano — sin carne",
        condition=lambda p: p.diet_type == "vegetariano",
        conclusion="Plan vegetariano: proteínas de huevo, lácteos y legumbres.",
        explanation=(
            "El usuario sigue una dieta vegetariana. El plan excluye carnes rojas, aves y "
            "pescado, pero incluye proteínas de calidad como huevos, queso, yogur y legumbres."
        ),
        category="nutricion", tier="PREFERENCIAS", priority=56, severity="info",
        references=("Academy of Nutrition and Dietetics — vegetarian diets"),
        conflicts=(),
        action="filtrar_dieta",
        alternative="Huevo, lácteos, legumbres, tofu y quinoa.",
        test="diet_type == 'vegetariano'",
    ),
    Rule(
        id="NUT-11",
        description="Plan pescetariano",
        condition=lambda p: p.diet_type == "pescetariano",
        conclusion="Plan pescetariano: p marino 2–3 veces/semana + huevos, lácteos y legumbres.",
        explanation=(
            "La dieta pescetariana incluye pescado —fuente de proteína y omega-3— y "
            "excluye carnes rojas y aves. El plan prioriza pescados azules 2–3 veces "
            "por semana para cubrir EPA/DHA según las recomendaciones de las guías "
            "cardiovasculares."
        ),
        category="nutricion", tier="PREFERENCIAS", priority=56, severity="info",
        references=("AHA — fish consumption recommendations",
                    "FAO — omega-3 intake"),
        conflicts=(),
        action="filtrar_dieta",
        alternative="Sardina, salmón, caballa, anchoa; legumbres y huevo el resto de días.",
        test="diet_type == 'pescetariano'",
    ),
    Rule(
        id="NUT-12",
        description="Celiaquía / alergia al gluten — exclusión estricta",
        condition=lambda p: "gluten" in p.allergies,
        conclusion=("Celiaquía/alergia al gluten: eliminar trigo, cebada, centeno y "
                    "sus derivados. Usar arroz, quinoa, maíz y avena certificada sin "
                    "contaminación cruzada."),
        explanation=(
            "En celiaquía no existe un umbral seguro de gluten: pequeñas cantidades "
            "mantienen la lesión intestinal (WGO). Por eso la regla no solo quita el "
            "trigo, sino que exige certificación sin contaminación cruzada —pan, pasta "
            "y salsas son fuentes ocultas habituales—."
        ),
        category="nutricion", tier="SEGURIDAD", priority=88, severity="alta",
        references=("WGO — Celiac disease global guideline",
                    "ACG — Celiac disease management"),
        action="excluir_alergeno",
        alternative="Arroz, quinoa, mijo, maíz, avena certificada GFree.",
        test="'gluten' in allergies",
    ),
    Rule(
        id="NUT-13",
        description="Filtro alergia a la proteína de leche",
        condition=lambda p: "leche" in p.allergies,
        conclusion=("Alergia a la proteína de leche: excluir leche y derivados "
                    "(no sustituir solo por lácteos «bajos en lactosa»). Alternativas: "
                    "bebida vegetal fortificada con calcio."),
        explanation=(
            "La alergia a la proteína de leche es una reacción inmunológica "
            "distinta de la intolerancia a la lactosa: los derivados lácteos "
            "también provocan reacción, por lo que no basta con quitar la lactosa. "
            "El sistema exige verificar etiquetas y recomendaciones alternativas "
            "fortificadas con calcio y vitamina D."
        ),
        category="nutricion", tier="SEGURIDAD", priority=88, severity="alta",
        references=("AAAAI/ACAAI — Food Allergy Practice Parameter",
                    "AAP — cow's milk protein allergy"),
        action="excluir_alergeno",
        alternative="Bebida de avena/almond-free fortificada, tofu calciado, sardinas.",
        test="'leche' in allergies",
    ),

    # ══ PREFERENCIAS — intolerancias (digestivas, no alergia) ═════════════════

    Rule(
        id="INT-01",
        description="Intolerancia a la lactosa",
        condition=lambda p: p.has_intolerance("lactosa") or "lactosa" in p.allergies,
        conclusion=("Intolerancia a la lactosa: reducir leche y lácteos frescos; "
                    "permitir versiones curadas/queso maduro en pequeñas cantidades "
                    "y bebidas vegetales. No se equipara a alergia."),
        explanation=(
            "La intolerancia a la lactosa es una carencia de lactasa, no una "
            "reacción inmunológica: el grado de tolerancia varía y los quesos "
            "curados tienen poca lactosa (NIH/NIDDK). Por eso la regla excluye las "
            "fuentes principales pero no declara «prohibidos absolutos», a "
            "diferencia de las alergias."
        ),
        category="nutricion", tier="PREFERENCIAS", priority=66, severity="media",
        references=("NIH/NIDDK — Lactose Intolerance",
                    "ESPGHAN — lactose malabsorption"),
        conflicts=(),
        action="filtrar_intolerancia",
        alternative="Bebida vegetal, queso curado pequeño, yogur con lactasa.",
        test="'lactosa' en intolerances (o allergies legado)",
    ),
    Rule(
        id="INT-02",
        description="Intolerancia a la fructosa",
        condition=lambda p: p.has_intolerance("fructosa"),
        conclusion=("Intolerancia a la fructosa: limitar miel, jarabes, fruta en "
                    "exceso y edulcorantes de alta fructosa; distribuir la fruta "
                    "en pequeñas porciones."),
        explanation=(
            "La malabsorción de fructosa provoca síntomas digestivos cuando los "
            "azúcares de cadena corta superan la capacidad del transportador "
            "intestinal. La regla reduce las fuentes concentradas (miel, jarabe de "
            "maíz, jugos) manteniendo fruta entera en porciones toleradas."
        ),
        category="nutricion", tier="PREFERENCIAS", priority=64, severity="media",
        references=("Monash University — FODMAP",
                    "Rome Foundation — fructose malabsorption"),
        conflicts=(),
        action="filtrar_intolerancia",
        alternative="Fruta madura en porciones, arroz, patata, sin jarabes.",
        test="'fructosa' in intolerances",
    ),
    Rule(
        id="INT-03",
        description="Sensibilidad al gluten no celíaca",
        condition=lambda p: p.has_intolerance("gluten_no_celiaca"),
        conclusion=("Sensibilidad al gluten no celíaca: reducir trigo, cebada y "
                    "centeno sin necesidad de certificación estricta; reevaluar si "
                    "los síntomas persisten (descartar celiaquía)."),
        explanation=(
            "La sensibilidad no celíaca no daña la mucosa intestinal, por lo que "
            "la restricción es de síntomas, no de seguridad absoluta. Si los "
            "síntomas continúan conviene descartar celiaquía con análisis: el "
            "sistema diferencia esta regla de la NUT-12, que sí exige exclusión "
            "total y certificación."
        ),
        category="nutricion", tier="PREFERENCIAS", priority=62, severity="media",
        references=("WGO — non-celiac gluten sensitivity",
                    "ACG — Celiac disease guideline"),
        conflicts=(),
        action="filtrar_intolerancia",
        alternative="Arroz, quinoa, patata; trigo ocasional si es tolerado.",
        test="'gluten_no_celiaca' in intolerances",
    ),

    # ══ PREFERENCIAS — gustos declarados ═════════════════════════════════════

    Rule(
        id="PREF-01",
        description="Preferencia: bajo en sal",
        condition=lambda p: p.has_preference("bajo_en_sal"),
        conclusion=("Preferencia baja en sal: condimentar con hierbas, cítricos y "
                    "especias; limitar ultraprocesados a <2 g de sodio/día (OMS)."),
        explanation=(
            "La OMS recomienda menos de 2 g de sodio al día (≈5 g de sal). El menú "
            "sustituye salsas y cubitos por aromáticas, ajo, limón y especias, que "
            "mantienen el sabor sin el exceso de sodio asociado a hipertensión."
        ),
        category="nutricion", tier="PREFERENCIAS", priority=45, severity="info",
        references=("OMS (2023) — sodium intake recommendation"),
        conflicts=(),
        action="ajustar_menus",
        alternative="Sal en mesa (no en cocina), consomés bajos en sodio, especias.",
        test="'bajo_en_sal' in preferences",
    ),
    Rule(
        id="PREF-02",
        description="Preferencia: sin azúcar añadido",
        condition=lambda p: p.has_preference("sin_azucar_anadido"),
        conclusion=("Preferencia sin azúcar añadido: endulzar con fruta, canela o "
                    "stevia; azúcares libres <10 % de las calorías (OMS)."),
        explanation=(
            "Las guías de la OMS sitúan el límite de azúcares libres en menos del "
            "10 % de la ingesta energética (ideal <5 %). El menú evita azúcares "
            "añadidos y usa la dulzor natural de la fruta o canela, respetando la "
            "preferencia declarada."
        ),
        category="nutricion", tier="PREFERENCIAS", priority=45, severity="info",
        references=("OMS (2015) — sugars intake guideline"),
        conflicts=(),
        action="ajustar_menus",
        alternative="Fruta fresca, canela, vainilla, dátil en puré.",
        test="'sin_azucar_anadido' in preferences",
    ),
    Rule(
        id="PREF-03",
        description="Preferencia: alta proteína",
        condition=lambda p: p.has_preference("alta_proteina"),
        conclusion=("Preferencia de alta proteína: priorizar huevo, pollo, pescado, "
                    "legumbres y lácteos en cada comida sin superar el rango "
                    "recomendado por kg de peso."),
        explanation=(
            "La preferencia se respeta dentro del rango seguro calculado para el "
            "perfil (ver NUT-15): más proteína que la media sí, pero no por encima "
            "de lo recomendado sin supervisión, especialmente si hay compromiso "
            "renal no declarado."
        ),
        category="nutricion", tier="PREFERENCIAS", priority=44, severity="info",
        references=("ISSN Position Stand — protein (2017)"),
        conflicts=(),
        action="ajustar_menus",
        alternative="Batidos de yogur y avena, huevos, atún, tofu.",
        test="'alta_proteina' in preferences",
    ),
    Rule(
        id="PREF-04",
        description="Preferencia: económica",
        condition=lambda p: p.has_preference("economica"),
        conclusion=("Preferencia económica: base de legumbres, huevo, avena, arroz "
                    "y pollo entero — proteína de bajo costo por gramo."),
        explanation=(
            "Un plan sostenible económicamente aumenta la adherencia a largo "
            "plazo. Legumbres, huevo y avena ofrecen la mejor relación proteína/"
            "costo, y el menú se construye con ingredientes de temporada para "
            "mantener el presupuesto."
        ),
        category="nutricion", tier="PREFERENCIAS", priority=43, severity="info",
        references=("FAO — affordable protein sources",
                    "AND — cost-effective healthy eating"),
        conflicts=(),
        action="ajustar_menus",
        alternative="Lentejas, huevo, pollo, avena, papa, bananas.",
        test="'economica' in preferences",
    ),
    Rule(
        id="PREF-05",
        description="Preferencia: preparación rápida",
        condition=lambda p: p.has_preference("rapida"),
        conclusion="Preferencia de comida rápida: menús con ≤20 min de preparación y batch cooking dominical.",
        explanation=(
            "El tiempo de preparación es una de las principales barreras de la "
            "adherencia alimentaria. El sistema prioriza recetas de ≤20 minutos y "
            "técnicas de cocina por lotes para que el plan sea viable entre semana."
        ),
        category="nutricion", tier="PREFERENCIAS", priority=42, severity="info",
        references=("AND — behavioral approaches to healthy eating"),
        conflicts=(),
        action="ajustar_menus",
        alternative="Un bowl de arroz + huevo + verdura congelada en 12 min.",
        test="'rapida' in preferences",
    ),

    # ══ SEGUIMIENTO — consejos transversales ═════════════════════════════════

    Rule(
        id="SEG-02",
        description="Mediciones cada 4 semanas",
        condition=lambda p: p.imc > 0 and p.tdee > 0,
        conclusion=("Medir peso y medidas cada 4 semanas en las mismas condiciones "
                    "(ayunas, mismo día/hora) para evaluar la tendencia real."),
        explanation=(
            "El peso fluctúa día a día por agua y sodio; solo la tendencia de "
            "varias semanas refleja cambios de grasa o músculo. Evaluar cada 4 "
            "semanas evita reacciones a ruido y permite ajustar el plan con datos."
        ),
        category="seguimiento", tier="SEGUIMIENTO", priority=40, severity="info",
        references=("ACSM Guidelines (11ª ed.) — assessment follow-up"),
        conflicts=(),
        action="orientar",
        alternative="Registrar también cintura y cómo calza la ropa.",
        test="imc > 0 y tdee > 0 (evaluación completa)",
    ),
    Rule(
        id="SEG-03",
        description="Sueño 7–9 horas (8–10 en adolescentes)",
        condition=lambda p: p.objective != "",
        conclusion=("Garantizar 7–9 horas de sueño (8–10 si es adolescente, AASM) "
                    "para la recuperación, el control del apetito y el rendimiento."),
        explanation=(
            "La privación de sueño aumenta la grelina (hambre) y reduce la "
            "sensibilidad a la insulina, saboteando cualquier objetivo corporal. "
            "La AASM fija 7–9 h en adultos y 8–10 h en adolescentes; por eso el "
            "sistema trata el sueño como parte del plan, no como consejo accesorio."
        ),
        category="seguimiento", tier="SEGUIMIENTO", priority=45, severity="info",
        references=("AASM/SRS — sleep duration recommendations (2016)",
                    "NIH — sleep & metabolic health"),
        conflicts=(),
        action="orientar",
        alternative="Rutina fija de acostarse, sin cafeína 6 h antes de dormir.",
        test="evaluación con objetivo declarado",
    ),
    Rule(
        id="SEG-06",
        description="Actividad diaria — pasos y romper el sedentarismo",
        condition=lambda p: p.activity_level in ("sedentario", "ligero", "moderado"),
        conclusion=("Romper el sedentarismo: levantarse y moverse 3–5 min cada hora "
                    "y caminar 7 000–10 000 pasos diarios como base."),
        explanation=(
            "La OMS (2020) recomienda limitar el tiempo sedentario; aun cumpliendo "
            "el mínimo de ejercicio, permanecer sentado muchas horas tiene efectos "
            "adversos propios. Micro-descansos activos y una meta de pasos "
            "accesible sostienen la actividad fuera del entrenamiento."
        ),
        category="seguimiento", tier="SEGUIMIENTO", priority=38, severity="info",
        references=("OMS (2020) — sedentary behaviour",
                    "ACSM — steps per day"),
        conflicts=(),
        action="orientar",
        alternative="Alarma horaria de 5 min de marcha; subir escaleras.",
        test="activity_level en sedentario/ligero/moderado",
    ),
    Rule(
        id="SEG-07",
        description="Higiene alimentaria y etiquetado",
        condition=lambda p: len(p.allergies) > 0 or len(p.intolerances) > 0,
        conclusion=("Con alergias/intolerancias declaradas: revisar la etiqueta en "
                    "cada compra (alérgenos ocultos en salsas y ultraprocesados) y "
                    "cocinar por separado para evitar contaminación cruzada."),
        explanation=(
            "Los alérgenos más frecuentes aparecen en productos «inesperados» "
            "(salsas, panificados, embutidos). La regla complementa el filtrado "
            "automático del plan recordando que la seguridad final depende de la "
            "lectura humana de la etiqueta: el sistema no puede garantizar trazas."
        ),
        category="nutricion", tier="SEGUIMIENTO", priority=48, severity="media",
        references=("FDA/EU — food labeling regulations",
                    "AAAAI/ACAAI — Food Allergy Practice Parameter"),
        conflicts=(),
        action="orientar",
        alternative="Listas de compra con alérgenos marcados; utensilios separados.",
        test="hay alergias o intolerancias",
    ),
]

# Normalización del contrato público: `references` SIEMPRE es una tupla de
# cadenas. Algunas reglas se definieron con una cadena suelta (paréntesis de
# agrupación sin coma); aquí se garantiza el tipo estable que esperan el motor,
# las explicaciones y los exportadores (auditoría de consistencia).
RULES = [
    r._replace(references=(r.references,) if isinstance(r.references, str)
               else tuple(r.references))
    for r in RULES
]


# ──────────────────────────────────────────────
#  Funciones de consulta
# ──────────────────────────────────────────────

def get_rules_by_category(category: str) -> list[Rule]:
    """Retorna las reglas filtradas por categoría."""
    return [r for r in RULES if r.category == category]


def get_all_categories() -> list[str]:
    """Retorna las categorías únicas de la base de conocimiento."""
    return list(dict.fromkeys(r.category for r in RULES))


def get_rule(rule_id: str) -> Rule | None:
    """Busca una regla por su identificador."""
    return next((r for r in RULES if r.id == rule_id), None)


def rules_by_tier() -> dict[str, list[Rule]]:
    """Agrupa las reglas por tier de la jerarquía de seguridad."""
    out: dict[str, list[Rule]] = {}
    for r in RULES:
        out.setdefault(r.tier, []).append(r)
    return out
