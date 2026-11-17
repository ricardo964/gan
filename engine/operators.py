"""Operadores genéticos del pipeline evolutivo (Hito 2, secciones 7.3 a 7.6).

Todos operan sobre lotes de individuos (arreglos (M, E, 2)) para evitar
bucles de Python por evento.
"""
from __future__ import annotations

import numpy as np

from .problem import R_COL, T_COL


def tournament(F: np.ndarray, tau: int, n_select: int, rng: np.random.Generator) -> np.ndarray:
    """Selección por torneo (7.3): X* = argmin_{X∈T} F(X), |T| = τ.

    Devuelve los índices de los `n_select` ganadores. No transforma la
    aptitud en probabilidades; la presión selectiva se controla con τ.
    """
    contenders = rng.integers(0, len(F), size=(n_select, tau))
    winners = np.argmin(F[contenders], axis=1)
    return contenders[np.arange(n_select), winners]


def uniform_event_crossover(p1: np.ndarray, p2: np.ndarray, pc: float,
                            rng: np.random.Generator) -> np.ndarray:
    """Cruce uniforme por evento (7.4).

    Para cada evento, una máscara elige qué progenitor aporta su paquete
    (t, r) COMPLETO, de modo que nunca se combina la franja de un padre
    con la sala del otro. Con probabilidad 1 - pc el hijo es copia de p1.
    """
    M, E, _ = p1.shape
    mask = rng.random((M, E)) < 0.5
    mask[rng.random(M) >= pc] = True          # sin cruce: hereda todo de p1
    return np.where(mask[:, :, None], p1, p2)


def reassignment_mutation(pop: np.ndarray, pm: float, n_slots: int, n_rooms: int,
                          rng: np.random.Generator) -> np.ndarray:
    """Mutación por reasignación (7.5), con probabilidad pm por evento.

    Elige al azar entre las tres variantes de la ecuación (6):
    (t, r) -> (t', r'),  (t, r) -> (t', r),  (t, r) -> (t, r').
    Los campos fijos l, c y S no forman parte del cromosoma.
    """
    out = pop.copy()
    M, E, _ = pop.shape
    mutate = rng.random((M, E)) < pm
    if not mutate.any():
        return out
    mode = rng.integers(0, 3, size=(M, E))    # 0: ambos, 1: solo t, 2: solo r
    change_t = mutate & (mode != 2)
    change_r = mutate & (mode != 1)
    out[:, :, T_COL] = np.where(change_t, rng.integers(0, n_slots, (M, E)), out[:, :, T_COL])
    out[:, :, R_COL] = np.where(change_r, rng.integers(0, n_rooms, (M, E)), out[:, :, R_COL])
    return out


def best_k(F: np.ndarray, k: int) -> np.ndarray:
    """Índices de los k mejores (menor F), en orden. Base del elitismo (7.6)."""
    return np.argsort(F, kind="stable")[:k]


def diversity(pop: np.ndarray, n_rooms: int) -> float:
    """Diversidad poblacional D_t (Tabla 16).

    D_t = 2 / (N(N-1)) · Σ_{a<b} d(X_a, X_b), con d la fracción de eventos
    con distinto paquete (t, r). Se calcula en O(N·E) contando, por evento,
    los pares de individuos que comparten el mismo paquete.
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
