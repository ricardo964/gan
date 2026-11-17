"""Configuración de parámetros e inicio de la optimización (Fig. 7, pasos 1 a 5)."""
from flask import (Blueprint, current_app, flash, redirect, render_template, request,
                   url_for)

from engine.ga import GAParams

from ..models import repo
from ..services import optimizer

bp = Blueprint("optimizacion", __name__, url_prefix="/optimizar")


@bp.get("/")
def formulario():
    return render_template("optimizar.html", p=GAParams(), c=repo.counts(),
                           activas=sum(1 for r in repo.list_rules() if r["activa"]))


@bp.post("/")
def iniciar():
    try:
        params = optimizer.parse_params(request.form)
    except ValueError as exc:
        flash(str(exc), "error")
        return render_template("optimizar.html", p=request.form, c=repo.counts(),
                               activas=sum(1 for r in repo.list_rules() if r["activa"])), 400
    run_id = optimizer.start_run(current_app._get_current_object(), params)
    flash(f"Corrida #{run_id} iniciada.", "ok")
    return redirect(url_for("resultados.corrida", run_id=run_id))
