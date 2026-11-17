"""Registration and lookup of academic data (graphical views, Fig. 6).

Simple CRUD for rooms, teachers, subjects and groups with validation
(Table 12), plus the availability/preference grid of each teacher over
the 60 time slots. Students and enrollments are loaded through
ingestion (XLSX/CSV).
"""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError

from ..models import repo

bp = Blueprint("datos", __name__, url_prefix="/datos")

# field, label, type (text | int | fk:<table>)
ENTIDADES = {
    "salones": {"titulo": "Salones", "campos": [("codigo", "Código", "text"),
                                                ("capacidad", "Capacidad", "int")]},
    "docentes": {"titulo": "Docentes", "campos": [("codigo", "Código", "text"),
                                                  ("nombre", "Nombre", "text")]},
    "materias": {"titulo": "Materias", "campos": [("codigo", "Código", "text"),
                                                  ("nombre", "Nombre", "text"),
                                                  ("horas_semanales", "Horas semanales", "int")]},
    "grupos": {"titulo": "Grupos", "campos": [("codigo", "Código", "text"),
                                              ("materia_id", "Materia", "fk:materias"),
                                              ("docente_id", "Docente", "fk:docentes")]},
}
LISTADOS = {
    "salones": "SELECT * FROM salones ORDER BY codigo",
    "docentes": """SELECT d.*, (SELECT COUNT(*) FROM grupos g WHERE g.docente_id = d.id) AS grupos,
                          (SELECT COUNT(*) FROM disponibilidad_docente x
                            WHERE x.docente_id = d.id AND NOT x.disponible) AS bloqueadas
                   FROM docentes d ORDER BY codigo""",
    "materias": "SELECT * FROM materias ORDER BY codigo",
    "grupos": """SELECT g.id, g.codigo, m.codigo AS materia_id, d.codigo AS docente_id,
                        m.horas_semanales AS horas,
                        (SELECT COUNT(*) FROM grupo_estudiante ge WHERE ge.grupo_id = g.id) AS estudiantes
                 FROM grupos g JOIN materias m ON m.id = g.materia_id
                 JOIN docentes d ON d.id = g.docente_id ORDER BY g.codigo""",
}
EXTRA_COLS = {"docentes": [("grupos", "Grupos"), ("bloqueadas", "Franjas bloqueadas")],
              "grupos": [("horas", "Horas/sem"), ("estudiantes", "Estudiantes")]}


def _entidad(nombre):
    if nombre not in ENTIDADES:
        abort(404)
    return ENTIDADES[nombre]


def _opciones(cfg):
    return {campo: repo.rows(f"SELECT id, codigo FROM {tipo[3:]} ORDER BY codigo")
            for campo, _, tipo in cfg["campos"] if tipo.startswith("fk:")}


def _leer_form(cfg) -> tuple[dict, list[str]]:
    data, errores = {}, []
    for campo, etiqueta, tipo in cfg["campos"]:
        val = request.form.get(campo, "").strip()
        if not val and campo != "nombre":
            errores.append(f"{etiqueta} es obligatorio")
            continue
        if tipo == "int" or tipo.startswith("fk:"):
            try:
                val = int(val)
            except ValueError:
                errores.append(f"{etiqueta} debe ser un entero")
                continue
            if tipo == "int" and val <= 0:
                errores.append(f"{etiqueta} debe ser mayor que cero")
        data[campo] = val
    return data, errores


@bp.get("/<entidad>")
def lista(entidad):
    cfg = _entidad(entidad)
    return render_template("datos/lista.html", entidad=entidad, cfg=cfg, entidades=ENTIDADES,
                           filas=repo.rows(LISTADOS[entidad]), extra=EXTRA_COLS.get(entidad, []),
                           opciones=_opciones(cfg))


@bp.post("/<entidad>")
def crear(entidad):
    cfg = _entidad(entidad)
    data, errores = _leer_form(cfg)
    if not errores:
        cols = ", ".join(data)
        vals = ", ".join(f":{c}" for c in data)
        try:
            repo.q(f"INSERT INTO {entidad} ({cols}) VALUES ({vals})", **data)
            if entidad in ("grupos", "materias"):
                repo.sync_eventos()
            repo.db.session.commit()
            flash(f"{cfg['titulo'][:-1] if entidad != 'materias' else 'Materia'} registrado(a).", "ok")
        except IntegrityError:
            repo.db.session.rollback()
            errores.append("el código ya existe o una referencia no es válida")
    for e in errores:
        flash(e, "error")
    return redirect(url_for(".lista", entidad=entidad))


@bp.route("/<entidad>/<int:item_id>/editar", methods=["GET", "POST"])
def editar(entidad, item_id):
    cfg = _entidad(entidad)
    item = repo.one(f"SELECT * FROM {entidad} WHERE id = :id", id=item_id) or abort(404)
    if request.method == "POST":
        data, errores = _leer_form(cfg)
        if not errores:
            sets = ", ".join(f"{c} = :{c}" for c in data)
            try:
                repo.q(f"UPDATE {entidad} SET {sets} WHERE id = :id", id=item_id, **data)
                if entidad in ("grupos", "materias"):
                    repo.sync_eventos()
                repo.db.session.commit()
                flash("Cambios guardados.", "ok")
                return redirect(url_for(".lista", entidad=entidad))
            except IntegrityError:
                repo.db.session.rollback()
                errores.append("el código ya existe o una referencia no es válida")
        for e in errores:
            flash(e, "error")
        item = {**item, **request.form}
    return render_template("datos/editar.html", entidad=entidad, cfg=cfg, item=item,
                           opciones=_opciones(cfg))


@bp.post("/<entidad>/<int:item_id>/eliminar")
def eliminar(entidad, item_id):
    _entidad(entidad)
    try:
        repo.q(f"DELETE FROM {entidad} WHERE id = :id", id=item_id)
        repo.db.session.commit()
        flash("Registro eliminado.", "ok")
    except IntegrityError:
        repo.db.session.rollback()
        flash("No se puede eliminar: otros registros dependen de él (p. ej. grupos).", "error")
    return redirect(url_for(".lista", entidad=entidad))


@bp.route("/docentes/<int:item_id>/disponibilidad", methods=["GET", "POST"])
def disponibilidad(item_id):
    docente = repo.one("SELECT * FROM docentes WHERE id = :id", id=item_id) or abort(404)
    franjas = repo.franjas()
    if request.method == "POST":
        bloqueadas = {int(x) for x in request.form.getlist("bloqueada")}
        preferidas = {int(x) for x in request.form.getlist("preferida")} - bloqueadas
        repo.q("DELETE FROM disponibilidad_docente WHERE docente_id = :d", d=item_id)
        data = [{"d": item_id, "f": f["id"], "a": f["id"] not in bloqueadas,
                 "p": f["id"] in preferidas}
                for f in franjas if f["id"] in bloqueadas or f["id"] in preferidas]
        if data:
            repo.db.session.execute(repo.text(
                "INSERT INTO disponibilidad_docente (docente_id, franja_id, disponible, preferida) "
                "VALUES (:d, :f, :a, :p)"), data)
        repo.db.session.commit()
        flash("Disponibilidad actualizada.", "ok")
        return redirect(url_for(".disponibilidad", item_id=item_id))
    marcas = {r["franja_id"]: r for r in repo.rows(
        "SELECT * FROM disponibilidad_docente WHERE docente_id = :d", d=item_id)}
    por_dia = max(f["dia"] for f in franjas)
    filas = {}
    for f in franjas:
        filas.setdefault(str(f["hora_inicio"])[:-3].zfill(5), []).append(f)
    return render_template("datos/disponibilidad.html", docente=docente, filas=filas,
                           marcas=marcas, dias=repo.DIAS[:por_dia])
