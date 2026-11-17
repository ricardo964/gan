"""Independent MDGA runs to evaluate the prototype (Milestone 2, section 11).

Executes Nc runs with different seeds on a synthetic instance (or an
ingestion XLSX) WITHOUT using the database, and reports the mean,
standard deviation and best value of the metrics in Tables 15 and 16:
feasibility rate R_f, G_f, Delta F, F*, H*, S*, final D_t, time, and also
how many of the k best are distinct schedules.

Usage:
    python scripts/experimento.py --corridas 10 --tmax 300
    python scripts/experimento.py --xlsx datos/ejemplo_utp.xlsx --pm 0.02
    python scripts/experimento.py --grupos 60 --estudiantes 800 --salones 15 --docentes 25
"""
import argparse
import json
import statistics as st
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from engine import Evaluator, Rule  # noqa: E402
from engine.ga import GAParams, run_ga  # noqa: E402
from engine.synthetic import SyntheticSpec, generate_tables, problem_from_tables  # noqa: E402

# Same base rules as db/init.sql
REGLAS = [
    Rule("disponibilidad_docente", "HC", "docente_no_disponible", 1000),
    Rule("capacidad_sala", "HC", "estudiantes_excede_capacidad", 1000),
    Rule("conflicto_docente", "HC", "docente_dos_eventos_misma_franja", 1000),
    Rule("conflicto_clase", "HC", "clase_dos_eventos_misma_franja", 1000),
    Rule("conflicto_sala", "HC", "sala_dos_eventos_misma_franja", 1000),
    Rule("preferencia_docente", "SC", "fuera_de_franja_preferida", 5),
    Rule("distribucion_carga", "SC", "carga_diaria_desbalanceada", 3),
    Rule("separacion_eventos", "SC", "eventos_clase_mismo_dia", 2),
    Rule("conflicto_estudiantes", "SC", "estudiante_dos_eventos_misma_franja", 10),
]


def resumen(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return {"media": None, "desv": None, "mejor": None, "n": 0}
    return {"media": st.fmean(xs), "desv": st.pstdev(xs) if len(xs) > 1 else 0.0,
            "min": min(xs), "max": max(xs), "n": len(xs)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xlsx", help="usar un archivo de ingesta en lugar de datos sintéticos")
    ap.add_argument("--corridas", type=int, default=10)
    ap.add_argument("--tmax", type=int, default=300)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--tau", type=int, default=3)
    ap.add_argument("--pc", type=float, default=0.9)
    ap.add_argument("--pm", type=float, default=0.01)
    ap.add_argument("--salones", type=int, default=12)
    ap.add_argument("--docentes", type=int, default=15)
    ap.add_argument("--materias", type=int, default=20)
    ap.add_argument("--grupos", type=int, default=30)
    ap.add_argument("--estudiantes", type=int, default=400)
    ap.add_argument("--semilla-datos", type=int, default=0)
    ap.add_argument("--salida", default="resultados")
    a = ap.parse_args()

    if a.xlsx:
        from ingest import read_files, validate

        tables, errs = read_files([(a.xlsx, Path(a.xlsx).read_bytes())])
        rep = validate(tables)
        if errs or not rep.ok:
            sys.exit("\n".join(errs + rep.errors))
        tables = rep.tables
        nombre = Path(a.xlsx).stem
    else:
        tables = generate_tables(SyntheticSpec(
            n_rooms=a.salones, n_teachers=a.docentes, n_subjects=a.materias,
            n_groups=a.grupos, n_students=a.estudiantes, seed=a.semilla_datos))
        nombre = f"sint_g{a.grupos}_e{a.estudiantes}_s{a.salones}"
    problem = problem_from_tables(tables)
    print(f"Instancia {nombre}: E={problem.n_events} eventos, R={problem.n_rooms} salas, "
          f"L={problem.n_teachers} docentes, C={problem.n_classes} clases, "
          f"St={problem.n_students} estudiantes")

    corridas = []
    for i in range(a.corridas):
        ev = Evaluator(problem, REGLAS)
        params = GAParams(t_max=a.tmax, k=a.k, n=a.n, tau=a.tau, pc=a.pc, pm=a.pm, seed=1000 + i)
        res = run_ga(problem, ev, params)
        best = ev.evaluate(res.best[0])
        distintos = len({r.tobytes() for r in res.best})
        corridas.append({
            "semilla": params.seed, "F": best.F, "H": best.H, "S": best.S,
            "factible": best.H == 0, "G_f": res.generations_to_feasible,
            "delta_F": res.relative_improvement, "D_final": res.history[-1]["diversity"],
            "tiempo_s": res.elapsed_s, "evaluaciones": res.evaluations,
            "k_distintos": distintos,
            "violaciones": dict(zip([r.nombre for r in ev.rules], best.violations.tolist())),
            "curva": [h["best_f"] for h in res.history],
        })
        c = corridas[-1]
        print(f"  corrida {i + 1:2d}: F={c['F']:9.2f} H={c['H']:3.0f} G_f={c['G_f']} "
              f"ΔF={c['delta_F']:.3f} D_T={c['D_final']:.3f} k_distintos={distintos}/{a.k} "
              f"t={c['tiempo_s']:.1f}s")

    nc = len(corridas)
    metricas = {
        "R_f": sum(c["factible"] for c in corridas) / nc,
        "F": resumen([c["F"] for c in corridas]),
        "H": resumen([c["H"] for c in corridas]),
        "S": resumen([c["S"] for c in corridas]),
        "G_f": resumen([c["G_f"] for c in corridas]),
        "delta_F": resumen([c["delta_F"] for c in corridas]),
        "D_final": resumen([c["D_final"] for c in corridas]),
        "tiempo_s": resumen([c["tiempo_s"] for c in corridas]),
        "k_distintos": resumen([c["k_distintos"] for c in corridas]),
        "violaciones_media": {r.nombre: st.fmean(c["violaciones"][r.nombre] for c in corridas)
                              for r in REGLAS},
    }
    print("\nResumen (media ± desv [min, max]):")
    print(f"  R_f = {metricas['R_f']:.2f}")
    for key in ("F", "H", "S", "G_f", "delta_F", "D_final", "tiempo_s", "k_distintos"):
        m = metricas[key]
        if m["n"]:
            print(f"  {key:12s} {m['media']:10.3f} ± {m['desv']:8.3f}  [{m['min']:.3f}, {m['max']:.3f}]"
                  + ("" if m["n"] == nc else f"  (n={m['n']})"))
    print("  Violaciones medias por regla:")
    for k, v in metricas["violaciones_media"].items():
        print(f"    {k:24s} {v:8.2f}")

    out = Path(a.salida)
    out.mkdir(exist_ok=True)
    f = out / f"exp_{nombre}_{time.strftime('%Y%m%d_%H%M%S')}.json"
    f.write_text(json.dumps({"instancia": nombre, "parametros": vars(a), "metricas": metricas,
                             "corridas": corridas}, indent=1, default=float))
    print(f"\nGuardado en {f}")


if __name__ == "__main__":
    np.seterr(all="ignore")
    main()
