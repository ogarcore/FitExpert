"""
exercise_info.py
================
Catálogo informativo de ejercicios de FitExpert (cliente web).

Complementa a `training.EXERCISE_LIBRARY` (que contiene los datos de
prescripción: series, músculo, impacto, lesiones, equipamiento) con una
fICHA EXPLICATIVA por ejercicio: descripción, ejecución paso a paso,
errores comunes, consejos de seguridad, respiración, tempo, regresión y
progresión.

No modifica ni duplica la lógica de generación de rutinas: solo consume
los datos existentes. Las zonas lesivas de cada ficha se toman SIEMPRE de
`EXERCISE_LIBRARY[...]["lesiones"]` (matriz única del proyecto).

Identificación:
    slug = slugify(nombre)  →  minúsculas, sin tildes, sin espacios,
    guiones bajos. Ejercicios repetidos en varios días resuelven al
    MISMO slug y a la MISMA ficha.

Imágenes:
    Se esperan en assets/exercises/<slug>.(png|jpg|jpeg|webp).
    `resolve_exercise_image(slug)` devuelve la ruta o None (nunca lanza).
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from training import EXERCISE_LIBRARY
from user_profile import INJURY_OPTIONS

ASSETS_DIR = Path(__file__).resolve().parent / "assets" / "exercises"
_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")


# ──────────────────────────────────────────────
#  Slugs
# ──────────────────────────────────────────────

def slugify(nombre: str) -> str:
    """Convierte un nombre de ejercicio en slug estable (ascii, _)."""
    s = unicodedata.normalize("NFKD", str(nombre).lower())
    s = s.encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s


# ──────────────────────────────────────────────
#  Ficha mínima por defecto (fallback seguro)
# ──────────────────────────────────────────────

_DEFAULT_RESP = "Exhala en el esfuerzo, inhala en la fase de retorno."
_DEFAULT_TEMPO = "2-0-2 (2 s bajando, sin pausa, 2 s subiendo)"


def _ficha_base(entry: dict) -> dict:
    return {
        "nombre": entry.get("nombre", "Ejercicio"),
        "categoria": _categoria(entry.get("musculo", "")),
        "grupo_muscular": entry.get("musculo", "—"),
        "secundarios": [],
        "descripcion": "Ejercicio incluido en la biblioteca del sistema.",
        "pasos": [],
        "errores": [],
        "consejos": [],
        "respiracion": _DEFAULT_RESP,
        "tempo": _DEFAULT_TEMPO,
        "regresion": "",
        "progresion": "",
        "lesiones": list(entry.get("lesiones", [])),
        "equipamiento": list(entry.get("equipamiento", [])),
        "imagen": None,
    }


_CATEGORIA_POR_PRIMER_GRUPO = {
    "cuádriceps": "Piernas", "glúteos": "Piernas", "isquiotibiales": "Piernas",
    "aductores": "Piernas",
    "pecho": "Pecho",
    "espalda": "Espalda", "dorsal": "Espalda", "romboides": "Espalda",
    "hombros": "Hombros", "deltoides": "Hombros", "manguito": "Hombros",
    "bíceps": "Brazos", "tríceps": "Brazos", "braquial": "Brazos",
    "core": "Core", "abdomen": "Core", "oblicuos": "Core",
    "cardio": "Cardio",
    "movilidad": "Movilidad y equilibrio", "flexibilidad": "Movilidad y equilibrio",
    "equilibrio": "Movilidad y equilibrio",
    "funcional": "Funcional",
}


def _categoria(musculo: str) -> str:
    primero = musculo.split("/")[0].strip().lower()
    for clave, cat in _CATEGORIA_POR_PRIMER_GRUPO.items():
        if clave in primero:
            return cat
    return "General"


# ──────────────────────────────────────────────
#  Contenido específico por ejercicio (clave: EXERCISE_LIBRARY)
# ──────────────────────────────────────────────

_E = lambda **kw: kw  # atajo de legibilidad

_EXTRA: dict[str, dict] = {
    "sentadilla_libre": _E(
        descripcion="Sentadilla profunda con barra sobre los trapecios; ejercicio compuesto de tren inferior.",
        pasos=["Barra apoyada en trapecios, pies al ancho de hombros.", "Activa el abdomen y baja con la espalda neutra.", "Baja hasta muslos paralelos o lo que permita tu movilidad.", "Empuja con los talones para volver arriba."],
        errores=["Rodillas que colapsan hacia dentro.", "Talones que se levantan del suelo.", "Redondear la zona lumbar al bajar."],
        consejos=["Calienta 5 minutos y empieza con carga ligera.", "Mirada al frente, pecho abierto."],
        respiracion="Inhala al bajar; exhala al subir.", tempo="3-0-1 (bajar controlado, subir con intención)",
        regresion="Sentadilla goblet con mancuerna o sentadilla asistida con apoyo.",
        progresion="Aumentar carga gradual o sentadilla búlgara.",
        secundarios=["Isquiotibiales", "Core", "Espalda baja"]),
    "prensa_piernas": _E(
        descripcion="Empuje de plataforma con las piernas en máquina; reduce la carga axial en la espalda.",
        pasos=["Espalda y glúteos apoyados contra el respaldo.", "Pies al ancho de hombros sobre la plataforma.", "Baja controlado hasta ~90° de rodilla.", "Extiende sin bloquear las rodillas."],
        errores=["Separar la espalda baja del respaldo.", "Bloquear las rodillas al final.", "Bajar demasiado provocando dolor lumbar."],
        consejos=["Rango de movimiento completo pero sin forzar."],
        regresion="Prensa con rango corto o sentadilla con peso corporal.",
        progresion="Más carga o tempo lento 3-1-3.",
        secundarios=["Glúteos", "Gemelos"]),
    "sentadilla_goblet": _E(
        descripcion="Sentadilla sosteniendo una mancuerna o pesa rusa frente al pecho.",
        pasos=["Sostén la mancuerna vertical contra el pecho.", "Codos apuntando al suelo.", "Baja entre los talones con la espalda neutra.", "Sube empujando el suelo."],
        errores=["Codos hacia fuera perdiendo la postura.", "Peso muy adelantado que arquea la espalda."],
        consejos=["Ideal para aprender el patrón de sentadilla."],
        regresion="Sentadilla con peso corporal.", progresion="Sentadilla libre con barra.",
        secundarios=["Core", "Glúteos"]),
    "sentadilla_corporal": _E(
        descripcion="Sentadilla con el propio peso; base de todos los patrones de empuje de piernas.",
        pasos=["Pies al ancho de hombros.", "Brazos al frente para equilibrio.", "Baja empujando cadera atrás y abajo.", "Vuelve a arriba contrayendo glúteos."],
        errores=["Rodillas hacia dentro.", "Inclinarse demasiado hacia delante."],
        consejos=["Domina la técnica antes de añadir carga."],
        regresion="Sentadilla asistida con apoyo.", progresion="Sentadilla goblet o con salto controlado.",
        secundarios=["Glúteos", "Core"]),
    "zancada_estatica": _E(
        descripcion="Paso largo hacia delante con flexión de ambas piernas; trabajo unilateral.",
        pasos=["Da un paso largo hacia delante.", "Baja la rodilla trasera casi al suelo.", "La rodilla delantera no supera mucho la punta del pie.", "Vuelve y alterna o repite el mismo lado."],
        errores=["Paso demasiado corto que carga de más la rodilla delantera.", "Tronco inclinado hacia delante."],
        consejos=["Apóyate en una pared si pierdes equilibrio."],
        regresion="Zancada con apoyo o rango reducido.", progresion="Mancuernas en cada mano o zancada caminando.",
        secundarios=["Glúteos", "Isquiotibiales", "Equilibrio"]),
    "extension_piernas": _E(
        descripcion="Extensión de rodilla en máquina de cuádriceps, aislando el músculo.",
        pasos=["Ajusta el respaldo y el rodillo sobre los tobillos.", "Extiende las piernas con control.", "Baja sin que el peso choque.", "Repite sin balancear el tronco."],
        errores=["Rodillas que se cierran al extender.", "Impulsar el peso con balanceo."],
        consejos=["Rango controlado para cuidar la rodilla."],
        regresion="Peso corporal sin máquina.", progresion="Más carga o pausa de 2 s arriba.",
        secundarios=["Vastos"]),
    "press_banca_mancuernas": _E(
        descripcion="Press de pecho con mancuernas en banco plano; mayor rango y simetría que la barra.",
        pasos=["Mancuernas junto al pecho, codos a ~45°.", "Empuja hacia arriba sin chocar las mancuernas.", "Baja controlado a la altura del pecho.", "Mantén la escápula apoyada."],
        errores=["Codos abiertos a 90°.", "Arquear la zona lumbar."],
        consejos=["Mancuernas permiten un estiramiento más seguro."],
        regresion="Press inclinado ligero o flexiones inclinadas.", progresion="Más peso o press declinado.",
        secundarios=["Hombro anterior", "Tríceps"]),
    "flexiones": _E(
        descripcion="Flexión de brazos apoyando manos y pies; clásico de pecho con peso corporal.",
        pasos=["Manos al ancho de hombros, cuerpo en línea recta.", "Baja el pecho hacia el suelo.", "Codos a ~45° del tronco.", "Empuja hasta extender los brazos."],
        errores=["Cadera hundida o elevada.", "Codos muy abiertos.", "Bajar solo hasta la mitad."],
        consejos=["Activa glúteos y abdomen durante todo el movimiento."],
        regresion="Flexiones inclinadas o contra la pared.", progresion="Flexiones con pies elevados o peso extra.",
        secundarios=["Tríceps", "Hombro anterior", "Core"]),
}

# Rellena con un bloque genérico breve los ejercicios sin entrada detallada,
# y después se sobrescribe con los que sí tengan contenido específico.
# (Se hace así para mantener la ficha SIEMPRE completa y nunca romper.)


# Descripciones y variantes específicas por ejercicio (complementan al texto por categoría).
_EXT2: dict[str, dict] = {
    "sentadilla_bulgara": _E(descripcion="Sentadilla a una pierna con el pie trasero apoyado en banco; gran demanda unilateral.",
                             regresion="Sentadilla asistida a una pierna.", progresion="Más carga o pausa de 2 s abajo.", secundarios=["Glúteos", "Core"]),
    "hipthrust_barra": _E(descripcion="Empuje de cadera con barra apoyada en la parte baja del abdomen; pico de contracción de glúteos arriba.",
                          regresion="Puente de glúteos sin carga.", progresion="Más carga o pausa de 2 s arriba.", secundarios=["Isquiotibiales", "Core"]),
    "hipthrust_corporal": _E(descripcion="Empuje de cadera con peso corporal, base para progresar al hip thrust con barra.",
                             regresion="Elevación de cadera isométrica.", progresion="Hip thrust con barra.", secundarios=["Isquiotibiales"]),
    "puente_gluteo": _E(descripcion="Elevación de pelvis desde el suelo, activando glúteos y estabilizando la espalda baja.",
                        regresion="Elevación isométrica corta.", progresion="A una pierna o con banda.", secundarios=["Isquiotibiales", "Core"]),
    "peso_muerto": _E(descripcion="Elevación de barra desde el suelo hasta la cadera manteniendo la espalda neutra.",
                      regresion="Peso muerto rumano con poco peso.", progresion="Más carga o peso muerto déficit.", secundarios=["Glúteos", "Espalda", "Agarre"]),
    "curl_femoral": _E(descripcion="Flexión de rodilla en máquina para isquiotibiales.",
                       regresion="Puente de glúteos isométrico.", progresion="Más carga o tempo lento.", secundarios=["Glúteos"]),
    "peso_muerto_rumano": _E(descripcion="Bisagra de cadera con mancuernas, énfasis en isquiotibiales y glúteos.",
                             regresion="Más ligero y rango corto.", progresion="Más carga o a una pierna.", secundarios=["Glúteos", "Espalda baja"]),
    "nordic_curl": _E(descripcion="Flexión excéntrica de rodilla con apoyos; muy exigente para isquiotibiales.",
                      regresion="Deslizamiento con toalla.", progresion="Más recorrido.", secundarios=["Glúteos", "Gemelos"]),
    "sentadilla_sumo": _E(descripcion="Sentadilla con pies separados y puntas hacia afuera; trabaja aductores.",
                          regresion="Sentadilla sumo sin carga.", progresion="Con pesa rusa o más apertura.", secundarios=["Glúteos", "Core"]),
    "press_banca_barra": _E(descripcion="Press de pecho en banco plano con barra; el compuesto clásico de empuje horizontal.",
                            regresion="Press con mancuernas ligeras o flexiones inclinadas.", progresion="Más carga o press declinado.", secundarios=["Tríceps", "Hombro anterior"]),
    "flexiones_inclinadas": _E(descripcion="Flexión con las manos elevadas, reduciendo la carga; progresión intermedia.",
                               regresion="Flexión contra la pared.", progresion="Flexión estándar en el suelo.", secundarios=["Tríceps", "Hombro anterior"]),
    "aperturas_mancuernas": _E(descripcion="Apertura horizontal con mancuernas para aislar el pecho.",
                               regresion="Aperturas con menos peso o en polea baja.", progresion="Más rango o banco inclinado.", secundarios=["Hombro anterior"]),
    "fondos_pecho": _E(descripcion="Fondos en paralelas con tronco inclinado, énfasis en pecho inferior.",
                       regresion="Fondos en banco.", progresion="Más profundidad o peso lastrado.", secundarios=["Tríceps", "Hombro anterior"]),
    "press_cable": _E(descripcion="Press de pecho en cable cruzado; tensión constante durante todo el recorrido.",
                      regresion="Press con banda elástica.", progresion="Más carga o press inclinado en cable.", secundarios=["Tríceps", "Core"]),
    "remo_barra": _E(descripcion="Remo inclinado con barra, trabaja espalda media y bíceps.",
                     regresion="Remo con mancuerna unilateral ligero.", progresion="Más carga o pausa en la espalda.", secundarios=["Bíceps", "Espalda baja"]),
    "remo_mancuerna": _E(descripcion="Remo con una mancuerna apoyando la otra mano y rodilla en un banco.",
                         regresion="Remo con banda elástica sentado.", progresion="Más peso o tempo lento.", secundarios=["Bíceps"]),
    "jalon_polea": _E(descripcion="Jalón al pecho en polea para dorsales.",
                      regresion="Jalón con banda detrás de la puerta.", progresion="Dominadas asistidas.", secundarios=["Bíceps", "Romboides"]),
    "dominadas": _E(descripcion="Tracción de cuerpo completo colgado de una barra; dorsal y bíceps.",
                    regresion="Dominadas con banda o jalón al pecho.", progresion="Más repeticiones o lastre.", secundarios=["Bíceps", "Core"]),
    "remo_corporal": _E(descripcion="Remo invertido bajo una mesa o barra baja; escalable con la altura de los pies.",
                        regresion="Pies más flexionados o barra más alta.", progresion="Pies más elevados o barra más baja.", secundarios=["Bíceps", "Core"]),
    "facepull": _E(descripcion="Jalón a la cara en polea para romboides y manguito rotador.",
                   regresion="Con banda elástica a baja tensión.", progresion="Más carga o pausa externa.", secundarios=["Deltoides posterior"]),
    "remo_banda": _E(descripcion="Remo sentado con banda elástica, alternativa de bajo impacto al remo con barra.",
                     regresion="Banda más ligera o menor rango.", progresion="Banda más tensa o más recorrido.", secundarios=["Bíceps"]),
    "press_militar": _E(descripcion="Press vertical con barra sobre la cabeza para hombros.",
                        regresion="Press con mancuernas sentado.", progresion="Más carga o push press.", secundarios=["Tríceps", "Core"]),
    "press_mancuernas_hombro": _E(descripcion="Press vertical con mancuernas, mayor rango y estabilidad escapular.",
                                  regresion="Menos peso o rango corto.", progresion="Más peso o press Arnold.", secundarios=["Tríceps", "Core"]),
    "elevaciones_laterales": _E(descripcion="Elevación lateral con mancuernas para deltoides lateral.",
                                regresion="Con bandas o rango corto.", progresion="Más carga o pausa arriba.", secundarios=["Trapecio"]),
    "rotacion_externa": _E(descripcion="Rotación externa de hombro con banda para manguito rotador.",
                           regresion="Banda más ligera.", progresion="Más tensión o a 90° de abducción.", secundarios=["Deltoides posterior"]),
    "elevacion_frontal": _E(descripcion="Elevación frontal con mancuerna para deltoides anterior.",
                            regresion="Con banda o menos peso.", progresion="Más carga o alternando brazos.", secundarios=["Pecho superior"]),
    "press_arnold": _E(descripcion="Press con mancuernas rotando el agarre durante el recorrido.",
                       regresion="Press de hombros estándar.", progresion="Más peso o tempo lento.", secundarios=["Tríceps", "Core"]),
    "curl_barra": _E(descripcion="Curl de bíceps con barra recta o Z.",
                     regresion="Con banda elástica o alternado ligero.", progresion="Más carga o pausa arriba.", secundarios=["Braquial", "Antebrazo"]),
    "curl_mancuernas": _E(descripcion="Curl alterno con mancuernas, permite mayor rango.",
                          regresion="Curl con banda.", progresion="Más carga o tempo lento.", secundarios=["Braquial"]),
    "curl_martillo": _E(descripcion="Curl con agarre neutro, enfatiza braquial y antebrazo.",
                        regresion="Con menos peso.", progresion="Más carga o alternando.", secundarios=["Braquial", "Antebrazo"]),
    "curl_banda": _E(descripcion="Curl de bíceps con banda elástica, tensión constante.",
                     regresion="Banda más ligera.", progresion="Doble banda o pausa arriba.", secundarios=["Braquial"]),
    "press_frances": _E(descripcion="Extensión de tríceps tumbado con barra; énfasis en la cabeza larga.",
                        regresion="Con mancuernas o menos carga.", progresion="Más peso o banco inclinado.", secundarios=["Codo"]),
    "extension_triceps": _E(descripcion="Extensión de tríceps en polea con cuerda o barra.",
                            regresion="Con cuerda ligera.", progresion="Más carga o pausa abajo.", secundarios=["Codo"]),
    "fondos_triceps": _E(descripcion="Fondos en banco para tríceps, sin necesidad de máquinas.",
                         regresion="Menor rango o pies más flexionados.", progresion="Pies elevados o peso extra.", secundarios=["Hombro anterior"]),
    "kickback_triceps": _E(descripcion="Extensión de tríceps con mancuerna, tronco inclinado.",
                           regresion="Con menos peso o en polea baja.", progresion="Más carga o pausa arriba.", secundarios=["Hombro posterior"]),
    "plancha": _E(descripcion="Plancha abdominal en apoyo de antebrazos, estabilizando el tronco.",
                  regresion="Plancha de rodillas.", progresion="Plancha a un brazo o con movimiento.", secundarios=["Glúteos", "Hombros"]),
    "crunch": _E(descripcion="Encogimiento abdominal tumbado, trabajo de recto abdominal.",
                 regresion="Crunch a rango corto.", progresion="Con peso o en bicicleta abdominal.", secundarios=["Oblicuos"]),
    "plancha_lateral": _E(descripcion="Plancha de lado sobre un antebrazo, trabaja oblicuos y glúteo medio.",
                          regresion="Rodillas apoyadas.", progresion="Pierna superior elevada o con movimiento.", secundarios=["Glúteos", "Core"]),
    "elevacion_piernas": _E(descripcion="Elevación de piernas colgado de una barra para abdomen bajo.",
                            regresion="Elevación de rodillas.", progresion="Piernas extendidas o con lastre.", secundarios=["Flexores de cadera"]),
    "mountain_climbers": _E(descripcion="Carrera de rodillas al pecho en posición de plancha; core y cardio.",
                            regresion="Más lento o con flexiones suaves.", progresion="Más rápido o elevando más las rodillas.", secundarios=["Hombros", "Cardio"]),
    "dead_bug": _E(descripcion="Ejercicio de control lumbar alternando brazo y pierna opuesta tumbado boca arriba.",
                   regresion="Sin movimiento de piernas.", progresion="Con banda o peso en manos.", secundarios=["Oblicuos", "Glúteos"]),
    "rueda_abdominal": _E(descripcion="Deslizamiento frontal con rueda abdominal, gran exigencia de core.",
                          regresion="Deslizamiento de rodillas a corta distancia.", progresion="Más recorrido o de pie.", secundarios=["Hombros", "Dorsal"]),
    "jumping_jacks": _E(descripcion="Saltos abriendo y cerrando piernas y brazos; cardio clásico.",
                        regresion="Paso lateral sin salto.", progresion="Doble rebote o mayor amplitud.", secundarios=["Gemelos", "Hombros"]),
    "saltos_cuerda": _E(descripcion="Saltos a la comba a ritmo constante para cardio y coordinación.",
                        regresion="Simular sin cuerda.", progresion="Más velocidad o doble salto.", secundarios=["Gemelos", "Hombros"]),
    "bicicleta_estatica": _E(descripcion="Pedaleo estacionario de bajo impacto articular.",
                             regresion="Menos resistencia.", progresion="Más resistencia o intervalos.", secundarios=["Glúteos", "Gemelos"]),
    "remo_maquina": _E(descripcion="Rowing en máquina, cardio de cuerpo completo con énfasis en espalda.",
                       regresion="Menos resistencia y menor rango.", progresion="Más intensidad o intervalos.", secundarios=["Piernas", "Core"]),
    "caminata_inclinada": _E(descripcion="Caminata en cinta a inclinación moderada, bajo impacto.",
                             regresion="Menos inclinación o velocidad.", progresion="Más inclinación o duración.", secundarios=["Glúteos", "Gemelos"]),
    "burpees": _E(descripcion="Combinación de sentadilla, plancha y salto; alta demanda cardiovascular.",
                  regresion="Sin salto o apoyando manos en banco.", progresion="Más velocidad o con flexión completa.", secundarios=["Pecho", "Core"]),
    "movilidad_cadera": _E(descripcion="Rotaciones suaves de cadera para mejorar el rango articular.",
                           regresion="Sentado o con apoyo.", progresion="Más amplitud o círculos grandes.", secundarios=["Lumbar"]),
    "stretching_isquiotibiales": _E(descripcion="Estiramiento mantenido de isquiotibiales, sin rebotes.",
                                    regresion="Pierna flexionada o usando toalla.", progresion="Más rango o ambas piernas.", secundarios=["Gemelos", "Lumbar"]),
    "equilibrio_unilateral": _E(descripcion="Apoyo unipodal estático para equilibrio y estabilidad de tobillo.",
                                regresion="Sujetándose a una pared.", progresion="Ojos cerrados o superficie inestable.", secundarios=["Glúteos", "Core"]),
    "sentadilla_asistida": _E(descripcion="Sentadilla con apoyo (silla o pared) para aprender el patrón sin riesgo.",
                              regresion="Sentado en silla alta y subir.", progresion="Menos apoyo o sin apoyo.", secundarios=["Glúteos", "Core"]),
    "marcha_elevada": _E(descripcion="Marcha en el sitio elevando rodillas; activa piernas y core a baja intensidad.",
                         regresion="Marcha normal sin elevar.", progresion="Más ritmo o con apoyo en manos.", secundarios=["Flexores de cadera", "Core"]),
    "flexion_pared": _E(descripcion="Flexión apoyando las manos en la pared; versión accesible.",
                        regresion="Mayor distancia de la pared.", progresion="Flexiones sobre mesa o inclinadas.", secundarios=["Tríceps", "Hombros"]),
}


def _general_extra(key: str, entry: dict) -> dict:
    musculo = entry.get("musculo", "")
    cat = _categoria(musculo)
    patron = {
        "Piernas": (
            "Controla el movimiento durante todo el rango, sin balanceos.",
            ["Flexiona y extiende con la columna neutra.", "Mantén las rodillas alineadas con los pies.", "No bloquees las articulaciones al final.", "Respira de forma continua y controlada."],
            ["Compensar con la espalda lo que no hacen las piernas.", "Rango de movimiento reducido por prisa."],
            ["Calienta la zona antes de cargar.", "Prioriza técnica sobre peso."],
            "Peso corporal o rango reducido.",
            "Aumentar carga o añadir pausa en la parte baja.",
        ),
        "Pecho": (
            "Movimiento de empuje horizontal/vertical controlando la bajada.",
            ["Activa el core y estabiliza el tronco.", "Baja controlado hasta la altura del pecho.", "Mantén los codos a ~45° del cuerpo.", "Empuja sin bloquear bruscamente."],
            ["Codos excesivamente abiertos.", "Perder la tensión del core."],
            ["Escápulas pegadas al respaldo o estables.", "Evita dolor en hombros: reduce el rango."],
            "Versión inclinada o con banda elástica.",
            "Aumentar peso o frecuencia de series.",
        ),
        "Espalda": (
            "Tirón o remo controlado, sintiendo la contracción de la espalda.",
            ["Inicia el movimiento con la escápula.", "Mantén el pecho abierto.", "Tira del codo hacia atrás y abajo.", "Vuelve con control."],
            ["Usar impulso del tronco en lugar de la espalda.", "Redondear la columna al tirar."],
            ["Cuello relajado, mirada al frente.", "Evita tirones bruscos."],
            "Banda elástica o remo inclinado ligero.",
            "Más carga o pausa de 1 s en contracción.",
        ),
        "Hombros": (
            "Elevación o press controlado sin forzar el rango.",
            ["Activa el abdomen para no arquear.", "Movimiento controlado en ambas fases.", "Codos ligeramente flexionados.", "No balancees el tronco."],
            ["Subir los hombros hacia las orejas.", "Usar impulso para compensar."],
            ["Evita dolor anterior de hombro: reduce rango.", "Calienta con rotaciones suaves."],
            "Menos peso o rango parcial.",
            "Más carga o press Arnold.",
        ),
        "Brazos": (
            "Aislamiento controlado de bíceps o tríceps.",
            ["Codos fijos junto al cuerpo o al banco.", "Rango completo sin balancear.", "Contrae 1 s en la posición final.", "Baja con control."],
            ["Balancear el tronco para levantar más.", "Rango incompleto."],
            ["Controla siempre la fase excéntrica."],
            "Banda elástica o menos peso.",
            "Más carga o trabajo a tempo lento.",
        ),
        "Core": (
            "Ejercicio de estabilidad del tronco manteniendo la columna neutra.",
            ["Activa abdomen profundo y glúteos.", "Columna neutra de principio a fin.", "Movimiento controlado, sin rebotes.", "Mantén la respiración fluida."],
            ["Aguantar la respiración.", "Compensar con lumbares o cadera."],
            ["Si aparece dolor lumbar, detente y reduce dificultad."],
            "Apoyo de rodillas o rango reducido.",
            "Más tiempo bajo tensión o inestabilidad.",
        ),
        "Cardio": (
            "Bloque de trabajo cardiovascular a intensidad moderada.",
            ["Calienta 3-5 minutos suave.", "Mantén un ritmo en el que puedas hablar.", "Hidrátate antes y después.", "Enfría marchando suave."],
            ["Empezar demasiado fuerte.", "Ignorar señales de mareo o dolor."],
            ["Ante dolor torácico o mareo, detente y consulta a un profesional."],
            "Menos intensidad o duración.",
            "Más duración, inclinación o intervalos suaves.",
        ),
        "Movilidad y equilibrio": (
            "Movimiento suave orientado a rango articular o estabilidad.",
            ["Muévete dentro de un rango cómodo.", "Sin rebotes ni tirones.", "Respira lento y profundo.", "Usa apoyo si pierdes equilibrio."],
            ["Forzar el rango generando dolor.", "Aguantar la respiración."],
            ["El estiramiento debe sentirse, no doler."],
            "Menor rango o con apoyo.",
            "Mayor rango o sin apoyo.",
        ),
        "Funcional": (
            "Movimiento global de bajo impacto para adultos o retorno progresivo.",
            ["Muévete despacio y con control.", "Mantén la postura erguida.", "Coordina respiración y movimiento.", "Detente si aparece molestia."],
            ["Perder la postura al cansarse."],
            ["Usa apoyo (pared, silla) si lo necesitas."],
            "Sentado o con apoyo.",
            "De pie, sin apoyo o con pequeños pesos.",
        ),
    }
    desc, pasos, errores, consejos, reg, prog = patron.get(
        cat, patron["Funcional"])
    extra = _EXT2.get(key, {})
    return _E(
        descripcion=extra.get("descripcion") or f"{entry.get('nombre', key)}: {desc}",
        pasos=extra.get("pasos") or pasos,
        errores=extra.get("errores") or errores,
        consejos=extra.get("consejos") or consejos,
        regresion=extra.get("regresion") or reg,
        progresion=extra.get("progresion") or prog,
        secundarios=extra.get("secundarios", []))


def _build_catalog() -> dict[str, dict]:
    catalogo: dict[str, dict] = {}
    for key, entry in EXERCISE_LIBRARY.items():
        slug = slugify(entry["nombre"])
        ficha = _ficha_base(entry)
        extra = _EXTRA.get(key) or _general_extra(key, entry)
        ficha.update({k: v for k, v in extra.items() if v not in (None, "", []) or k in ("secundarios",)})
        ficha["slug"] = slug
        ficha["lib_key"] = key
        ficha["imagen"] = f"assets/exercises/{slug}"
        catalogo[slug] = ficha
    return catalogo


CATALOG: dict[str, dict] = _build_catalog()

# Índice por nombre exacto (como aparece en las rutinas) → ficha
_BY_NAME: dict[str, dict] = {f["nombre"]: f for f in CATALOG.values()}


def get_ficha(nombre_o_slug: str) -> dict:
    """Devuelve la ficha por nombre exacto o por slug; nunca lanza."""
    if not nombre_o_slug:
        return {}
    f = _BY_NAME.get(nombre_o_slug)
    if f:
        return f
    f = CATALOG.get(nombre_o_slug)
    if f:
        return f
    f = CATALOG.get(slugify(nombre_o_slug))
    if f:
        return f
    # Ficha mínima para ejercicios sin catálogo (robustez)
    return {
        "nombre": nombre_o_slug, "categoria": "—", "grupo_muscular": "—",
        "secundarios": [], "descripcion": "Información detallada no disponible todavía.",
        "pasos": [], "errores": [], "consejos": [], "respiracion": "", "tempo": "",
        "regresion": "", "progresion": "", "lesiones": [], "equipamiento": [],
        "imagen": None, "slug": slugify(nombre_o_slug), "lib_key": "",
    }


def resolve_exercise_image(slug: str) -> Path | None:
    """Devuelve la ruta de la imagen del ejercicio si existe, si no None."""
    try:
        for ext in _IMAGE_EXTS:
            p = ASSETS_DIR / f"{slug}{ext}"
            if p.is_file():
                return p
    except Exception:
        return None
    return None


def lesion_labels(lesion_keys) -> list[str]:
    """Etiquetas legibles de las zonas lesivas de una ficha (de la matriz)."""
    out = []
    for k in lesion_keys or []:
        out.append(INJURY_OPTIONS.get(k, k))
    return out
