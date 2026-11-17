"""Orchestration of a run (Figure 7 of Milestone 2, steps 3 to 13).

The controller loads data and active rules from MySQL, runs the MDGA
engine (evolutionary loop that saves the k best), passes the result to
the explanation subsystem and stores everything back in MySQL.

Runs execute in a thread so the HTTP request is not blocked. The state
lives in the database, so the interface and the API can read it no
matter which process serves the request. Cancellation is also signaled
through the database (state 'cancelando').
"""
from __future__ import annotations

import threading
import traceback

from flask import Flask

from engine import Evaluator
from engine.ga import GAParams, run_ga
from explain import explain

from ..models import repo

FLUSH_EVERY = 20          # iterations per bulk write
CHECK_CANCEL_EVERY = 10   # iterations between cancellation checks

_threads: dict[int, threading.Thread] = {}


def parse_params(form: dict) -> GAParams:
    """Convert and validate the parameters received from the web or the API (Table 12)."""
    try:
        seed = form.get("seed") if form.get("seed") not in (None, "") else form.get("semilla")
        p = GAParams(
            t_max=int(form.get("t_max", 200)),
            k=int(form.get("k", 5)),
            n=int(form.get("n", 60)),
            tau=int(form.get("tau", 3)),
            pc=float(form.get("pc", 0.9)),
            pm=float(form.get("pm", 0.01)),
            seed=int(seed) if seed not in (None, "") else None,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(f"parámetros con formato inválido: {exc}") from exc
    p.validate()
    return p


def start_run(app: Flask, params: GAParams) -> int:
    run_id = repo.create_run(params.to_dict())
    th = threading.Thread(target=_execute, args=(app, run_id, params), daemon=True,
                          name=f"mdga-run-{run_id}")
    _threads[run_id] = th
    th.start()
    return run_id


def cancel_run(run_id: int) -> bool:
    if repo.run_status(run_id) in ("pendiente", "ejecutando"):
        repo.update_run(run_id, estado="cancelando")
        return True
    return False


def mark_interrupted() -> None:
    """On startup, runs still 'ejecutando' from a previous process are orphaned."""
    repo.q("""UPDATE corridas SET estado = 'error',
              mensaje = 'interrumpida: el servidor se reinició durante la ejecución'
              WHERE estado IN ('pendiente', 'ejecutando', 'cancelando')""")
    repo.db.session.commit()


def _execute(app: Flask, run_id: int, params: GAParams) -> None:
    with app.app_context():
        try:
            repo.update_run(run_id, estado="ejecutando")
            problem = repo.load_problem()
            evaluator = Evaluator(problem, repo.load_rules())
            repo.update_run(run_id, n_eventos=problem.n_events)

            hist_buf: list[dict] = []
            elite_buf: list[dict] = []
            soft = ~evaluator.is_hard
            state = {"cancel": False}

            def on_iteration(info):
                hist_buf.append({"t": info.t, "best_f": info.best_f, "best_h": info.best_h,
                                 "mean_f": info.mean_f, "diversity": info.diversity})
                for rank, idx in enumerate(info.elite_idx, start=1):
                    v = evaluator.violations(info.pop[idx])
                    elite_buf.append({"t": info.t, "rango": rank, "f": float(info.F[idx]),
                                      "h": float(info.H[idx]),
                                      "s": float((evaluator.weights * v)[soft].sum())})
                if len(hist_buf) >= FLUSH_EVERY:
                    repo.save_iterations(run_id, hist_buf, elite_buf)
                    hist_buf.clear()
                    elite_buf.clear()

            def should_stop():
                state["n"] = state.get("n", 0) + 1
                if state["n"] % CHECK_CANCEL_EVERY == 0:
                    state["cancel"] = repo.run_status(run_id) == "cancelando"
                return state["cancel"]

            result = run_ga(problem, evaluator, params, on_iteration=on_iteration,
                            should_stop=should_stop)
            repo.save_iterations(run_id, hist_buf, elite_buf)

            explanations = [explain(evaluator, ind) for ind in result.best]
            repo.save_final(run_id, problem, result.generations, result.best, explanations)
            repo.update_run(
                run_id,
                estado="cancelada" if result.stopped_by == "cancelada" else "terminada",
                generaciones=result.generations,
                g_factible=result.generations_to_feasible,
                mejor_f=float(result.best_F[0]),
                mejor_h=float(result.best_H[0]),
                f_inicial=result.initial_best_f,
                evaluaciones=result.evaluations,
                detenida_por=result.stopped_by,
                tiempo_s=result.elapsed_s,
            )
        except Exception as exc:  # noqa: BLE001 - recorded in the run
            repo.db.session.rollback()
            repo.update_run(run_id, estado="error",
                            mensaje=f"{exc}\n\n{traceback.format_exc()}"[:60000])
        finally:
            repo.db.session.remove()
            _threads.pop(run_id, None)
