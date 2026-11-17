"""Catalog of logical conditions (rule-based inference engine).

Each rule stored in the database (Table 6 of Milestone 2) has a
`condicion` field of the form::

    condition_name              or
    condition_name:param=value,param2=value

`condition_name` selects a function from this catalog; the parameters
let the rule be tuned from the interface without changing the algorithm
code (configurability, metric 11.3).

Every condition receives the problem and the t and r vectors of a
schedule and returns V_i(P) (number of violations) and, if `detail=True`,
the list of events involved (for the explanation subsystem).
"""
from __future__ import annotations

from typing import Callable

import numpy as np

from .problem import Problem

ConditionFn = Callable[[Problem, np.ndarray, np.ndarray, dict, bool], tuple[float, list[int] | None]]

CONDITIONS: dict[str, dict] = {}


def condition(name: str, nivel: str, descripcion: str, params: dict | None = None):
    """Register a condition with its natural depth level."""

    def deco(fn: ConditionFn) -> ConditionFn:
        CONDITIONS[name] = {"fn": fn, "nivel": nivel, "descripcion": descripcion,
                            "params": params or {}}
        return fn

    return deco


def parse_condition(text: str) -> tuple[str, dict]:
    """Parse 'name:a=1,b=2' into ('name', {'a': 1.0, 'b': 2.0})."""
    name, _, raw = text.strip().partition(":")
    params: dict = {}
    for part in filter(None, (p.strip() for p in raw.split(","))):
        key, sep, value = part.partition("=")
        if not sep:
            raise ValueError(f"parámetro mal formado en la condición: '{part}'")
        try:
            params[key.strip()] = float(value)
        except ValueError as exc:
            raise ValueError(f"el parámetro '{key}' debe ser numérico") from exc
    if name not in CONDITIONS:
        raise ValueError(f"condición desconocida: '{name}'. Disponibles: {sorted(CONDITIONS)}")
    unknown = set(params) - set(CONDITIONS[name]["params"])
    if unknown:
        raise ValueError(f"parámetros no soportados por '{name}': {sorted(unknown)}")
    return name, {**CONDITIONS[name]["params"], **params}


# Utilities
def _excess_by_key(keys: np.ndarray, size: int, detail: bool):
    """Sum of max(0, n_k - 1) over repeated keys, and the events with a repeated key."""
    counts = np.bincount(keys, minlength=size)
    v = float(np.maximum(counts - 1, 0).sum())
    events = np.flatnonzero(counts[keys] > 1).tolist() if detail and v else ([] if detail else None)
    return v, events


def _mask_result(mask: np.ndarray, detail: bool):
    v = float(mask.sum())
    return v, (np.flatnonzero(mask).tolist() if detail else None)


# Surface level
@condition("docente_no_disponible", "superficial",
           "El evento está en una franja en la que su docente no está disponible.")
def docente_no_disponible(p: Problem, t, r, params, detail):
    return _mask_result(~p.teacher_available[p.event_teacher, t], detail)


@condition("estudiantes_excede_capacidad", "superficial",
           "La cantidad de estudiantes del evento supera la capacidad de la sala.")
def estudiantes_excede_capacidad(p: Problem, t, r, params, detail):
    return _mask_result(p.event_size > p.room_capacity[r], detail)


@condition("fuera_de_franja_preferida", "superficial",
           "El evento está fuera de las franjas preferidas de su docente "
           "(solo docentes que declararon preferencias).")
def fuera_de_franja_preferida(p: Problem, t, r, params, detail):
    has = p.teacher_has_pref[p.event_teacher]
    return _mask_result(has & ~p.teacher_preferred[p.event_teacher, t], detail)


# Middle level
@condition("docente_dos_eventos_misma_franja", "medio",
           "Un docente tiene más de un evento en la misma franja.")
def docente_dos_eventos(p: Problem, t, r, params, detail):
    return _excess_by_key(p.event_teacher * p.n_slots + t, p.n_teachers * p.n_slots, detail)


@condition("clase_dos_eventos_misma_franja", "medio",
           "Una clase (grupo) tiene más de un evento en la misma franja.")
def clase_dos_eventos(p: Problem, t, r, params, detail):
    return _excess_by_key(p.event_class * p.n_slots + t, p.n_classes * p.n_slots, detail)


@condition("sala_dos_eventos_misma_franja", "medio",
           "Una sala tiene más de un evento en la misma franja.")
def sala_dos_eventos(p: Problem, t, r, params, detail):
    return _excess_by_key(r * p.n_slots + t, p.n_rooms * p.n_slots, detail)


@condition("carga_diaria_desbalanceada", "medio",
           "Suma, sobre los docentes, de la desviación estándar de sus horas "
           "diarias. Detalle: eventos de docentes con desviación >= umbral.",
           params={"umbral": 1.0})
def carga_diaria(p: Problem, t, r, params, detail):
    D = p.n_days
    day = p.slot_day[t]
    hours = np.bincount(p.event_teacher * D + day, minlength=p.n_teachers * D).reshape(-1, D)
    active = hours.sum(axis=1) > 0
    std = hours.std(axis=1)
    v = float(std[active].sum())
    if not detail:
        return v, None
    bad = std >= params["umbral"]
    return v, np.flatnonzero(bad[p.event_teacher]).tolist()


@condition("eventos_clase_mismo_dia", "medio",
           "Una clase tiene más de `max` horas el mismo día (mala separación "
           "entre eventos).", params={"max": 2.0})
def eventos_clase_mismo_dia(p: Problem, t, r, params, detail):
    D = p.n_days
    keys = p.event_class * D + p.slot_day[t]
    counts = np.bincount(keys, minlength=p.n_classes * D)
    limit = int(params["max"])
    v = float(np.maximum(counts - limit, 0).sum())
    if not detail:
        return v, None
    return v, np.flatnonzero(counts[keys] > limit).tolist()


# Deep level
@condition("estudiante_dos_eventos_misma_franja", "profundo",
           "Un estudiante tiene eventos de clases distintas en la misma franja.")
def estudiante_dos_eventos(p: Problem, t, r, params, detail):
    occ = np.zeros((p.n_classes, p.n_slots), dtype=np.int64)
    occ[p.event_class, t] = 1                      # class busy at t (0/1)
    per_student = p.class_students.T.astype(np.int64) @ occ   # (St, T)
    conflict = per_student > 1
    v = float(np.maximum(per_student - 1, 0).sum())
    if not detail:
        return v, None
    if not v:
        return v, []
    class_conflict = (p.class_students.astype(np.int64) @ conflict.astype(np.int64)) > 0
    return v, np.flatnonzero(class_conflict[p.event_class, t]).tolist()
