"""Pipeline evolutivo MDGA (Hito 2, sección 7.2, Figura 8):

    P0 → Eval → Select_torneo → Crossover_uniforme → Mutation_reasignación
       → Elitism_k → P_{t+1}

Reemplazo generacional con elitismo: P_{t+1} = Best_k(P_t) ∪ C_t, donde
|C_t| = N − k. Termina al alcanzar T_max o el criterio de calidad.
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
    """Parámetros de ejecución (Tabla 12)."""

    t_max: int = 200          # iteraciones máximas
    k: int = 5                # mejores individuos conservados (elitismo y persistencia)
    n: int = 60               # tamaño de población N
    tau: int = 3              # tamaño de torneo τ
    pc: float = 0.9           # probabilidad de cruce
    pm: float = 0.01          # probabilidad de mutación por evento
    seed: int | None = None
    target_f: float | None = None   # criterio de calidad: parar si F* <= target_f
    diversity_every: int = 1        # calcular D_t cada cuántas iteraciones (0 = nunca)

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
    elite_idx: np.ndarray          # índices de los k mejores en `pop`
    pop: np.ndarray
    F: np.ndarray
    H: np.ndarray


@dataclass
class GAResult:
    best: np.ndarray               # (k, E, 2) mejores k, ordenados
    best_F: np.ndarray
    best_H: np.ndarray
    history: list = field(default_factory=list)   # dicts por iteración
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
        """ΔF = (F0* − FT*) / F0*."""
        f0 = self.initial_best_f
        return (f0 - float(self.best_F[0])) / f0 if f0 else 0.0


def run_ga(problem: Problem, evaluator: Evaluator, params: GAParams,
           on_iteration: Callable[[IterationInfo], None] | None = None,
           should_stop: Callable[[], bool] | None = None,
           initial_population: np.ndarray | None = None) -> GAResult:
    """Ejecuta el MDGA y devuelve los k mejores horarios.

    `on_iteration` recibe la información de cada generación (incluida la
    t = 0) y permite persistir los mejores k sin acoplar el motor a la BD.
    `should_stop` permite cancelar la corrida desde fuera.
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

        # Criterios de terminación
        if params.target_f is not None and F[b] <= params.target_f:
            stopped_by = "calidad"
            break
        if t >= params.t_max:
            break
        if should_stop and should_stop():
            stopped_by = "cancelada"
            break

        # Selección → cruce → mutación → elitismo
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
