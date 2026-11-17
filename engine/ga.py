"""MDGA evolutionary pipeline (Milestone 2, section 7.2, Figure 8).

Starting from P0, each generation applies evaluation, tournament
selection, uniform crossover, reassignment mutation and k-elitism to
produce P_{t+1}.

Generational replacement with elitism: P_{t+1} = Best_k(P_t) union C_t,
where |C_t| = N - k. Stops when T_max or the quality criterion is reached.
"""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Callable

import numpy as np

from .fitness import Evaluator
from .operators import best_k, diversity, reassignment_mutation, tournament, uniform_event_crossover
from .problem import Problem


@dataclass
class GAParams:
    """Run parameters (Table 12)."""

    t_max: int = 200          # maximum iterations
    k: int = 5                # best individuals kept (elitism and persistence)
    n: int = 60               # population size N
    tau: int = 3              # tournament size tau
    pc: float = 0.9           # crossover probability
    pm: float = 0.01          # mutation probability per event
    seed: int | None = None
    target_f: float | None = None   # quality criterion: stop if F* <= target_f
    diversity_every: int = 1        # compute D_t every this many iterations (0 = never)

    def validate(self) -> None:
        errors = []
        for name in ("t_max", "k", "n", "tau"):
            if int(getattr(self, name)) <= 0:
                errors.append(f"{name} debe ser un entero positivo")
        if self.k >= self.n:
            errors.append("k debe ser menor que N")
        if self.tau > self.n:
            errors.append("τ no puede ser mayor que N")
        for name in ("pc", "pm"):
            if not 0.0 <= float(getattr(self, name)) <= 1.0:
                errors.append(f"{name} debe estar en [0, 1]")
        if errors:
            raise ValueError("; ".join(errors))

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class IterationInfo:
    t: int
    best_f: float
    best_h: float
    mean_f: float
    diversity: float | None
    elite_idx: np.ndarray          # indices of the k best in `pop`
    pop: np.ndarray
    F: np.ndarray
    H: np.ndarray


@dataclass
class GAResult:
    best: np.ndarray               # (k, E, 2) k best, sorted
    best_F: np.ndarray
    best_H: np.ndarray
    history: list = field(default_factory=list)   # dicts per iteration
    generations: int = 0
    generations_to_feasible: int | None = None    # G_f
    elapsed_s: float = 0.0
    stopped_by: str = "t_max"
    evaluations: int = 0

    @property
    def initial_best_f(self) -> float:
        return self.history[0]["best_f"] if self.history else float("nan")

    @property
    def relative_improvement(self) -> float:
        """Delta F = (F0* - FT*) / F0*."""
        f0 = self.initial_best_f
        return (f0 - float(self.best_F[0])) / f0 if f0 else 0.0


def run_ga(problem: Problem, evaluator: Evaluator, params: GAParams,
           on_iteration: Callable[[IterationInfo], None] | None = None,
           should_stop: Callable[[], bool] | None = None,
           initial_population: np.ndarray | None = None) -> GAResult:
    """Run the MDGA and return the k best schedules.

    `on_iteration` receives the information of each generation (including
    t = 0) and allows persisting the k best without coupling the engine
    to the database. `should_stop` allows cancelling the run externally.
    """
    params.validate()
    rng = np.random.default_rng(params.seed)
    N, k = params.n, params.k
    start = time.perf_counter()
    evals0 = evaluator.n_evaluations

    pop = (initial_population.copy() if initial_population is not None
           else problem.random_population(N, rng))
    F, H = evaluator.evaluate_population(pop)

    history: list[dict] = []
    g_feasible: int | None = None
    stopped_by = "t_max"
    t = 0
    while True:
        elite = best_k(F, k)
        b = elite[0]
        div = (diversity(pop, problem.n_rooms)
               if params.diversity_every and t % params.diversity_every == 0 else None)
        if g_feasible is None and H[b] == 0:
            g_feasible = t
        history.append({"t": t, "best_f": float(F[b]), "best_h": float(H[b]),
                        "mean_f": float(F.mean()), "diversity": div})
        if on_iteration:
            on_iteration(IterationInfo(t, float(F[b]), float(H[b]), float(F.mean()), div,
                                       elite, pop, F, H))

        # Termination criteria
        if params.target_f is not None and F[b] <= params.target_f:
            stopped_by = "calidad"
            break
        if t >= params.t_max:
            break
        if should_stop and should_stop():
            stopped_by = "cancelada"
            break

        # Selection, crossover, mutation and elitism
        n_children = N - k
        parents = tournament(F, params.tau, 2 * n_children, rng)
        p1, p2 = pop[parents[:n_children]], pop[parents[n_children:]]
        children = uniform_event_crossover(p1, p2, params.pc, rng)
        children = reassignment_mutation(children, params.pm, problem.n_slots,
                                         problem.n_rooms, rng)
        cF, cH = evaluator.evaluate_population(children)

        pop = np.concatenate([pop[elite], children])
        F = np.concatenate([F[elite], cF])
        H = np.concatenate([H[elite], cH])
        t += 1

    elite = best_k(F, k)
    return GAResult(
        best=pop[elite].copy(), best_F=F[elite].copy(), best_H=H[elite].copy(),
        history=history, generations=t, generations_to_feasible=g_feasible,
        elapsed_s=time.perf_counter() - start, stopped_by=stopped_by,
        evaluations=evaluator.n_evaluations - evals0,
    )
