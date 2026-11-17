"""Gestión de reglas lógicas (Hito 2, sección 4.1, Tabla 6).

Las reglas se validan con el mismo motor que las evalúa, de modo que
una condición inválida se rechaza al guardarla y no durante la corrida.
"""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError

from engine import Rule
from engine.fitness import LEVELS
from engine.rules import CONDITIONS

from ..models import repo

bp = Blueprint("reglas", __name__, url_prefix="/reglas")


def _leer() -> tuple[dict, str | None]:
    f = request.form
    data = {"nombre": f.get("nombre", "").strip(), "tipo": f.get("tipo", ""),
            "nivel": f.get("nivel", ""), "condicion": f.get("condicion", "").strip(),
            "descripcion": f.get("descripcion", "").strip() or None,
            "activa": f.get("activa") == "on"}
    try:
        data["peso"] = float(f.get("peso", ""))
        if not data["nombre"]:
            raise ValueError("el nombre es obligatorio")
        Rule(nombre=data["nombre"], tipo=data["tipo"], condicion=data["condicion"],
             peso=data["peso"], nivel=data["nivel"])
    except ValueError as exc:
        return data, str(exc).replace("could not convert string to float", "peso inválido")
    return data, None


@bp.get("/")
def lista():
    return render_template("reglas.html", reglas=repo.list_rules(), catalogo=CONDITIONS,
                           niveles=LEVELS, item=None)


@bp.post("/")
def crear():
    data, error = _leer()
    if not error:
        try:
            repo.q("""INSERT INTO reglas (nombre, tipo, nivel, condicion, peso, activa, descripcion)
                      VALUES (:nombre, :tipo, :nivel, :condicion, :peso, :activa, :descripcion)""", **data)
            repo.db.session.commit()
            flash(f"Regla '{data['nombre']}' creada.", "ok")
            return redirect(url_for(".lista"))
        except IntegrityError:
            repo.db.session.rollback()
            error = "ya existe una regla con ese nombre"
    flash(error, "error")
    return render_template("reglas.html", reglas=repo.list_rules(), catalogo=CONDITIONS,
                           niveles=LEVELS, item=data)


@bp.route("/<int:regla_id>/editar", methods=["GET", "POST"])
def editar(regla_id):
    item = repo.one("SELECT * FROM reglas WHERE id = :id", id=regla_id) or abort(404)
    if request.method == "POST":
        data, error = _leer()
        if not error:
            try:
                repo.q("""UPDATE reglas SET nombre = :nombre, tipo = :tipo, nivel = :nivel,
                          condicion = :condicion, peso = :peso, activa = :activa,
                          descripcion = :descripcion WHERE id = :id""", id=regla_id, **data)
                repo.db.session.commit()
                flash("Regla actualizada.", "ok")
                return redirect(url_for(".lista"))
            except IntegrityError:
                repo.db.session.rollback()
                error = "ya existe una regla con ese nombre"
        flash(error, "error")
        item = {**data, "id": regla_id}
    return render_template("regla_editar.html", item=item, catalogo=CONDITIONS, niveles=LEVELS)


@bp.post("/<int:regla_id>/estado")
def alternar(regla_id):
    repo.q("UPDATE reglas SET activa = NOT activa WHERE id = :id", id=regla_id)
    repo.db.session.commit()
    return redirect(url_for(".lista"))


@bp.post("/<int:regla_id>/eliminar")
def eliminar(regla_id):
    repo.q("DELETE FROM reglas WHERE id = :id", id=regla_id)
    repo.db.session.commit()
    flash("Regla eliminada.", "ok")
    return redirect(url_for(".lista"))
