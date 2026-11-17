"""Consulta de resultados (Dashboards de visualización, Fig. 6; Tabla 13).

- Corridas y sus k mejores horarios con F, H y S.
- Horario por grupo, docente o salón (cuadrícula día × franja).
- Explicación: desglose de violaciones por regla y eventos involucrados.
- Evolución: mejor aptitud, aptitud media y diversidad por iteración.
- Exportación del horario a CSV.
"""
import csv
import io

from flask import (Blueprint, Response, abort, flash, redirect, render_template, request,
                   url_for)

from ..models import repo
from ..services import optimizer

bp = Blueprint("resultados", __name__, url_prefix="/corridas")

POR = {"grupo": "Grupo", "docente": "Docente", "salon": "Salón"}


def _run(run_id):
    return repo.get_run(run_id) or abort(404)


def _horario(run_id, horario_id):
    h = repo.schedule(horario_id)
    if not h or h["corrida_id"] != run_id:
        abort(404)
    return h


@bp.get("/")
def corridas():
    return render_template("corridas.html", corridas=repo.list_runs())


@bp.get("/<int:run_id>")
def corrida(run_id):
    run = _run(run_id)
    finales = repo.final_schedules(run_id) if run["estado"] in ("terminada", "cancelada") else []
    hist = repo.history(run_id)
    comparacion = {}
    for h in finales:
        for v in repo.violations(h["id"]):
            comparacion.setdefault((v["nombre"], v["tipo"]), {})[h["rango"]] = v["conteo"]
    return render_template("corrida.html", run=run, finales=finales, hist_n=len(hist),
                           ultimo=hist[-1] if hist else None, comparacion=comparacion)


@bp.post("/<int:run_id>/cancelar")
def cancelar(run_id):
    if optimizer.cancel_run(run_id):
        flash("Cancelación solicitada; se conservarán los mejores hasta ahora.", "warn")
    return redirect(url_for(".corrida", run_id=run_id))


@bp.post("/<int:run_id>/eliminar")
def eliminar(run_id):
    run = _run(run_id)
    if run["estado"] in ("pendiente", "ejecutando", "cancelando"):
        flash("No se puede eliminar una corrida en ejecución.", "error")
        return redirect(url_for(".corrida", run_id=run_id))
    repo.delete_run(run_id)
    flash(f"Corrida #{run_id} eliminada.", "ok")
    return redirect(url_for(".corridas"))


def _conflict_events(horario_id) -> set:
    return {e for v in repo.violations(horario_id) if v["tipo"] == "HC" for e in v["eventos"]}


@bp.get("/<int:run_id>/horario/<int:horario_id>")
def horario(run_id, horario_id):
    run, h = _run(run_id), _horario(run_id, horario_id)
    asig = repo.assignments(horario_id)
    por = request.args.get("por", "grupo")
    if por not in POR:
        por = "grupo"
    opciones = sorted({a[por] for a in asig})
    valor = request.args.get("valor") or (opciones[0] if opciones else None)
    sel = [a for a in asig if a[por] == valor]
    franjas = repo.franjas()
    dias = repo.DIAS[:max(f["dia"] for f in franjas)]
    horas = sorted({str(f["hora_inicio"])[:-3].zfill(5) for f in franjas})
    celdas = {}
    for a in sel:
        celdas.setdefault((a["dia"], str(a["hora_inicio"])[:-3].zfill(5)), []).append(a)
    return render_template("horario.html", run=run, h=h, por=por, POR=POR, opciones=opciones,
                           valor=valor, dias=dias, horas=horas, celdas=celdas,
                           conflictos=_conflict_events(horario_id), total=len(asig))


@bp.get("/<int:run_id>/horario/<int:horario_id>/explicacion")
def explicacion(run_id, horario_id):
    run, h = _run(run_id), _horario(run_id, horario_id)
    eventos = {a["evento_id"]: a for a in repo.assignments(horario_id)}
    viol = repo.violations(horario_id)
    total_v = sum(v["conteo"] for v in viol)
    cubiertas = sum(v["conteo"] for v in viol if v["conteo"] and v["eventos"])
    niveles = {}
    for v in viol:
        niveles[v["nivel"]] = niveles.get(v["nivel"], 0) + v["penalizacion"]
    return render_template("explicacion.html", run=run, h=h, viol=viol, eventos=eventos,
                           niveles=niveles, cobertura=(cubiertas / total_v if total_v else 1.0))


@bp.get("/<int:run_id>/evolucion")
def evolucion(run_id):
    return render_template("evolucion.html", run=_run(run_id), hist=repo.history(run_id))


@bp.get("/<int:run_id>/horario/<int:horario_id>/export.csv")
def exportar(run_id, horario_id):
    _horario(run_id, horario_id)
    buf = io.StringIO()
    cols = ["evento_id", "grupo", "materia", "materia_nombre", "docente", "docente_nombre",
            "franja", "salon", "capacidad", "estudiantes"]
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(repo.assignments(horario_id))
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition":
                             f"attachment; filename=horario_c{run_id}_h{horario_id}.csv"})
