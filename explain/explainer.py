"""Justificación de un horario: desglose de F(P) por regla.

Para cada regla activa reporta V_i(P), w_i, la penalización w_i·V_i y
los eventos involucrados con su docente, clase, franja y sala, de modo
que el usuario pueda ver POR QUÉ un horario obtuvo su aptitud.
"""
from __future__ import annotations

import numpy as np

from engine.fitness import Evaluator
from engine.problem import R_COL, T_COL
from engine.rules import CONDITIONS


def _label(seq, i, prefix):
    return seq[i] if i < len(seq) else f"{prefix}{i}"


def describe_event(evaluator: Evaluator, ind: np.ndarray, e: int) -> dict:
    p = evaluator.problem
    t, r = int(ind[e, T_COL]), int(ind[e, R_COL])
    c = int(p.event_class[e])
    return {
        "evento": e,
        "evento_id": _label(p.event_ids, e, "") if p.event_ids else e,
        "clase": _label(p.class_codes, c, "c"),
        "docente": _label(p.teacher_codes, int(p.event_teacher[e]), "l"),
        "franja": _label(p.slot_labels, t, "t"),
        "sala": _label(p.room_codes, r, "r"),
        "estudiantes": int(p.event_size[e]),
        "capacidad": int(p.room_capacity[r]),
    }


def explain(evaluator: Evaluator, ind: np.ndarray, max_events: int = 50) -> dict:
    """Explicación completa de un horario.

    `cobertura` es la proporción de violaciones que quedan asociadas a una
    regla y a eventos concretos (métrica de cobertura explicativa, 11.3).
    """
    ev = evaluator.evaluate(ind)
    reglas, total_v, covered_v = [], 0.0, 0.0
    for d in evaluator.detail(ind):
        rule = d["regla"]
        total_v += d["V"]
        if d["V"] and d["eventos"]:
            covered_v += d["V"]
        reglas.append({
            "id": rule.id,
            "nombre": rule.nombre,
            "tipo": rule.tipo,
            "nivel": rule.nivel,
            "condicion": rule.condicion,
            "descripcion": CONDITIONS[rule.cond_name]["descripcion"],
            "V": d["V"],
            "w": d["w"],
            "penalizacion": d["penalizacion"],
            "n_eventos": len(d["eventos"]),
            "eventos_idx": d["eventos"],
            "eventos": [describe_event(evaluator, ind, e) for e in d["eventos"][:max_events]],
        })
    reglas.sort(key=lambda x: (-x["penalizacion"], x["nombre"]))
    return {
        "F": ev.F, "H": ev.H, "S": ev.S,
        "factible": ev.feasible,
        "por_nivel": ev.by_level,
        "reglas": reglas,
        "cobertura": covered_v / total_v if total_v else 1.0,
    }


def compare(explanations: list[dict]) -> list[dict]:
    """Tabla regla × horario para comparar los k mejores."""
    names = [r["nombre"] for r in explanations[0]["reglas"]] if explanations else []
    rows = []
    for name in names:
        row = {"regla": name, "valores": []}
        for exp in explanations:
            r = next(x for x in exp["reglas"] if x["nombre"] == name)
            row["valores"].append({"V": r["V"], "penalizacion": r["penalizacion"]})
        rows.append(row)
    return rows
