"""Función de aptitud multi-profundidad (Hito 2, sección 3.3).

    F(P) = Σ_i w_i · V_i(P)          (minimizar)
    H(P) = Σ_{i ∈ HC} V_i(P)          (factible si H = 0)
    S(P) = Σ_{j ∈ SC} w_j · V_j(P)

Las reglas se agrupan en tres niveles (superficial, medio, profundo); la
penalización total es la suma de las contribuciones de los tres niveles.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .problem import R_COL, T_COL, Problem
from .rules import CONDITIONS, parse_condition

LEVELS = ("superficial", "medio", "profundo")


@dataclass
class Rule:
    """Regla lógica tal como se almacena en la BD (Tabla 6)."""

    nombre: str
    tipo: str            # 'HC' | 'SC'
    condicion: str
    peso: float
    nivel: str = ""      # si se omite se toma el nivel natural de la condición
    activa: bool = True
    id: int | None = None

    def __post_init__(self):
        if self.tipo not in ("HC", "SC"):
            raise ValueError(f"regla '{self.nombre}': tipo debe ser HC o SC")
        if self.peso < 0:
            raise ValueError(f"regla '{self.nombre}': el peso no puede ser negativo")
        self.cond_name, self.params = parse_condition(self.condicion)
        if not self.nivel:
            self.nivel = CONDITIONS[self.cond_name]["nivel"]
        if self.nivel not in LEVELS:
            raise ValueError(f"regla '{self.nombre}': nivel inválido '{self.nivel}'")


@dataclass
class Evaluation:
    F: float
    H: float
    S: float
    violations: np.ndarray                    # V_i por regla activa
    by_level: dict = field(default_factory=dict)

    @property
    def feasible(self) -> bool:
        return self.H == 0


class Evaluator:
    """Evalúa horarios con las reglas activas. Es el motor de inferencia."""

    def __init__(self, problem: Problem, rules: list[Rule]):
        self.problem = problem
        self.rules = [r for r in rules if r.activa]
        if not self.rules:
            raise ValueError("no hay reglas activas para evaluar")
        self.weights = np.array([r.peso for r in self.rules], dtype=float)
        self.is_hard = np.array([r.tipo == "HC" for r in self.rules])
        self._fns = [CONDITIONS[r.cond_name]["fn"] for r in self.rules]
        self.n_evaluations = 0

    def violations(self, ind: np.ndarray) -> np.ndarray:
        t, r = ind[:, T_COL], ind[:, R_COL]
        p = self.problem
        return np.array([fn(p, t, r, rule.params, False)[0]
                         for fn, rule in zip(self._fns, self.rules)])

    def evaluate(self, ind: np.ndarray) -> Evaluation:
        self.n_evaluations += 1
        v = self.violations(ind)
        pen = self.weights * v
        by_level = {lvl: float(sum(pen[i] for i, r in enumerate(self.rules) if r.nivel == lvl))
                    for lvl in LEVELS}
        return Evaluation(
            F=float(pen.sum()),
            H=float(v[self.is_hard].sum()),
            S=float(pen[~self.is_hard].sum()),
            violations=v,
            by_level=by_level,
        )

    def evaluate_population(self, pop: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Devuelve (F, H) para cada individuo de la población."""
        F = np.empty(len(pop))
        H = np.empty(len(pop))
        for i, ind in enumerate(pop):
            self.n_evaluations += 1
            v = self.violations(ind)
            F[i] = float((self.weights * v).sum())
            H[i] = float(v[self.is_hard].sum())
        return F, H

    def detail(self, ind: np.ndarray) -> list[dict]:
        """Desglose por regla con los eventos involucrados (para explicación)."""
        t, r = ind[:, T_COL], ind[:, R_COL]
        out = []
        for fn, rule, w in zip(self._fns, self.rules, self.weights):
            v, events = fn(self.problem, t, r, rule.params, True)
            out.append({"regla": rule, "V": v, "w": float(w), "penalizacion": float(w * v),
                        "eventos": events or []})
        return out
