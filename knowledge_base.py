"""
knowledge_base.py
=================
Base de conocimiento del Sistema Experto de Nutrición y Fitness.

Representa el conocimiento usando el modelo Objeto-Atributo-Valor
mediante reglas de producción (IF-THEN).

Cada regla tiene:
  - id:          identificador único
  - description: nombre de la regla
  - condition:   función lambda que evalúa el perfil del usuario
  - conclusion:  texto de la conclusión generada
  - explanation: texto explicativo para el módulo de explicación
  - category:    "nutricion" | "entrenamiento" | "seguimiento" | "alerta" | "biomecánica"
"""

from typing import NamedTuple, Callable
from user_profile import UserProfile


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


# ──────────────────────────────────────────────
#  Base de Conocimiento
# ──────────────────────────────────────────────

RULES: list[Rule] = [

    # ── NUTRICIÓN ────────────────────────────────────────────────────────────

    Rule(
        id="NUT-01",
        description="Déficit calórico para pérdida de grasa",
        condition=lambda p: p.objective == "perdida_grasa",
        conclusion="Aplicar déficit calórico de 500 kcal/día sobre el TDEE.",
        explanation=(
            "Su objetivo es la pérdida de grasa. Consumir 500 kcal menos que su gasto "
            "diario produce un déficit semanal de ~3,500 kcal, equivalente a ~0.5 kg de "
            "grasa corporal perdida por semana, un ritmo considerado seguro y sostenible."
        ),
        category="nutricion",
    ),
    Rule(
        id="NUT-02",
        description="Superávit calórico para aumento muscular",
        condition=lambda p: p.objective == "aumento_muscular",
        conclusion="Aplicar superávit calórico de 400 kcal/día sobre el TDEE.",
        explanation=(
            "Para ganar masa muscular se requiere un superávit energético moderado. "
            "400 kcal adicionales favorecen la síntesis proteica sin generar exceso "
            "de grasa corporal, especialmente combinado con entrenamiento de fuerza."
        ),
        category="nutricion",
    ),
    Rule(
        id="NUT-03",
        description="Déficit leve para definición",
        condition=lambda p: p.objective == "definicion",
        conclusion="Aplicar déficit calórico de 250 kcal/día para preservar músculo.",
        explanation=(
            "La definición muscular requiere reducir la grasa sin sacrificar el músculo. "
            "Un déficit leve de 250 kcal, junto con alta ingesta proteica, logra este "
            "balance de forma eficiente."
        ),
        category="nutricion",
    ),
    Rule(
        id="NUT-04",
        description="Calorías de mantenimiento",
        condition=lambda p: p.objective in ("mantenimiento", "recomposicion"),
        conclusion="Consumir las calorías equivalentes al TDEE.",
        explanation=(
            "Para mantenimiento o recomposición corporal se recomienda consumir exactamente "
            "lo que el cuerpo gasta (TDEE). La diferencia radica en la distribución de "
            "macronutrientes: mayor proteína para la recomposición."
        ),
        category="nutricion",
    ),
    Rule(
        id="NUT-05",
        description="Alta proteína para pérdida de grasa y definición",
        condition=lambda p: p.objective in ("perdida_grasa", "definicion"),
        conclusion="Priorizar alta ingesta proteica (35–40% de las calorías totales).",
        explanation=(
            "La proteína tiene el mayor efecto saciante y termogénico. Una ingesta alta "
            "durante un déficit calórico preserva la masa muscular y acelera la recuperación."
        ),
        category="nutricion",
    ),
    Rule(
        id="NUT-06",
        description="Hidratación recomendada",
        condition=lambda p: p.weight > 0,
        conclusion="Consumir entre 2 y 3 litros de agua diarios (mínimo 35 ml/kg de peso corporal).",
        explanation=(
            "La hidratación adecuada optimiza el metabolismo, la recuperación muscular y "
            "los procesos de lipólisis (quema de grasa). El mínimo recomendado es 35 ml "
            "por kilogramo de peso corporal al día."
        ),
        category="nutricion",
    ),
    Rule(
        id="NUT-07",
        description="Control de IMC bajo peso",
        condition=lambda p: p.imc < 18.5 and p.imc > 0,
        conclusion="El IMC indica bajo peso. Aumentar ingesta calórica de forma progresiva.",
        explanation=(
            "Con un IMC inferior a 18.5 existe riesgo de deficiencia nutricional. "
            "Se recomienda aumentar el aporte calórico de manera gradual priorizando "
            "alimentos nutritivos y con alta densidad energética."
        ),
        category="nutricion",
    ),
    Rule(
        id="NUT-08",
        description="Alerta obesidad",
        condition=lambda p: p.imc >= 30 and p.imc > 0,
        conclusion="IMC indica obesidad. Se recomienda control médico y nutricional especializado.",
        explanation=(
            "Un IMC ≥ 30 se clasifica como obesidad (OMS). En este rango, el sistema "
            "proporciona orientación general, pero se recomienda encarecidamente la "
            "supervisión de un profesional de salud para el seguimiento personalizado."
        ),
        category="alerta",
    ),
    Rule(
        id="NUT-09",
        description="Plan vegano — exclusión de productos animales",
        condition=lambda p: p.diet_type == "vegano",
        conclusion="Plan nutricional 100% vegetal. Proteínas de legumbres, tofu, tempeh y semillas.",
        explanation=(
            "El usuario sigue una dieta vegana. El plan excluye todas las carnes, lácteos "
            "y huevos, utilizando fuentes proteicas vegetales de alto valor biológico como "
            "legumbres, quinoa, tofu y combinaciones complementarias."
        ),
        category="nutricion",
    ),
    Rule(
        id="NUT-10",
        description="Plan vegetariano — sin carne",
        condition=lambda p: p.diet_type == "vegetariano",
        conclusion="Plan nutricional vegetariano. Proteínas de huevo, lácteos y legumbres.",
        explanation=(
            "El usuario sigue una dieta vegetariana. El plan excluye carnes rojas, aves y "
            "pescado, pero incluye proteínas de calidad como huevos, queso, yogur y legumbres."
        ),
        category="nutricion",
    ),
    Rule(
        id="NUT-11",
        description="Filtro alergia a lactosa",
        condition=lambda p: "lactosa" in p.allergies,
        conclusion="Plan sin lácteos: sustituir leche por bebida vegetal, queso por alternativas sin lactosa.",
        explanation=(
            "La intolerancia a la lactosa impide la digestión del azúcar de la leche. "
            "Se eliminan todos los lácteos del plan y se reemplazan por bebidas vegetales "
            "fortificadas (avena, almendra, soya) y alternativas sin lactosa."
        ),
        category="nutricion",
    ),
    Rule(
        id="NUT-12",
        description="Filtro alergia a gluten / celiaquía",
        condition=lambda p: "gluten" in p.allergies,
        conclusion="Plan libre de gluten: eliminar trigo, cebada y centeno. Usar arroz, quinoa y avena certificada.",
        explanation=(
            "La celiaquía o sensibilidad al gluten requiere eliminar completamente el trigo, "
            "la cebada y el centeno. El plan utiliza cereales naturalmente libres de gluten: "
            "arroz, quinoa, mijo, maíz y avena certificada sin contaminación cruzada."
        ),
        category="nutricion",
    ),

    # ── ENTRENAMIENTO — CASA ──────────────────────────────────────────────────

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
            "Para principiantes en casa con objetivo de pérdida de grasa, un circuito de "
            "cuerpo completo de 3 días semanales combina fuerza y cardio, maximizando el "
            "gasto calórico sin requerir equipo especializado."
        ),
        category="entrenamiento",
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
        category="entrenamiento",
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
        category="entrenamiento",
    ),

    # ── ENTRENAMIENTO — GIMNASIO ──────────────────────────────────────────────

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
        category="entrenamiento",
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
        category="entrenamiento",
    ),
    Rule(
        id="TRAIN-GYM-03",
        description="Rutina gimnasio — intermedio",
        condition=lambda p: (
            p.training_place == "gimnasio"
            and p.experience == "intermedio"
        ),
        conclusion="Rutina gimnasio: Split 4 días — Empuje / Jalar / Piernas / Cuerpo completo.",
        explanation=(
            "El split de 4 días permite mayor volumen por grupo muscular que el Full Body, "
            "favoreciendo la hipertrofia en usuarios con más de 6 meses de experiencia."
        ),
        category="entrenamiento",
    ),
    Rule(
        id="TRAIN-GYM-04",
        description="Rutina gimnasio — avanzado",
        condition=lambda p: (
            p.training_place == "gimnasio"
            and p.experience == "avanzado"
        ),
        conclusion="Rutina gimnasio: Split 5–6 días — PPL doble (Push-Pull-Legs x2 semana).",
        explanation=(
            "Usuarios avanzados necesitan mayor frecuencia y volumen para continuar "
            "progresando. El PPL doble (6 días) ofrece 2 estímulos semanales por grupo "
            "muscular con periodización avanzada."
        ),
        category="entrenamiento",
    ),

    # ── SEGURIDAD BIOMECÁNICA ─────────────────────────────────────────────────

    Rule(
        id="BIO-01",
        description="Adulto mayor (>70 años) — restricción de alto impacto",
        condition=lambda p: p.age > 70,
        conclusion="Edad avanzada: excluir ejercicios de alto impacto articular. Rutina de movilidad y fuerza suave.",
        explanation=(
            "A partir de los 70 años, los cartílagos articulares y la densidad ósea están "
            "significativamente reducidos. Los ejercicios pliométricos y los levantamientos "
            "olímpicos generan fuerzas de impacto que pueden causar lesiones graves. Se "
            "prioriza la movilidad, el equilibrio y la prevención de sarcopenia."
        ),
        category="biomecánica",
    ),
    Rule(
        id="BIO-02",
        description="Usuario menor de edad (<16 años) — rutina de movilidad",
        condition=lambda p: p.age < 16,
        conclusion="Edad: menor de 16 años. Excluir cargas pesadas. Solo movilidad, coordinación y peso corporal.",
        explanation=(
            "En menores de 16 años las placas de crecimiento óseo (epífisis) aún están "
            "abiertas. Las cargas axiales elevadas pueden lesionarlas permanentemente, "
            "comprometiendo el crecimiento. Se recomienda exclusivamente trabajo de "
            "movilidad, coordinación y calistenia ligera supervisada."
        ),
        category="biomecánica",
    ),
    Rule(
        id="BIO-03",
        description="Obesidad mórbida — protección articular de rodilla",
        condition=lambda p: p.imc >= 40 and p.imc > 0,
        conclusion="Obesidad mórbida (IMC >= 40): eliminar saltos e impacto en rodillas. Ejercicio acuático o en máquinas.",
        explanation=(
            "Con un IMC ≥ 40, las rodillas soportan una carga equivalente a 4–6 veces el "
            "peso corporal durante ejercicios de impacto. Esto genera deterioro acelerado "
            "del cartílago patelar. Se recomiendan actividades de bajo impacto: natación, "
            "bicicleta estática, remo y ejercicios en máquinas guiadas."
        ),
        category="biomecánica",
    ),

    # ── FILTROS DE LESIONES ───────────────────────────────────────────────────

    Rule(
        id="LES-01",
        description="Lesión lumbar — adaptar ejercicios axiales",
        condition=lambda p: "lumbar" in p.injuries,
        conclusion="Lesión lumbar detectada: sustituir sentadilla libre por prensa de piernas. Evitar peso muerto convencional.",
        explanation=(
            "Los ejercicios axiales (sentadilla libre, peso muerto) someten la columna "
            "lumbar a cargas de compresión elevadas. Con lesión lumbar, se reemplazan por "
            "ejercicios de cadena cerrada con soporte (prensa de piernas, extensiones) "
            "que aislan la musculatura sin comprometer la columna."
        ),
        category="lesión",
    ),
    Rule(
        id="LES-02",
        description="Lesión de rodilla — cadena abierta",
        condition=lambda p: "rodilla" in p.injuries,
        conclusion="Lesión de rodilla detectada: eliminar sentadillas profundas. Usar extensiones de pierna y ejercicios de cadena abierta.",
        explanation=(
            "Las lesiones de rodilla (LCA, LCP, menisco) contraindican ejercicios que "
            "generen fuerzas de cizallamiento en la articulación. Se sustituyen las "
            "sentadillas por ejercicios de cadena abierta (extensiones de pierna, curl "
            "femoral) y trabajo de cuádriceps isométrico para proteger la articulación."
        ),
        category="lesión",
    ),
    Rule(
        id="LES-03",
        description="Lesión de hombro — eliminar press y overhead",
        condition=lambda p: "hombro" in p.injuries,
        conclusion="Lesión de hombro detectada: eliminar press militar y elevaciones sobre la cabeza. Sustituir por jalones y remo.",
        explanation=(
            "Las lesiones de hombro (manguito rotador, impingement) se agravan con "
            "movimientos overhead (sobre la cabeza). Se eliminan el press militar, "
            "el press inclinado alto y las elevaciones laterales, sustituyéndolos por "
            "jalones al pecho, remo en polea y trabajo de manguito rotador externo."
        ),
        category="lesión",
    ),

    # ── SEGUIMIENTO ───────────────────────────────────────────────────────────

    Rule(
        id="SEG-01",
        description="Alerta sedentarismo con obesidad",
        condition=lambda p: p.activity_level == "sedentario" and p.imc >= 25,
        conclusion="Aumentar gradualmente el nivel de actividad física. Iniciar con caminatas diarias.",
        explanation=(
            "La combinación de sedentarismo y sobrepeso/obesidad representa un riesgo "
            "cardiovascular elevado. Iniciar con 30 minutos de caminata diaria y progresar "
            "de forma gradual es la estrategia más segura."
        ),
        category="seguimiento",
    ),
    Rule(
        id="SEG-02",
        description="Recomendación de seguimiento cada 4 semanas",
        condition=lambda p: True,
        conclusion="Realizar mediciones de peso y composición corporal cada 4 semanas para evaluar progreso.",
        explanation=(
            "El seguimiento periódico permite detectar estancamientos y ajustar el plan "
            "calórico o de entrenamiento. Se recomienda pesarse en las mismas condiciones "
            "(misma hora, mismo día, en ayunas)."
        ),
        category="seguimiento",
    ),
    Rule(
        id="SEG-03",
        description="Descanso y recuperación",
        condition=lambda p: True,
        conclusion="Garantizar 7–9 horas de sueño por noche para optimizar la recuperación muscular.",
        explanation=(
            "Durante el sueño se libera hormona de crecimiento (GH) y se reparan las "
            "fibras musculares dañadas durante el entrenamiento. Dormir menos de 6 horas "
            "reduce la síntesis proteica y aumenta la retención de grasa."
        ),
        category="seguimiento",
    ),
    Rule(
        id="SEG-04",
        description="Alerta edad avanzada (50+)",
        condition=lambda p: 50 <= p.age <= 70,
        conclusion="Consultar con un médico antes de iniciar cualquier programa de entrenamiento intenso.",
        explanation=(
            "A partir de los 50 años, factores como la sarcopenia, la densidad ósea y "
            "el riesgo cardiovascular requieren una evaluación médica previa. El sistema "
            "puede orientar, pero no reemplaza la supervisión clínica."
        ),
        category="alerta",
    ),
    Rule(
        id="SEG-05",
        description="Cardio para usuarios con actividad sedentaria o ligera",
        condition=lambda p: p.activity_level in ("sedentario", "ligero"),
        conclusion="Incorporar mínimo 150 minutos de actividad cardiovascular moderada por semana (OMS).",
        explanation=(
            "La OMS recomienda 150–300 minutos semanales de actividad moderada para adultos. "
            "Para usuarios con bajo nivel de actividad, esta base cardio mejora la salud "
            "cardiovascular y aumenta el TDEE."
        ),
        category="seguimiento",
    ),
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
