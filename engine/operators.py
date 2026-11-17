"""Genetic operators of the evolutionary pipeline (Milestone 2, sections 7.3 to 7.6).

All of them operate on batches of individuals ((M, E, 2) arrays) to
avoid per-event Python loops.
"""
from __future__ import annotations

import numpy as np

from .problem import R_COL, T_COL


def tournament(F: np.ndarray, tau: int, n_select: int, rng: np.random.Generator) -> np.ndarray:
    """Tournament selection (7.3): X* = argmin_{X in T} F(X), |T| = tau.

    Returns the indices of the `n_select` winners. Fitness is not turned
    into probabilities; selective pressure is controlled with tau.
    """
    contenders = rng.integers(0, len(F), size=(n_select, tau))
    winners = np.argmin(F[contenders], axis=1)
    return contenders[np.arange(n_select), winners]


def uniform_event_crossover(p1: np.ndarray, p2: np.ndarray, pc: float,
                            rng: np.random.Generator) -> np.ndarray:
    """Uniform per-event crossover (7.4).

    For each event, a mask chooses which parent contributes its WHOLE
    (t, r) package, so the time slot of one parent is never combined with
    the room of the other. With probability 1 - pc the child is a copy of p1.
    """
    M, E, _ = p1.shape
    mask = rng.random((M, E)) < 0.5
    mask[rng.random(M) >= pc] = True          # no crossover: inherits everything from p1
    return np.where(mask[:, :, None], p1, p2)


def reassignment_mutation(pop: np.ndarray, pm: float, n_slots: int, n_rooms: int,
                          rng: np.random.Generator) -> np.ndarray:
    """Reassignment mutation (7.5), with probability pm per event.

    Randomly picks one of the three variants of equation (6): change both
    t and r, change only t, or change only r.
    The fixed fields l, c and S are not part of the chromosome.
    """
    out = pop.copy()
    M, E, _ = pop.shape
    mutate = rng.random((M, E)) < pm
    if not mutate.any():
        return out
    mode = rng.integers(0, 3, size=(M, E))    # 0: both, 1: only t, 2: only r
    change_t = mutate & (mode != 2)
    change_r = mutate & (mode != 1)
    out[:, :, T_COL] = np.where(change_t, rng.integers(0, n_slots, (M, E)), out[:, :, T_COL])
    out[:, :, R_COL] = np.where(change_r, rng.integers(0, n_rooms, (M, E)), out[:, :, R_COL])
    return out


def best_k(F: np.ndarray, k: int) -> np.ndarray:
    """Indices of the k best (lowest F), in order. Basis of elitism (7.6)."""
    return np.argsort(F, kind="stable")[:k]


def diversity(pop: np.ndarray, n_rooms: int) -> float:
    """Population diversity D_t (Table 16).

    D_t = 2 / (N(N-1)) * sum_{a<b} d(X_a, X_b), where d is the fraction of
    events with a different (t, r) package. Computed in O(N*E) by counting,
    per event, the pairs of individuals that share the same package.
    """
    N, E, _ = pop.shape
    if N < 2:
        return 0.0
    genes = pop[:, :, T_COL] * n_rooms + pop[:, :, R_COL]       # (N, E)
    total_pairs = N * (N - 1) / 2
    equal_pairs = 0.0
    for e in range(E):
        _, counts = np.unique(genes[:, e], return_counts=True)
        equal_pairs += float((counts * (counts - 1) / 2).sum())
    return 1.0 - equal_pairs / (E * total_pairs)
