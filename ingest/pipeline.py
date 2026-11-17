"""Reading and validation of the UTP coordination files.

Accepted formats (Table 14 of Milestone 2):
- XLSX with one sheet per entity (sheet names are the SCHEMA keys).
- CSV, one file per entity, whose name (without extension) is the
  entity, e.g. `salones.csv`.

Ingestion fully replaces the academic data set, which is why the
entities marked `required` are mandatory; `disponibilidad` is optional
(without it, every teacher is available in every time slot).
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from pathlib import Path

N_SLOTS = 60

SCHEMA: dict[str, dict] = {
    "salones": {"required": True, "cols": {"codigo": str, "capacidad": int}},
    "docentes": {"required": True, "cols": {"codigo": str, "nombre": str}},
    "materias": {"required": True, "cols": {"codigo": str, "nombre": str, "horas_semanales": int}},
    "grupos": {"required": True, "cols": {"codigo": str, "materia": str, "docente": str}},
    "inscripciones": {"required": True, "cols": {"grupo": str, "estudiante": str}},
    "disponibilidad": {"required": False,
                       "cols": {"docente": str, "franja": int, "disponible": int, "preferida": int}},
}
OPTIONAL_COLS = {("docentes", "nombre"), ("materias", "nombre")}


@dataclass
class IngestReport:
    tables: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def summary(self) -> dict:
        return {name: len(rows) for name, rows in self.tables.items()}


# Reading
def _norm(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value).strip()


def _rows_from_matrix(matrix: list[list]) -> list[dict]:
    rows = [r for r in matrix if any(_norm(c) for c in r)]
    if not rows:
        return []
    header = [_norm(h).lower() for h in rows[0]]
    return [{h: _norm(v) for h, v in zip(header, r) if h} for r in rows[1:]]


def read_xlsx(data: bytes) -> dict[str, list[dict]]:
    from openpyxl import load_workbook

    wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    out = {}
    for ws in wb.worksheets:
        name = ws.title.strip().lower()
        if name in SCHEMA:
            out[name] = _rows_from_matrix([list(r) for r in ws.iter_rows(values_only=True)])
    return out


def read_csv(data: bytes, entity: str) -> dict[str, list[dict]]:
    text = data.decode("utf-8-sig")
    dialect = csv.Sniffer().sniff(text.splitlines()[0] if text else ",", delimiters=",;\t")
    return {entity: _rows_from_matrix(list(csv.reader(io.StringIO(text), dialect)))}


def read_files(files: list[tuple[str, bytes]]) -> tuple[dict, list[str]]:
    """Turn [(file_name, bytes)] into (tables, read errors)."""
    tables, errors = {}, []
    for filename, data in files:
        ext = Path(filename).suffix.lower()
        stem = Path(filename).stem.lower()
        try:
            if ext == ".xlsx":
                tables.update(read_xlsx(data))
            elif ext == ".csv":
                if stem not in SCHEMA:
                    errors.append(f"{filename}: el nombre debe ser una entidad {sorted(SCHEMA)}")
                    continue
                tables.update(read_csv(data, stem))
            else:
                errors.append(f"{filename}: formato no soportado (use CSV o XLSX)")
        except Exception as exc:  # noqa: BLE001 - reported to the user
            errors.append(f"{filename}: no se pudo leer ({exc})")
    return tables, errors


# Validation
def _cast(entity, row_no, col, raw, typ, errors):
    if raw == "":
        if (entity, col) in OPTIONAL_COLS:
            return ""
        errors.append(f"{entity} fila {row_no}: '{col}' está vacío")
        return None
    if typ is int:
        try:
            f = float(raw)
            if not f.is_integer():
                raise ValueError
            return int(f)
        except ValueError:
            errors.append(f"{entity} fila {row_no}: '{col}' debe ser entero (valor '{raw}')")
            return None
    return raw


def validate(raw: dict[str, list[dict]], n_slots: int = N_SLOTS,
             max_rooms_hint: int | None = None) -> IngestReport:
    """Validate types, uniqueness, references and consistency (Table 12)."""
    rep = IngestReport()
    for entity, spec in SCHEMA.items():
        if entity not in raw:
            if spec["required"]:
                rep.errors.append(f"falta la entidad '{entity}'")
            continue
        rows = raw[entity]
        if rows:
            missing = [c for c in spec["cols"] if c not in rows[0] and (entity, c) not in OPTIONAL_COLS]
            if missing:
                rep.errors.append(f"{entity}: faltan columnas {missing}")
                continue
        clean = []
        for i, row in enumerate(rows, start=2):           # row 1 = header
            item, bad = {}, False
            for col, typ in spec["cols"].items():
                val = _cast(entity, i, col, row.get(col, ""), typ, rep.errors)
                bad |= val is None
                item[col] = val
            if not bad:
                item["_fila"] = i
                clean.append(item)
        rep.tables[entity] = clean
    if rep.errors:
        return rep

    t = rep.tables

    def unique(entity, key=("codigo",)):
        seen = {}
        for r in t[entity]:
            k = tuple(r[c] for c in key)
            if k in seen:
                rep.errors.append(f"{entity} fila {r['_fila']}: {'/'.join(map(str, k))} "
                                  f"duplicado (ya en fila {seen[k]})")
            seen.setdefault(k, r["_fila"])
        return {k[0] if len(k) == 1 else k for k in seen}

    salones = unique("salones")
    docentes = unique("docentes")
    materias = unique("materias")
    grupos = unique("grupos")
    unique("inscripciones", ("grupo", "estudiante"))
    if "disponibilidad" in t:
        unique("disponibilidad", ("docente", "franja"))

    for r in t["salones"]:
        if r["capacidad"] <= 0:
            rep.errors.append(f"salones fila {r['_fila']}: capacidad debe ser positiva")
    for r in t["materias"]:
        if r["horas_semanales"] <= 0:
            rep.errors.append(f"materias fila {r['_fila']}: horas_semanales debe ser > 0")
    for r in t["grupos"]:
        if r["materia"] not in materias:
            rep.errors.append(f"grupos fila {r['_fila']}: materia '{r['materia']}' no existe")
        if r["docente"] not in docentes:
            rep.errors.append(f"grupos fila {r['_fila']}: docente '{r['docente']}' no existe")
    for r in t["inscripciones"]:
        if r["grupo"] not in grupos:
            rep.errors.append(f"inscripciones fila {r['_fila']}: grupo '{r['grupo']}' no existe")
    for r in t.get("disponibilidad", []):
        if r["docente"] not in docentes:
            rep.errors.append(f"disponibilidad fila {r['_fila']}: docente '{r['docente']}' no existe")
        if not 1 <= r["franja"] <= n_slots:
            rep.errors.append(f"disponibilidad fila {r['_fila']}: franja fuera de 1..{n_slots}")
        for flag in ("disponible", "preferida"):
            if r[flag] not in (0, 1):
                rep.errors.append(f"disponibilidad fila {r['_fila']}: '{flag}' debe ser 0 o 1")
    if rep.errors:
        return rep

    # Global consistency (warnings: the algorithm can still run)
    hours = {m["codigo"]: m["horas_semanales"] for m in t["materias"]}
    n_events = sum(hours[g["materia"]] for g in t["grupos"])
    capacity = n_slots * len(salones)
    if n_events > capacity:
        rep.errors.append(f"hay {n_events} eventos y solo {capacity} paquetes (t, r): "
                          "el problema es infactible por construcción")
    max_cap = max((r["capacidad"] for r in t["salones"]), default=0)
    size = {}
    for r in t["inscripciones"]:
        size[r["grupo"]] = size.get(r["grupo"], 0) + 1
    for g in t["grupos"]:
        if size.get(g["codigo"], 0) == 0:
            rep.warnings.append(f"el grupo {g['codigo']} no tiene estudiantes inscritos")
        elif size[g["codigo"]] > max_cap:
            rep.warnings.append(f"el grupo {g['codigo']} ({size[g['codigo']]} est.) no cabe en "
                                f"ningún salón (máx. {max_cap})")
    load = {}
    for g in t["grupos"]:
        load[g["docente"]] = load.get(g["docente"], 0) + hours[g["materia"]]
    blocked = {}
    for r in t.get("disponibilidad", []):
        if not r["disponible"]:
            blocked[r["docente"]] = blocked.get(r["docente"], 0) + 1
    for d, h in load.items():
        if h > n_slots - blocked.get(d, 0):
            rep.errors.append(f"el docente {d} tiene {h} horas y solo "
                              f"{n_slots - blocked.get(d, 0)} franjas disponibles")
    return rep
