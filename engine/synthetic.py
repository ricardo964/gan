"""Generador de instancias sintéticas tipo UTP.

Sirve para probar el motor sin BD y para los experimentos. Las mismas
estructuras se exportan a XLSX (scripts/generar_datos.py) para probar
la ingesta.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .problem import Problem, utp_slots


@dataclass
class SyntheticSpec:
    n_rooms: int = 12
    n_teachers: int = 15
    n_subjects: int = 20
    n_groups: int = 30
    n_students: int = 400
    hours_min: int = 2
    hours_max: int = 4
    group_size: tuple[int, int] = (20, 40)
    courses_per_student: int = 5
    unavailable_frac: float = 0.15     # fracción de franjas no disponibles por docente
    pref_frac: float = 0.3             # fracción de docentes con preferencias
    seed: int = 0


def generate_tables(spec: SyntheticSpec) -> dict[str, list[dict]]:
    """Tablas con las mismas columnas que espera la ingesta CSV/XLSX."""
    rng = np.random.default_rng(spec.seed)
    slots = utp_slots()
    T = len(slots)
    lo, hi = spec.group_size

    salones = [{"codigo": f"S{i + 1:02d}",
                "capacidad": int(rng.choice([25, 30, 35, 40, 45, 60]))}
               for i in range(spec.n_rooms)]
    docentes = [{"codigo": f"D{i + 1:03d}", "nombre": f"Docente {i + 1}"}
                for i in range(spec.n_teachers)]
    materias = [{"codigo": f"M{i + 1:03d}", "nombre": f"Materia {i + 1}",
                 "horas_semanales": int(rng.integers(spec.hours_min, spec.hours_max + 1))}
                for i in range(spec.n_subjects)]

    disponibilidad = []
    for d in docentes:
        blocked = rng.random(T) < spec.unavailable_frac
        has_pref = rng.random() < spec.pref_frac
        # preferencia: mañanas (primeras 5 franjas del día) o tardes
        morning = rng.random() < 0.5
        for t in range(T):
            pos = t % 10
            pref = has_pref and ((pos < 5) == morning) and not blocked[t]
            if blocked[t] or pref:
                disponibilidad.append({"docente": d["codigo"], "franja": t + 1,
                                       "disponible": int(not blocked[t]), "preferida": int(pref)})

    grupos = []
    for g in range(spec.n_groups):
        m = materias[g % spec.n_subjects]
        grupos.append({"codigo": f"G{g + 1:03d}", "materia": m["codigo"],
                       "docente": docentes[int(rng.integers(spec.n_teachers))]["codigo"]})

    # Inscripciones: cada estudiante en `courses_per_student` grupos de materias
    # distintas, respetando un tamaño máximo por grupo.
    cap = {g["codigo"]: int(rng.integers(lo, hi + 1)) for g in grupos}
    count = {g["codigo"]: 0 for g in grupos}
    inscripciones = []
    for s in range(spec.n_students):
        code = f"E{s + 1:05d}"
        taken = set()
        for g in rng.permutation(len(grupos)):
            grp = grupos[g]
            if len(taken) >= spec.courses_per_student:
                break
            if grp["materia"] in taken or count[grp["codigo"]] >= cap[grp["codigo"]]:
                continue
            taken.add(grp["materia"])
            count[grp["codigo"]] += 1
            inscripciones.append({"grupo": grp["codigo"], "estudiante": code})

    return {"salones": salones, "docentes": docentes, "materias": materias,
            "disponibilidad": disponibilidad, "grupos": grupos,
            "inscripciones": inscripciones}


def problem_from_tables(tables: dict[str, list[dict]]) -> Problem:
    """Construye un Problem directamente desde las tablas (sin BD)."""
    slots = utp_slots()
    T = len(slots)
    rooms = tables["salones"]
    teachers = [d["codigo"] for d in tables["docentes"]]
    t_idx = {c: i for i, c in enumerate(teachers)}
    hours = {m["codigo"]: int(m["horas_semanales"]) for m in tables["materias"]}
    groups = tables["grupos"]
    g_idx = {g["codigo"]: i for i, g in enumerate(groups)}
    students = sorted({i["estudiante"] for i in tables["inscripciones"]})
    s_idx = {s: i for i, s in enumerate(students)}

    avail = np.ones((len(teachers), T), dtype=bool)
    pref = np.zeros((len(teachers), T), dtype=bool)
    for row in tables.get("disponibilidad", []):
        li, ti = t_idx[row["docente"]], int(row["franja"]) - 1
        avail[li, ti] = bool(int(row["disponible"]))
        pref[li, ti] = bool(int(row["preferida"]))

    cs = np.zeros((len(groups), max(len(students), 1)), dtype=bool)
    for row in tables["inscripciones"]:
        cs[g_idx[row["grupo"]], s_idx[row["estudiante"]]] = True

    ev_teacher, ev_class = [], []
    for gi, g in enumerate(groups):
        for _ in range(hours[g["materia"]]):
            ev_teacher.append(t_idx[g["docente"]])
            ev_class.append(gi)

    return Problem(
        n_slots=T, slot_day=slots,
        room_capacity=[r["capacidad"] for r in rooms],
        event_teacher=ev_teacher, event_class=ev_class, class_students=cs,
        teacher_available=avail, teacher_preferred=pref,
        slot_ids=list(range(1, T + 1)),
        room_codes=[r["codigo"] for r in rooms], teacher_codes=teachers,
        class_codes=[g["codigo"] for g in groups],
    )


def generate_problem(spec: SyntheticSpec | None = None) -> Problem:
    return problem_from_tables(generate_tables(spec or SyntheticSpec()))
