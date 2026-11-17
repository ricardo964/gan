"""Modelo (MVC): acceso a MySQL, la base de hechos y de conocimiento.

Traduce entre las tablas del esquema (db/init.sql) y las estructuras
del motor (`engine.Problem`, `engine.Rule`). Es la conexión funcional
entre el motor de inferencia y la base de hechos que pide el Hito 3.
"""
from __future__ import annotations

import json

import numpy as np
from sqlalchemy import text  # noqa: F401  (reexportado para controladores)

from engine import Problem, Rule

from .. import db

DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"]


def q(sql: str, **params):
    return db.session.execute(text(sql), params)


def rows(sql: str, **params) -> list[dict]:
    return [dict(r._mapping) for r in q(sql, **params)]


def one(sql: str, **params) -> dict | None:
    r = q(sql, **params).first()
    return dict(r._mapping) if r else None


def slot_label(row: dict) -> str:
    return f"{DIAS[row['dia'] - 1]} {str(row['hora_inicio'])[:-3].zfill(5)}"


# ------------------------------------------------------------ datos base
def counts() -> dict:
    tables = ["salones", "docentes", "materias", "grupos", "estudiantes", "eventos",
              "reglas", "corridas"]
    return {t: q(f"SELECT COUNT(*) FROM {t}").scalar() for t in tables}


def franjas() -> list[dict]:
    out = rows("SELECT id, dia, hora_inicio, hora_fin FROM franjas ORDER BY id")
    for r in out:
        r["etiqueta"] = slot_label(r)
    return out


def sync_eventos() -> int:
    """Asegura un evento por hora semanal de cada grupo (e = (l, c, S)).

    Inserta los que faltan y elimina los sobrantes (p. ej. si bajaron las
    horas de una materia). Devuelve el total de eventos.
    """
    q("""
        DELETE e FROM eventos e
        JOIN grupos g ON g.id = e.grupo_id
        JOIN materias m ON m.id = g.materia_id
        WHERE e.indice > m.horas_semanales
    """)
    q("""
        INSERT INTO eventos (grupo_id, indice)
        WITH RECURSIVE seq(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM seq WHERE n < 60)
        SELECT g.id, s.n
        FROM grupos g JOIN materias m ON m.id = g.materia_id
        JOIN seq s ON s.n <= m.horas_semanales
        LEFT JOIN eventos e ON e.grupo_id = g.id AND e.indice = s.n
        WHERE e.id IS NULL
    """)
    return q("SELECT COUNT(*) FROM eventos").scalar()


def replace_academic_data(t: dict[str, list[dict]]) -> dict:
    """Reemplaza todos los datos académicos por los de la ingesta.

    Las corridas anteriores se eliminan porque sus horarios referencian
    eventos que dejan de existir. Se ejecuta en una sola transacción.
    """
    try:
        for table in ("corridas", "eventos", "grupo_estudiante", "grupos", "estudiantes",
                      "disponibilidad_docente", "docentes", "materias", "salones"):
            q(f"DELETE FROM {table}")
        _insert("INSERT INTO salones (codigo, capacidad) VALUES (:codigo, :capacidad)",
                t["salones"])
        _insert("INSERT INTO docentes (codigo, nombre) VALUES (:codigo, :nombre)", t["docentes"])
        _insert("INSERT INTO materias (codigo, nombre, horas_semanales) "
                "VALUES (:codigo, :nombre, :horas_semanales)", t["materias"])
        doc = _ids("docentes")
        mat = _ids("materias")
        _insert("INSERT INTO grupos (codigo, materia_id, docente_id) VALUES (:c, :m, :d)",
                [{"c": g["codigo"], "m": mat[g["materia"]], "d": doc[g["docente"]]}
                 for g in t["grupos"]])
        students = sorted({i["estudiante"] for i in t["inscripciones"]})
        _insert("INSERT INTO estudiantes (codigo) VALUES (:c)", [{"c": s} for s in students])
        grp, est = _ids("grupos"), _ids("estudiantes")
        _insert("INSERT INTO grupo_estudiante (grupo_id, estudiante_id) VALUES (:g, :e)",
                [{"g": grp[i["grupo"]], "e": est[i["estudiante"]]} for i in t["inscripciones"]])
        _insert("INSERT INTO disponibilidad_docente (docente_id, franja_id, disponible, preferida) "
                "VALUES (:d, :f, :a, :p)",
                [{"d": doc[r["docente"]], "f": r["franja"], "a": r["disponible"],
                  "p": r["preferida"]} for r in t.get("disponibilidad", [])])
        n_events = sync_eventos()
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return {**{k: len(v) for k, v in t.items()}, "estudiantes": len(students),
            "eventos": n_events}


def _insert(sql, data):
    if data:
        db.session.execute(text(sql), data)


def _ids(table: str) -> dict:
    return {r["codigo"]: r["id"] for r in rows(f"SELECT id, codigo FROM {table}")}


# ----------------------------------------------------------------- reglas
def list_rules() -> list[dict]:
    return rows("SELECT * FROM reglas ORDER BY tipo, nivel, nombre")


def load_rules(only_active: bool = True) -> list[Rule]:
    sql = "SELECT * FROM reglas" + (" WHERE activa" if only_active else "") + " ORDER BY id"
    return [Rule(nombre=r["nombre"], tipo=r["tipo"], condicion=r["condicion"],
                 peso=float(r["peso"]), nivel=r["nivel"], activa=bool(r["activa"]), id=r["id"])
            for r in rows(sql)]


# ------------------------------------------------------- problema (hechos)
def load_problem() -> Problem:
    """Construye el Problem del motor a partir de la base de hechos."""
    fr = franjas()
    slot_index = {r["id"]: i for i, r in enumerate(fr)}
    salones = rows("SELECT id, codigo, capacidad FROM salones ORDER BY id")
    docentes = rows("SELECT id, codigo FROM docentes ORDER BY id")
    grupos = rows("SELECT id, codigo FROM grupos ORDER BY id")
    estudiantes = rows("SELECT id FROM estudiantes ORDER BY id")
    eventos = rows("""SELECT e.id, e.grupo_id, g.docente_id FROM eventos e
                      JOIN grupos g ON g.id = e.grupo_id ORDER BY e.id""")
    if not eventos:
        raise ValueError("no hay eventos: cargue datos académicos antes de optimizar")
    if not salones:
        raise ValueError("no hay salones registrados")

    d_idx = {d["id"]: i for i, d in enumerate(docentes)}
    g_idx = {g["id"]: i for i, g in enumerate(grupos)}
    s_idx = {s["id"]: i for i, s in enumerate(estudiantes)}
    T = len(fr)

    avail = np.ones((len(docentes), T), dtype=bool)
    pref = np.zeros((len(docentes), T), dtype=bool)
    for r in rows("SELECT * FROM disponibilidad_docente"):
        i, t = d_idx[r["docente_id"]], slot_index[r["franja_id"]]
        avail[i, t] = bool(r["disponible"])
        pref[i, t] = bool(r["preferida"])

    cs = np.zeros((len(grupos), max(len(estudiantes), 1)), dtype=bool)
    for r in rows("SELECT grupo_id, estudiante_id FROM grupo_estudiante"):
        cs[g_idx[r["grupo_id"]], s_idx[r["estudiante_id"]]] = True

    return Problem(
        n_slots=T,
        slot_day=[r["dia"] - 1 for r in fr],
        room_capacity=[s["capacidad"] for s in salones],
        event_teacher=[d_idx[e["docente_id"]] for e in eventos],
        event_class=[g_idx[e["grupo_id"]] for e in eventos],
        class_students=cs,
        teacher_available=avail,
        teacher_preferred=pref,
        slot_ids=[r["id"] for r in fr],
        slot_labels=[r["etiqueta"] for r in fr],
        room_ids=[s["id"] for s in salones],
        room_codes=[s["codigo"] for s in salones],
        teacher_codes=[d["codigo"] for d in docentes],
        class_codes=[g["codigo"] for g in grupos],
        event_ids=[e["id"] for e in eventos],
    )


# --------------------------------------------------------------- corridas
def create_run(p: dict) -> int:
    res = q("""INSERT INTO corridas (t_max, k, n, tau, pc, pm, semilla)
               VALUES (:t_max, :k, :n, :tau, :pc, :pm, :seed)""", **p)
    db.session.commit()
    return res.lastrowid


def update_run(run_id: int, **fields) -> None:
    sets = ", ".join(f"{k} = :{k}" for k in fields)
    q(f"UPDATE corridas SET {sets} WHERE id = :id", id=run_id, **fields)
    db.session.commit()


def run_status(run_id: int) -> str | None:
    db.session.rollback()          # ver cambios de otros procesos/hilos
    return q("SELECT estado FROM corridas WHERE id = :id", id=run_id).scalar()


def get_run(run_id: int) -> dict | None:
    return one("SELECT * FROM corridas WHERE id = :id", id=run_id)


def list_runs(limit: int = 50) -> list[dict]:
    return rows("SELECT * FROM corridas ORDER BY id DESC LIMIT :n", n=limit)


def delete_run(run_id: int) -> None:
    q("DELETE FROM corridas WHERE id = :id", id=run_id)
    db.session.commit()


def save_iterations(run_id: int, history: list[dict], elites: list[dict]) -> None:
    """Persiste en bloque el historial y los mejores k de varias iteraciones."""
    _insert("""INSERT INTO historial (corrida_id, iteracion, mejor_f, mejor_h, media_f, diversidad)
               VALUES (:c, :t, :f, :h, :m, :d)""",
            [{"c": run_id, "t": h["t"], "f": h["best_f"], "h": h["best_h"],
              "m": h["mean_f"], "d": h["diversity"]} for h in history])
    _insert("""INSERT INTO horarios (corrida_id, iteracion, rango, aptitud, h, s)
               VALUES (:c, :t, :rango, :f, :h, :s)""",
            [{"c": run_id, **e} for e in elites])
    db.session.commit()


def save_final(run_id: int, problem: Problem, final_iter: int, best: np.ndarray,
               explanations: list[dict]) -> None:
    """Guarda las asignaciones (t, r) y el desglose de violaciones de los k mejores."""
    ids = {r["rango"]: r["id"] for r in rows(
        "SELECT id, rango FROM horarios WHERE corrida_id = :c AND iteracion = :t",
        c=run_id, t=final_iter)}
    for rank, (ind, exp) in enumerate(zip(best, explanations), start=1):
        hid = ids[rank]
        _insert("""INSERT INTO asignaciones (horario_id, evento_id, franja_id, salon_id)
                   VALUES (:h, :e, :f, :s)""",
                [{"h": hid, "e": problem.event_ids[e], "f": problem.slot_ids[int(ind[e, 0])],
                  "s": problem.room_ids[int(ind[e, 1])]} for e in range(problem.n_events)])
        _insert("""INSERT INTO violaciones (horario_id, regla_id, conteo, penalizacion, eventos_json)
                   VALUES (:h, :r, :v, :p, :ev)""",
                [{"h": hid, "r": r["id"], "v": r["V"], "p": r["penalizacion"],
                  "ev": json.dumps([problem.event_ids[i] for i in r["eventos_idx"]])}
                 for r in exp["reglas"] if r["id"] is not None])
    db.session.commit()


def history(run_id: int) -> list[dict]:
    return rows("SELECT iteracion, mejor_f, mejor_h, media_f, diversidad FROM historial "
                "WHERE corrida_id = :c ORDER BY iteracion", c=run_id)


def final_schedules(run_id: int) -> list[dict]:
    """Los k mejores horarios de la última iteración (los que tienen asignaciones)."""
    return rows("""SELECT h.* FROM horarios h
                   WHERE h.corrida_id = :c
                     AND h.iteracion = (SELECT MAX(iteracion) FROM horarios WHERE corrida_id = :c)
                   ORDER BY h.rango""", c=run_id)


def schedule(horario_id: int) -> dict | None:
    return one("SELECT * FROM horarios WHERE id = :id", id=horario_id)


def assignments(horario_id: int) -> list[dict]:
    out = rows("""
        SELECT a.evento_id, a.franja_id, f.dia, f.hora_inicio, s.codigo AS salon, s.capacidad,
               g.codigo AS grupo, m.codigo AS materia, m.nombre AS materia_nombre,
               d.codigo AS docente, d.nombre AS docente_nombre,
               (SELECT COUNT(*) FROM grupo_estudiante ge WHERE ge.grupo_id = g.id) AS estudiantes
        FROM asignaciones a
        JOIN franjas f ON f.id = a.franja_id
        JOIN salones s ON s.id = a.salon_id
        JOIN eventos e ON e.id = a.evento_id
        JOIN grupos g ON g.id = e.grupo_id
        JOIN materias m ON m.id = g.materia_id
        JOIN docentes d ON d.id = g.docente_id
        WHERE a.horario_id = :h ORDER BY a.franja_id, s.codigo""", h=horario_id)
    for r in out:
        r["franja"] = slot_label(r)
    return out


def violations(horario_id: int) -> list[dict]:
    out = rows("""SELECT v.*, r.nombre, r.tipo, r.nivel, r.condicion, r.peso
                  FROM violaciones v JOIN reglas r ON r.id = v.regla_id
                  WHERE v.horario_id = :h ORDER BY v.penalizacion DESC, r.nombre""", h=horario_id)
    for r in out:
        r["eventos"] = json.loads(r["eventos_json"]) if r["eventos_json"] else []
    return out
