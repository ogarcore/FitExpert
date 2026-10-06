"""
benchmarks.py
=============
Mide tiempos de respuesta de las operaciones críticas del sistema.

Uso:
    python benchmarks.py            # ejecuta la batería completa
    python benchmarks.py --json     # imprime resultados en JSON

No modifica datos persistidos (usa rutas temporales para auth/database).
"""

import json
import os
import shutil
import statistics
import sys
import tempfile
import time
from pathlib import Path

BASE = Path(__file__).parent


def _time(fn, n=1):
    """Devuelve (ms_promedio, resultado_última_ejecución)."""
    times = []
    result = None
    for _ in range(n):
        t0 = time.perf_counter()
        result = fn()
        times.append((time.perf_counter() - t0) * 1000)
    return (statistics.median(times), result)


def run_benchmarks(verbose=True):
    results = {}

    tmp = Path(tempfile.mkdtemp(prefix="fitexpert_bench_"))
    try:
        # Aislar persistencia
        import auth as auth_mod
        import database as db_mod

        old_auth = auth_mod.AUTH_DB_PATH
        old_db = db_mod.DB_PATH
        auth_mod.AUTH_DB_PATH = tmp / "auth_db.json"
        db_mod.DB_PATH = tmp / "usuarios.json"

        try:
            from user_profile import UserProfile
            from inference_engine import InferenceEngine
            from nutrition import generate_nutrition_plan
            from training import generate_training_plan

            # 1. Registro
            def _register():
                import uuid
                return auth_mod.register(f"bench_{uuid.uuid4().hex[:8]}", "Passw0rd!123")

            ms, _ = _time(_register, 20)
            results["registro_ms"] = round(ms, 2)

            # 2. Login
            auth_mod.register("bench_login", "Passw0rd!123")
            ms, ok = _time(lambda: auth_mod.login("bench_login", "Passw0rd!123"), 20)
            results["login_ms"] = round(ms, 2)
            results["login_ok"] = bool(ok and ok.get("ok"))

            # 3. Login inválido
            ms, ok = _time(lambda: auth_mod.login("bench_login", "mala"), 10)
            results["login_invalido_ms"] = round(ms, 2)
            results["login_invalido_rechazado"] = not (ok and ok.get("ok"))

            # Perfiles de prueba (casos extremos representativos)
            perfiles = _build_profiles()

            # 4. Motor de inferencia
            def _engine():
                p = perfiles["adulto_base"].to_dict()
                prof = UserProfile(**{k: v for k, v in p.items() if k in UserProfile.__dataclass_fields__})
                return InferenceEngine().run(prof)

            ms, prof = _time(_engine, 20)
            results["motor_inferencia_ms"] = round(ms, 2)
            results["reglas_disparadas"] = len(getattr(prof, "fired_rules", []) or []) or len(prof.conclusions)

            # 5. Nutrición
            ms, plan = _time(lambda: generate_nutrition_plan(_engine()), 20)
            results["nutricion_ms"] = round(ms, 2)

            # 6. Entrenamiento
            ms, rutina = _time(lambda: generate_training_plan(_engine()), 20)
            results["entrenamiento_ms"] = round(ms, 2)

            # 7. Pipeline completo (evaluación completa)
            def _full():
                d = perfiles["adulto_base"].to_dict()
                prof = UserProfile(**{k: v for k, v in d.items() if k in UserProfile.__dataclass_fields__})
                InferenceEngine().run(prof)
                generate_nutrition_plan(prof)
                generate_training_plan(prof)
                return prof

            ms, _ = _time(_full, 20)
            results["pipeline_evaluacion_ms"] = round(ms, 2)

            # 8. Guardar + historial
            prof = _engine()
            for i in range(50):
                prof.user_id = "bench_user"
                db_mod.save_profile(prof)
            ms, hist = _time(lambda: db_mod.get_user_history("bench_user"), 20)
            results["historial_carga_ms"] = round(ms, 2)
            results["historial_registros"] = len(hist)

            # 9. PDF
            try:
                from pdf_exporter import export_pdf

                prof = _engine()
                out = str(tmp / "out.pdf")

                def _pdf():
                    p = generate_nutrition_plan(prof)
                    r = generate_training_plan(prof)
                    return export_pdf(prof, p, r, out)

                ms, _ = _time(_pdf, 3)
                results["pdf_ms"] = round(ms, 2)
                results["pdf_bytes"] = os.path.getsize(out) if os.path.exists(out) else 0
            except Exception as exc:  # pragma: no cover
                results["pdf_ms"] = None
                results["pdf_error"] = f"{type(exc).__name__}: {exc}"

            # 10. Casos extremos: motor + planes
            extreme = {}
            for name, prof in perfiles.items():
                if name == "adulto_base":
                    continue
                t0 = time.perf_counter()
                try:
                    InferenceEngine().run(prof)
                    generate_nutrition_plan(prof)
                    generate_training_plan(prof)
                    extreme[name] = round((time.perf_counter() - t0) * 1000, 2)
                except Exception as exc:
                    extreme[name] = f"ERROR {type(exc).__name__}: {exc}"
            results["casos_extremos_ms"] = extreme

        finally:
            auth_mod.AUTH_DB_PATH = old_auth
            db_mod.DB_PATH = old_db
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if verbose:
        print("\n=== BENCHMARKS FitExpert ===")
        for k, v in results.items():
            if isinstance(v, dict):
                print(f"{k}:")
                for k2, v2 in v.items():
                    print(f"    {k2}: {v2}")
            else:
                print(f"{k}: {v}")
        print("===========================\n")

    return results


def _build_profiles():
    """Construye perfiles que cubren los casos extremos obligatorios."""
    from user_profile import UserProfile

    def mk(**kw):
        campos = UserProfile.__dataclass_fields__
        return UserProfile(**{k: v for k, v in kw.items() if k in campos})

    base = dict(
        name="Benchmark", sex="masculino", weight=75.0, height=175.0,
        activity_level="moderado", objective="perdida_grasa",
        experience="principiante", training_place="gimnasio",
        diet_type="omnivoro", meal_frequency=3,
    )

    def variant(**over):
        data = {**base, **over}
        return mk(**data)

    return {
        "adulto_base": variant(age=25),
        "adolescente_sedentario": variant(age=15, weight=85, height=165,
                                          activity_level="sedentario",
                                          training_place="casa"),
        "bajo_peso": variant(age=25, weight=46, height=175,
                             objective="aumento_muscular"),
        "obesidad_lesion": variant(age=30, weight=135, height=170,
                                   injuries=["rodilla"], experience="principiante"),
        "adulto_mayor": variant(age=78, weight=70, height=168,
                                activity_level="sedentario",
                                experience="principiante", training_place="casa"),
        "vegano_alergias": variant(age=29, diet_type="vegano",
                                   allergies=["nueces", "soya"],
                                   intolerances=["lactosa"]),
        "datos_extremos": variant(age=100, weight=300, height=250),
    }


if __name__ == "__main__":
    as_json = "--json" in sys.argv
    res = run_benchmarks(verbose=not as_json)
    if as_json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
