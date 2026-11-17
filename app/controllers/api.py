"""REST/JSON API adapters (Fig. 6 and Fig. 10, Table 14 of Milestone 2).

They let legacy and external systems query data, launch runs and
retrieve schedules and explanations without using the web interface.
Errors are always returned as JSON: {"error": "...", ...}.
"""
from flask import Blueprint, current_app, jsonify, request
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException

from engine import Rule

from ..models import repo
from ..services import optimizer

bp = Blueprint("api", __name__, url_prefix="/api/v1")

ENTIDADES = {
    "salones": "SELECT id, codigo, capacidad FROM salones ORDER BY codigo",
    "docentes": "SELECT id, codigo, nombre FROM docentes ORDER BY codigo",
    "materias": "SELECT id, codigo, nombre, horas_semanales FROM materias ORDER BY codigo",
    "grupos": """SELECT g.id, g.codigo, m.codigo AS materia, d.codigo AS docente,
                        (SELECT COUNT(*) FROM grupo_estudiante ge WHERE ge.grupo_id = g.id) AS estudiantes
                 FROM grupos g JOIN materias m ON m.id = g.materia_id
                 JOIN docentes d ON d.id = g.docente_id ORDER BY g.codigo""",
    "franjas": None,
}
RUN_FIELDS = ("id", "creada_en", "estado", "t_max", "k", "n", "tau", "pc", "pm", "semilla",
              "n_eventos", "generaciones", "g_factible", "mejor_f", "mejor_h", "f_inicial",
              "evaluaciones", "detenida_por", "tiempo_s", "mensaje")


def error(msg, status=400, **extra):
    return jsonify(error=msg, **extra), status


@bp.errorhandler(HTTPException)
def http_error(exc):
    return error(exc.description, exc.code)


def _json(data):
    """Convert MySQL types (time, datetime) to serializable text."""
    if isinstance(data, (list, tuple)):
        return [_json(x) for x in data]
    if isinstance(data, dict):
        return {k: _json(v) for k, v in data.items()}
    if isinstance(data, (int, float, str, bool, type(None))):
        return data
    return str(data)


def _run_or_404(run_id):
    run = repo.get_run(run_id)
    if not run:
        return None, error("corrida no encontrada", 404)
    return run, None


# Base data
@bp.get("/estado")
def estado():
    return jsonify(conteos=repo.counts())


@bp.get("/<entidad>")
def listar(entidad):
    if entidad not in ENTIDADES:
        return error(f"entidad desconocida; use {sorted(ENTIDADES)}", 404)
    data = repo.franjas() if entidad == "franjas" else repo.rows(ENTIDADES[entidad])
    return jsonify(_json(data))


# Rules
@bp.get("/reglas")
def reglas():
    return jsonify(_json(repo.list_rules()))


def _rule_payload(body: dict, base: dict | None = None) -> dict:
    d = {**(base or {}), **{k: body[k] for k in ("nombre", "tipo", "nivel", "condicion", "peso",
                                                 "activa", "descripcion") if k in body}}
    d.setdefault("activa", True)
    d.setdefault("descripcion", None)
    rule = Rule(nombre=str(d.get("nombre", "")), tipo=d.get("tipo", ""),
                condicion=str(d.get("condicion", "")), peso=float(d.get("peso", -1)),
                nivel=d.get("nivel") or "")
    d["nivel"] = rule.nivel
    d["peso"] = rule.peso
    d["activa"] = bool(d["activa"])
    return d


@bp.post("/reglas")
def crear_regla():
    try:
        d = _rule_payload(request.get_json(force=True, silent=True) or {})
        res = repo.q("""INSERT INTO reglas (nombre, tipo, nivel, condicion, peso, activa, descripcion)
                        VALUES (:nombre, :tipo, :nivel, :condicion, :peso, :activa, :descripcion)""",
                     **{k: d[k] for k in ("nombre", "tipo", "nivel", "condicion", "peso", "activa",
                                          "descripcion")})
        repo.db.session.commit()
    except (ValueError, TypeError) as exc:
        return error(str(exc))
    except IntegrityError:
        repo.db.session.rollback()
        return error("ya existe una regla con ese nombre", 409)
    return jsonify(_json(repo.one("SELECT * FROM reglas WHERE id = :id", id=res.lastrowid))), 201


@bp.patch("/reglas/<int:regla_id>")
def editar_regla(regla_id):
    base = repo.one("SELECT * FROM reglas WHERE id = :id", id=regla_id)
    if not base:
        return error("regla no encontrada", 404)
    try:
        d = _rule_payload(request.get_json(force=True, silent=True) or {}, base)
        repo.q("""UPDATE reglas SET nombre = :nombre, tipo = :tipo, nivel = :nivel,
                  condicion = :condicion, peso = :peso, activa = :activa,
                  descripcion = :descripcion WHERE id = :id""",
               **{k: d[k] for k in ("nombre", "tipo", "nivel", "condicion", "peso", "activa",
                                    "descripcion")}, id=regla_id)
        repo.db.session.commit()
    except (ValueError, TypeError) as exc:
        return error(str(exc))
    except IntegrityError:
        repo.db.session.rollback()
        return error("ya existe una regla con ese nombre", 409)
    return jsonify(_json(repo.one("SELECT * FROM reglas WHERE id = :id", id=regla_id)))


# Runs
@bp.get("/corridas")
def corridas():
    return jsonify(_json([{k: r[k] for k in RUN_FIELDS} for r in repo.list_runs()]))


@bp.post("/corridas")
def crear_corrida():
    body = request.get_json(force=True, silent=True) or {}
    try:
        params = optimizer.parse_params(body)
    except ValueError as exc:
        return error(str(exc))
    if not repo.counts()["eventos"]:
        return error("no hay eventos: importe datos académicos primero", 409)
    run_id = optimizer.start_run(current_app._get_current_object(), params)
    return jsonify(id=run_id, estado="pendiente", url=f"/api/v1/corridas/{run_id}"), 202


@bp.get("/corridas/<int:run_id>")
def corrida(run_id):
    run, err = _run_or_404(run_id)
    if err:
        return err
    out = {k: run[k] for k in RUN_FIELDS}
    out["mejores"] = repo.final_schedules(run_id) if run["estado"] in ("terminada", "cancelada") else []
    return jsonify(_json(out))


@bp.post("/corridas/<int:run_id>/cancelar")
def cancelar(run_id):
    _, err = _run_or_404(run_id)
    if err:
        return err
    if not optimizer.cancel_run(run_id):
        return error("la corrida no está en ejecución", 409)
    return jsonify(id=run_id, estado="cancelando"), 202


@bp.get("/corridas/<int:run_id>/historial")
def historial(run_id):
    _, err = _run_or_404(run_id)
    return err or jsonify(_json(repo.history(run_id)))


# Schedules
def _schedule_or_404(horario_id):
    h = repo.schedule(horario_id)
    if not h:
        return None, error("horario no encontrado", 404)
    if not repo.one("SELECT 1 AS x FROM asignaciones WHERE horario_id = :h LIMIT 1", h=horario_id):
        return None, error("este horario no tiene asignaciones guardadas "
                           "(solo se guardan las de la iteración final)", 404)
    return h, None


@bp.get("/horarios/<int:horario_id>")
def horario(horario_id):
    h, err = _schedule_or_404(horario_id)
    if err:
        return err
    asig = repo.assignments(horario_id)
    por = request.args.get("por")
    valor = request.args.get("valor")
    if por:
        if por not in ("grupo", "docente", "salon"):
            return error("'por' debe ser grupo, docente o salon")
        if valor:
            asig = [a for a in asig if a[por] == valor]
    return jsonify(_json({**h, "asignaciones": asig}))


@bp.get("/horarios/<int:horario_id>/explicacion")
def explicacion(horario_id):
    h, err = _schedule_or_404(horario_id)
    if err:
        return err
    viol = repo.violations(horario_id)
    for v in viol:
        v.pop("eventos_json", None)
    total = sum(v["conteo"] for v in viol)
    cub = sum(v["conteo"] for v in viol if v["conteo"] and v["eventos"])
    return jsonify(_json({"horario": h, "F": h["aptitud"], "H": h["h"], "S": h["s"],
                          "cobertura": cub / total if total else 1.0, "reglas": viol}))
