"""
test_ui_state.py
================
Estado inicial del acordeón de días (pestaña Entrenamiento):

  - Por defecto solo "Lunes" queda abierto.
  - Si el plan no contiene "Lunes", se abre el primer día (fallback).
  - La comparación tolera mayúsculas, tildes y espacios.
  - default=[] también cae en el fallback (primer día), documentado.
"""

from ui_state import (DIAS_ABIERTOS_POR_DEFECTO, dias_abiertos_iniciales,
                      nombre_de_dia)

SEMANA = [
    {"dia": "Lunes"}, {"dia": "Martes"}, {"dia": "Miércoles"},
    {"dia": "Jueves"}, {"dia": "Viernes"}, {"dia": "Sábado"},
    {"dia": "Domingo"},
]


def test_lunes_abierto_por_defecto():
    abiertos = dias_abiertos_iniciales(SEMANA)
    assert abiertos == {"lunes"}, f"Esperado solo lunes, obtuve {abiertos}"


def test_fallback_al_primer_dia_sin_lunes():
    semana = [{"dia": n} for n in ("Martes", "Miércoles", "Viernes")]
    abiertos = dias_abiertos_iniciales(semana)
    assert abiertos == {"martes"}


def test_comparacion_tolerante():
    semana = [{"dia": "  LUNES "}, {"dia": "martes"}]
    assert dias_abiertos_iniciales(semana) == {"lunes"}
    assert dias_abiertos_iniciales([{"dia": "Miércoles"}], default=["miércoles"]) == {"miercoles"}


def test_acepta_lista_de_strings_y_nombres_con_tildes():
    assert nombre_de_dia({"dia": "Miércoles"}) == "Miércoles"
    assert nombre_de_dia("Jueves") == "Jueves"
    assert dias_abiertos_iniciales(["Sábado", "Domingo"], default=["sábado"]) == {"sabado"}


def test_plan_vacio_no_falla():
    assert dias_abiertos_iniciales([]) == set()
    assert dias_abiertos_iniciales(None) == set()


def test_default_varios_dias():
    abiertos = dias_abiertos_iniciales(SEMANA, default=["Lunes", "Viernes"])
    assert abiertos == {"lunes", "viernes"}


def test_multiples_default_inexistente_fallback_primer_dia():
    abiertos = dias_abiertos_iniciales([{"dia": "Martes"}], default=["Lunes", "Domingo"])
    assert abiertos == {"martes"}


def test_default_vacia_deja_todo_cerrado():
    # Con default explícita y presente-en-el-plan vacía, no hay abiertos
    # solo si la lista de default es vacía Y hay días: por la regla de
    # fallback se abriría el primero. Documentamos el comportamiento real:
    abiertos = dias_abiertos_iniciales([{"dia": "Lunes"}, {"dia": "Martes"}], default=[])
    assert abiertos == {"lunes"}  # fallback: primer día


def test_conteo_ejercicios():
    from ui_state import conteo_ejercicios
    assert conteo_ejercicios({"descanso": False, "ejercicios": [("a", "3x10", "Pecho")]*5}) == 5
    assert conteo_ejercicios({"descanso": True, "ejercicios": []}) == 0
    assert conteo_ejercicios({"grupo": "Piernas"}) == 0
    assert conteo_ejercicios("no-dict") == 0


def test_es_descanso():
    from ui_state import es_descanso
    assert es_descanso({"descanso": True, "grupo": "Descanso Activo"})
    assert es_descanso({"grupo": "Cardio / Descanso activo", "ejercicios": []})
    assert es_descanso({"ejercicios": [], "grupo": ""})       # sin ejercicios → descanso
    assert not es_descanso({"descanso": False, "grupo": "Pecho", "ejercicios": [("a",)*3]})
    assert not es_descanso("nope")


def test_texto_secundario_dia():
    from ui_state import texto_secundario_dia
    assert texto_secundario_dia({"ejercicios": [("a","x","y")]}) == "1 ejercicio"
    assert texto_secundario_dia({"ejercicios": [("a","x","y")]*3}) == "3 ejercicios"
    assert texto_secundario_dia({"descanso": True, "grupo": "Descanso completo", "ejercicios": []}) == "Día de recuperación"
    assert texto_secundario_dia({"grupo": "Cardio / Descanso activo", "ejercicios": [("a","x","y")]*2}) == "2 ejercicios · Recuperación"
    assert texto_secundario_dia({"grupo": "Descanso Activo", "ejercicios": []}) == "Día de recuperación"
    assert texto_secundario_dia("no-dict") == "Día de recuperación"


def test_plan_key_reinicio_al_cambiar_de_plan():
    from ui_state import plan_key_de
    class P: created_at = "2026-10-07 10:00"
    r1 = {"nombre": "Split A", "semana": [{"dia": "Lunes"}, {"dia": "Martes"}]}
    assert plan_key_de(P(), r1) == plan_key_de(P(), r1)
    r2 = {"nombre": "Split A", "semana": [{"dia": "Lunes"}]}
    assert plan_key_de(P(), r1) != plan_key_de(P(), r2)
    class P2: created_at = "2026-10-07 10:01"
    assert plan_key_de(P(), r1) != plan_key_de(P2(), r1)
    assert plan_key_de(P(), None) is not None  # no falla con rutina vacía
