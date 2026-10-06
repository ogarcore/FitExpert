"""
test_engine.py
==============
Base de conocimiento (knowledge_base.py) y motor de inferencia
(inference_engine.py):

  - Integridad: 69 reglas, ids únicos, jerarquía documentada, metadatos
    completos, referencias citadas reales, conflicts siempre resolubles.
  - Encadenamiento y contratos (conclusions/explanations/facts/summary).
  - Determinismo y resolución de conflictos por jerarquía.
  - Suprimidos registrados (nunca silenciosos) y errores auditable.
  - Casos de seguridad: señales de alarma, menores, bajo peso, alergias.
"""

import fnmatch
import re

from inference_engine import InferenceEngine
from knowledge_base import RULES, TIER_LABELS, TIER_ORDER, tier_rank

from conftest import conclusion_ids, make_profile, run_profile

ID_PATTERN = re.compile(r"^[A-Z]+(?:-[A-Z0-9]+)+$")
SEVERITIES = {"critica", "alta", "media", "baja", "info"}
REAL_SOURCES = ("OMS", "WHO", "AAP", "ACSM", "AHA", "CDC", "PROT-AGE", "WGO",
                "NIH", "AASM", "NIDDK", "ADA", "JAMDA", "ACR", "Harvard",
                "ISSN", "USDA", "CSEP", "Diabetes", "American College",
                "Colegio Americano", "Consenso", "Rheumatology", "EFSA",
                "PTJ", "Medicine & Science", "Sports Medicine")


# ── Integridad de la base de conocimiento ──────────────────────────────

def test_rule_count_is_69():
    assert len(RULES) == 69


def test_rule_ids_unique_and_parseable():
    ids = [r.id for r in RULES]
    assert len(set(ids)) == len(ids)
    for rid in ids:
        assert ID_PATTERN.match(rid), f"id raro: {rid}"


def test_every_rule_has_full_metadata():
    for r in RULES:
        assert r.id, r
        assert len(r.description) > 5
        assert len(r.conclusion) > 20
        assert len(r.explanation) > 40
        assert r.category, r.id
        assert callable(r.condition)
        assert r.tier in TIER_ORDER, (r.id, r.tier)
        assert 0 <= r.priority <= 100
        assert r.severity in SEVERITIES, (r.id, r.severity)


def test_references_only_real_sources():
    for r in RULES:
        assert isinstance(r.references, (tuple, list)) and r.references, (
            f"{r.id} debe citar al menos una fuente real")
        for ref in r.references:
            assert isinstance(ref, str) and len(ref.strip()) >= 8
            lower = ref.lower()
            assert "todo" not in lower and "pendiente" not in lower, ref
    # El corpus completo debe citar las guías clave reales
    all_refs = " ".join(ref for r in RULES for ref in r.references)
    for keyword in ("OMS", "ACSM"):
        assert keyword in all_refs, keyword
    assert any(k in all_refs for k in ("AAP", "WHO", "CDC", "AHA"))


def test_tier_hierarchy_complete():
    assert set(TIER_ORDER) == {"SEGURIDAD", "CONTRAINDICACIONES", "EDAD",
                               "CONDICION_FISICA", "OBJETIVO", "PREFERENCIAS",
                               "SEGUIMIENTO"}
    assert [TIER_ORDER[k] for k in TIER_ORDER] == [0, 1, 2, 3, 4, 5, 6]
    assert set(TIER_LABELS) == set(TIER_ORDER)
    assert tier_rank("SEGURIDAD") < tier_rank("CONTRAINDICACIONES") \
           < tier_rank("EDAD") < tier_rank("CONDICION_FISICA") \
           < tier_rank("OBJETIVO") < tier_rank("PREFERENCIAS")


def test_conflicts_patterns_resolvable_against_kb():
    for r in RULES:
        for pattern in r.conflicts:
            # el patrón debe apuntar a OTRA regla de la base (no a sí misma)
            assert not fnmatch.fnmatchcase(r.id, pattern), (r.id, pattern)
            match = [o.id for o in RULES if o.id != r.id
                     and fnmatch.fnmatchcase(o.id, pattern)]
            assert match, (f"{r.id} declara conflict '{pattern}' que no "
                           f"coincide con ninguna regla")


def test_no_rule_self_conflicts_empty_resolution():
    # una regla nunca debe listar su propio id en conflicts
    for r in RULES:
        assert r.id not in r.conflicts


# ── Motor sobre perfil sano ────────────────────────────────────────────

def test_engine_contracts_healthy_profile():
    p = make_profile()
    engine = run_profile(p)
    assert isinstance(p.conclusions, list) and p.conclusions
    assert isinstance(p.explanations, list)
    assert len(p.explanations) == len(p.conclusions)
    # Contrato consumido por las interfaces
    for c in p.conclusions:
        assert {"id", "description", "conclusion", "category", "severity",
                "tier", "tier_label", "priority", "references"} <= set(c)
    for e in p.explanations:
        assert {"id", "explanation", "test", "trigger"} <= set(e)
    # hechos OAV
    assert isinstance(p.facts, dict)
    assert "Usuario" in p.facts and "Evaluación" in p.facts
    assert p.facts["Usuario"]["Edad"] == 30
    # summary() (API expuesta por las UI en lugar de `stats`)
    s = engine.summary()
    for key in ("total_rules", "fired", "skipped", "suppressed", "errors",
                "fired_ids", "suppressed_detail", "errors_detail"):
        assert key in s
    assert s["total_rules"] == 69
    assert s["fired"] + s["skipped"] == 69
    assert s["errors"] == 0
    assert p.engine_errors == []


def test_engine_deterministic():
    p1 = make_profile()
    run_profile(p1)
    ids1 = conclusion_ids(p1)
    p2 = make_profile()
    run_profile(p2)
    ids2 = conclusion_ids(p2)
    assert ids1 == ids2


def test_engine_orders_by_hierarchy():
    p = make_profile(red_flags=["mareo_desmayo"], injuries=["rodilla"])
    run_profile(p)
    assert p.conclusions[0]["id"].startswith("SEG-"), p.conclusions[0]["id"]
    assert p.conclusions[0]["severity"] == "critica"


def test_empty_profile_no_crash_and_auditable():
    from user_profile import UserProfile
    p = UserProfile()  # perfil sin datos: caso adverso
    engine = run_profile(p)
    assert isinstance(p.conclusions, list)
    for c in p.conclusions:
        assert c["id"] and isinstance(c["conclusion"], str)
    # Si algo falla debe quedar registrado en engine_errors, jamás silencio
    assert all(isinstance(e, dict) for e in p.engine_errors)
    assert isinstance(engine.summary(), dict)


def test_supressed_rules_recorded():
    p = make_profile(age=15, training_place="casa",
                     experience="principiante", objective="incrementar masa")
    engine = run_profile(p)
    ids = conclusion_ids(p)
    assert "EDAD-02" in ids, "menor de 16 debe activar EDAD-02"
    # EDAD-02 declara conflict TRAIN-*: si se activó una TRAIN, debió suprimirse
    fired_trains = [i for i in engine.fired_rules if i.startswith("TRAIN-")]
    suppressed_ids = {s["id"] for s in p.suppressed}
    for tid in fired_trains:
        assert tid in suppressed_ids, f"{tid} debió registrarse en suppressed"
    assert not any(i.startswith("TRAIN-") for i in ids), \
        "no puede quedar una recomendación TRAIN-* como conclusión final"
    for s in p.suppressed:
        assert s["id"] != s["suppressed_by"]
        assert s.get("reason")
        assert "SEGURIDAD" in s["reason"] or "prioridad" in s["reason"]


# ── Seguridad y jerarquía ──────────────────────────────────────────────

def test_red_flags_derivation_and_suppression():
    p = make_profile(red_flags=["dolor_toracico"], activity_level="activo")
    engine = run_profile(p)
    assert "SEG-RF-01" in conclusion_ids(p)
    fired_trains = [i for i in engine.fired_rules if i.startswith("TRAIN-")]
    supressed_ids = {s["id"] for s in p.suppressed}
    for tid in fired_trains:
        assert tid in supressed_ids or tid not in conclusion_ids(p)


def test_low_weight_suppresses_deficit():
    # IMC ~17.3 en adulto → NUT-07 (CONDICION_FISICA) suprime NUT-01/NUT-03
    p = make_profile(age=30, weight=50.0, height=170.0,
                     objective="perdida_grasa")
    run_profile(p)
    ids = conclusion_ids(p)
    assert "NUT-07" in ids, "bajo peso debe activar NUT-07"
    assert "NUT-01" not in ids, "el déficit calórico de NUT-01 debe suprimirse"
    suppressed = {s["id"]: s["suppressed_by"] for s in p.suppressed}
    assert suppressed.get("NUT-01") == "NUT-07", suppressed


def test_severity_propagation_to_conclusions():
    p = make_profile(red_flags=["dolor_agudo_articular"])
    run_profile(p)
    assert conclusion_ids(p)[0] == "SEG-RF-04"
    assert p.conclusions[0]["severity"] == "critica"
    assert p.conclusions[0]["action"] == "derivar"
    assert p.explanations[0]["trigger"].startswith("Se activó porque")


def test_injury_specific_rule_fires():
    p = make_profile(injuries=["rodilla"], injury_severity="moderada")
    run_profile(p)
    assert "LES-02" in conclusion_ids(p)          # regla de rodilla
    assert "LES-SEV-02" in conclusion_ids(p)      # severidad moderada con lesiones


def test_allergen_safety_rules():
    p = make_profile(allergies=["gluten", "soja"], diet_type="vegano")
    run_profile(p)
    ids = conclusion_ids(p)
    assert any(i.startswith("ALLE") for i in ids) or \
           any(i in ("SEG-ALG-01", "SEG-ALG-02") for i in ids)
    sev = {c["severity"] for c in p.conclusions if c["id"] in ("SEG-ALG-01", "SEG-ALG-02")}
    assert sev <= {"alta"}, sev


def test_seguimiento_rules_run_last():
    p = make_profile()
    run_profile(p)
    ids = conclusion_ids(p)
    rank_last = [TIER_ORDER["EDAD"], TIER_ORDER["OBJETIVO"],
                 TIER_ORDER["PREFERENCIAS"], TIER_ORDER["SEGUIMIENTO"]]
    last_tier = p.conclusions[-1]["tier"]
    assert TIER_ORDER[last_tier] == max(
        TIER_ORDER[c["tier"]] for c in p.conclusions), last_tier


def test_engine_re_run_replaces_previous_results():
    p = make_profile()
    run_profile(p)
    p2 = make_profile(red_flags=["mareo_desmayo"])
    run_profile(p2)
    assert p2.conclusions == [] or p2.conclusions[0]["id"] == "SEG-RF-02"
    # La alarma de seguridad no puede quedar enterrada por recomendaciones de objetivo
    for c in p2.conclusions:
        assert not c["id"].startswith("TRAIN-")
    sev = [c for c in p2.conclusions if c["id"] == "SEG-RF-02"]
    assert sev and sev[0]["severity"] == "critica"