import numpy as np
import pytest

from engine import Evaluator, Rule
from engine.ga import GAParams, run_ga
from engine.operators import (best_k, diversity, reassignment_mutation, tournament,
                              uniform_event_crossover)
from engine.synthetic import SyntheticSpec, generate_problem


def test_torneo_elige_el_menor_F():
    rng = np.random.default_rng(0)
    F = np.array([5.0, 1.0, 3.0, 0.5])
    # con τ = N el ganador siempre es el mejor... si aparece entre los aspirantes
    winners = tournament(F, tau=50, n_select=20, rng=rng)
    assert (winners == 3).all()


def test_cruce_conserva_paquetes_completos():
    rng = np.random.default_rng(1)
    p1 = np.stack([np.arange(100), np.arange(100) + 1000], axis=1)[None].repeat(10, 0)
    p2 = np.stack([np.arange(100) + 500, np.arange(100) + 2000], axis=1)[None].repeat(10, 0)
    child = uniform_event_crossover(p1, p2, pc=1.0, rng=rng)
    from_p1 = child[:, :, 0] < 500
    # si t vino de p1, r también (nunca se mezclan t de un padre y r del otro)
    assert (from_p1 == (child[:, :, 1] < 2000)).all()
    assert from_p1.any() and (~from_p1).any()


def test_sin_cruce_el_hijo_es_copia_de_p1():
    rng = np.random.default_rng(2)
    p1 = np.zeros((5, 20, 2), dtype=np.int64)
    p2 = np.ones((5, 20, 2), dtype=np.int64)
    assert (uniform_event_crossover(p1, p2, pc=0.0, rng=rng) == p1).all()


def test_mutacion_respeta_dominios_y_tasa():
    rng = np.random.default_rng(3)
    pop = np.zeros((50, 200, 2), dtype=np.int64)
    out = reassignment_mutation(pop, pm=0.1, n_slots=60, n_rooms=7, rng=rng)
    assert out[:, :, 0].max() < 60 and out[:, :, 1].max() < 7
    changed = (out != pop).any(axis=2).mean()
    assert 0.05 < changed < 0.12          # ≈ pm (algunas reasignaciones caen igual)
    assert (pop == 0).all()               # no modifica la entrada
    assert (reassignment_mutation(pop, 0.0, 60, 7, rng) == pop).all()


def test_diversidad():
    pop = np.zeros((4, 10, 2), dtype=np.int64)
    assert diversity(pop, 5) == 0
    pop[:, :, 0] = np.arange(4)[:, None]
    assert diversity(pop, 5) == 1


def test_best_k():
    assert list(best_k(np.array([3.0, 1.0, 2.0, 0.0]), 2)) == [3, 1]


@pytest.mark.parametrize("bad", [dict(k=10, n=10), dict(pm=1.5), dict(tau=0), dict(t_max=0)])
def test_parametros_invalidos(bad):
    with pytest.raises(ValueError):
        GAParams(**bad).validate()


RULES = [
    Rule("disp", "HC", "docente_no_disponible", 1000),
    Rule("cap", "HC", "estudiantes_excede_capacidad", 1000),
    Rule("doc", "HC", "docente_dos_eventos_misma_franja", 1000),
    Rule("cla", "HC", "clase_dos_eventos_misma_franja", 1000),
    Rule("sal", "HC", "sala_dos_eventos_misma_franja", 1000),
    Rule("est", "SC", "estudiante_dos_eventos_misma_franja", 10),
]


def test_ga_alcanza_factibilidad_y_elitismo_monotono():
    spec = SyntheticSpec(n_rooms=6, n_teachers=6, n_subjects=6, n_groups=8,
                         n_students=80, courses_per_student=3, seed=7)
    problem = generate_problem(spec)
    ev = Evaluator(problem, RULES)
    seen = []
    res = run_ga(problem, ev, GAParams(t_max=150, k=3, n=40, tau=3, pc=0.9, pm=0.02, seed=1),
                 on_iteration=lambda info: seen.append(info.t))
    best = [h["best_f"] for h in res.history]
    assert all(b2 <= b1 for b1, b2 in zip(best, best[1:]))     # elitismo
    assert seen == list(range(res.generations + 1))
    assert res.best_H[0] == 0 and res.generations_to_feasible is not None
    assert res.relative_improvement > 0.9
    assert res.best.shape == (3, problem.n_events, 2)
    assert list(res.best_F) == sorted(res.best_F)


def test_ga_reproducible_y_criterio_de_calidad():
    problem = generate_problem(SyntheticSpec(n_groups=6, n_students=50, seed=3))
    params = GAParams(t_max=40, k=2, n=20, seed=11)
    a = run_ga(problem, Evaluator(problem, RULES), params)
    b = run_ga(problem, Evaluator(problem, RULES), params)
    assert np.array_equal(a.best, b.best)
    c = run_ga(problem, Evaluator(problem, RULES),
               GAParams(t_max=500, k=2, n=20, seed=11, target_f=1e12))
    assert c.stopped_by == "calidad" and c.generations == 0


def test_ga_cancelable():
    problem = generate_problem(SyntheticSpec(n_groups=6, n_students=50, seed=3))
    res = run_ga(problem, Evaluator(problem, RULES), GAParams(t_max=1000, k=2, n=20, seed=1),
                 should_stop=lambda: True)
    assert res.stopped_by == "cancelada" and res.generations == 0
