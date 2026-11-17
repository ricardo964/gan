"""Generate a sample XLSX with the ingestion format.

Usage:
    python scripts/generar_datos.py [salida.xlsx] [--grupos 30] [--estudiantes 400] [--semilla 0]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from openpyxl import Workbook  # noqa: E402

from engine.synthetic import SyntheticSpec, generate_tables  # noqa: E402
from ingest import SCHEMA  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("salida", nargs="?", default="datos/ejemplo_utp.xlsx")
    ap.add_argument("--salones", type=int, default=12)
    ap.add_argument("--docentes", type=int, default=15)
    ap.add_argument("--materias", type=int, default=20)
    ap.add_argument("--grupos", type=int, default=30)
    ap.add_argument("--estudiantes", type=int, default=400)
    ap.add_argument("--semilla", type=int, default=0)
    a = ap.parse_args()

    tables = generate_tables(SyntheticSpec(
        n_rooms=a.salones, n_teachers=a.docentes, n_subjects=a.materias,
        n_groups=a.grupos, n_students=a.estudiantes, seed=a.semilla))
    wb = Workbook()
    wb.remove(wb.active)
    for name, spec in SCHEMA.items():
        ws = wb.create_sheet(name)
        cols = list(spec["cols"])
        ws.append(cols)
        for row in tables[name]:
            ws.append([row[c] for c in cols])
    out = Path(a.salida)
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    print(f"{out}: " + ", ".join(f"{k}={len(v)}" for k, v in tables.items()))


if __name__ == "__main__":
    main()
