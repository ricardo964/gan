"""Import of the UTP coordination files (ingestion pipelines)."""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from ingest import SCHEMA, read_files, validate

from ..models import repo

bp = Blueprint("ingesta", __name__, url_prefix="/ingesta")

MAX_ERRORES = 50


@bp.get("/")
def formulario():
    return render_template("ingesta.html", schema=SCHEMA, reporte=None)


@bp.post("/")
def importar():
    files = [(f.filename, f.read()) for f in request.files.getlist("archivos") if f.filename]
    if not files:
        flash("Seleccione al menos un archivo.", "error")
        return redirect(url_for(".formulario"))
    tables, read_errors = read_files(files)
    rep = validate(tables)
    rep.errors = read_errors + rep.errors
    if rep.ok:
        try:
            resumen = repo.replace_academic_data(rep.tables)
        except Exception as exc:  # noqa: BLE001 - database error shown to the user
            rep.errors.append(f"error al guardar en la base de datos: {exc}")
        else:
            flash("Datos importados: " + ", ".join(f"{k} {v}" for k, v in resumen.items()), "ok")
            for w in rep.warnings:
                flash(w, "warn")
            return redirect(url_for("inicio.index"))
    return render_template("ingesta.html", schema=SCHEMA, reporte=rep,
                           errores=rep.errors[:MAX_ERRORES], omitidos=max(0, len(rep.errors) - MAX_ERRORES))
