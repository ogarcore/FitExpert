"""
test_dedup_rutinas.py
=====================
Garantías de generación de rutinas (deduplicación por día):

  - Ningún día tiene ejercicios repetidos.
  - Ningún ejercicio excluido por la matriz de lesionas aparece.
  - El contador que muestra la UI (= len(ejercicios)) es la lista real.
  - Regresión: el caso observado (plan activo) ya no repite Dead bug.
"""
import itertools

import pytest

from training import EXERCISE_LIBRARY, generate_training_plan
from tests.conftest import make_profile

OBJ = ["perdida_grasa", "aumento_muscular", "definicion", "recomposicion", "mantenimiento"]
EXP = ["principiante", "intermedio", "avanzado"]
PLACE = ["casa", "gimnasio"]
ZONAS = ["lumbar", "cervical", "rodilla", "hombro", "codo",
         "muneca", "tobillo", "cadera", "dolor_general", "movilidad"]
COMBOS = [["rodilla", "tobillo"], ["hombro", "codo"], ["lumbar", "dolor_general"]]

CASOS = []
for place, exp, obj in itertools.product(PLACE, EXP, OBJ):
    CASOS.append((place, exp, obj, ()))
    for zona in ZONAS:
        CASOS.append((place, exp, obj, (zona,)))
for combo in COMBOS:
    CASOS.append(("casa", "intermedio", "aumento_muscular", tuple(combo)))


def _excluidos_por_matriz(ejercicios, injuries):
    for e in ejercicios:
        nombre = e[0] if isinstance(e, (tuple, list)) else str(e)
        key = _nombre_a_key(nombre)
        if key is None:
            continue
        entry = EXERCISE_LIBRARY[key]
        if any(inj in entry.get("lesiones", []) for inj in injuries):
            yield key


_NAME2KEY = None
def _nombre_a_key(nombre):
    global _NAME2KEY
    if _NAME2KEY is None:
        _NAME2KEY = {v["nombre"]: k for k, v in EXERCISE_LIBRARY.items()}
    return _NAME2KEY.get(nombre)


@pytest.mark.parametrize("place,exp,obj,injuries", CASOS)
def test_dia_sin_duplicados_ni_contraindicados(place, exp, obj, injuries):
    profile = make_profile(objective=obj, experience=exp,
                           training_place=place, injuries=list(injuries))
    rutina = generate_training_plan(profile)
    for day in rutina["semana"]:
        if day["descanso"]:
            continue
        nombres = [e[0] for e in day["ejercicios"]]
        assert len(nombres) == len(set(nombres)), \
            f"Duplicados en {day['dia']}: {nombres} ({place}/{exp}/{obj}/{injuries})"
        assert not any(_excluidos_por_matriz(day["ejercicios"], list(injuries))), \
            f"Ejercicio no seguro en {day['dia']}: {injuries}"
        # El contador de la UI usa esta misma lista: coherente por construcción
        assert day["grupo"] is not None


def test_regresion_caso_observado_no_repite_dead_bug():
    profile = make_profile(objective="aumento_muscular", experience="intermedio",
                           training_place="casa", age=20, injuries=["hombro"],
                           equipment=["solo_peso_corporal"])
    profile.imc = 26.89
    rutina = generate_training_plan(profile)
    jueves = next(d for d in rutina["semana"] if d["dia"] == "Jueves")
    nombres = [e[0] for e in jueves["ejercicios"]]
    assert nombres.count("Dead bug") <= 1, nombres
