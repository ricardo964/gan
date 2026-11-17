import numpy as np
import pytest

from engine import Evaluator, Rule
from engine.rules import parse_condition


def ind(*pairs):
    return np.array(pairs, dtype=np.int64)


def test_horario_factible_tiene_F_cero(tiny, base_rules):
    ev = Evaluator(tiny, base_rules)
    e = ev.evaluate(ind((0, 0), (1, 0), (2, 1)))
    assert e.F == 0 and e.H == 0 and e.feasible


def test_conflictos_medio_y_profundo(tiny, base_rules):
    ev = Evaluator(tiny, base_rules)
    # e0 and e1 at t0, room 0: teacher l0 duplicated, room duplicated and s1 in c0 and c1
    e = ev.evaluate(ind((0, 0), (0, 0), (2, 1)))
    v = dict(zip([r.nombre for r in ev.rules], e.violations))
    assert v == {"disp": 0, "cap": 0, "doc": 1, "cla": 0, "sal": 1, "est": 1}
    assert e.H == 2
    assert e.F == 2 * 1000 + 10
    assert e.S == 10
    assert e.by_level == {"superficial": 0, "medio": 2000, "profundo": 10}


def test_disponibilidad_y_capacidad(tiny, base_rules):
    ev = Evaluator(tiny, base_rules)
    # e1 (teacher l0) in time slot 3, where it is not available
    e = ev.evaluate(ind((0, 0), (3, 0), (2, 1)))
    assert dict(zip([r.nombre for r in ev.rules], e.violations))["disp"] == 1

    tiny.room_capacity = np.array([1, 30])
    tiny.event_size = tiny.class_size[tiny.event_class]
    e = Evaluator(tiny, base_rules).evaluate(ind((0, 0), (1, 1), (2, 1)))
    assert dict(zip([r.nombre for r in base_rules], e.violations))["cap"] == 1


def test_clase_duplicada_no_cuenta_como_conflicto_de_estudiante(tiny, base_rules):
    ev = Evaluator(tiny, base_rules)
    # e1 and e2 (both class c1) at t2: class conflict (HC), not student conflict (SC)
    e = ev.evaluate(ind((0, 0), (2, 0), (2, 1)))
    v = dict(zip([r.nombre for r in ev.rules], e.violations))
    assert v["cla"] == 1 and v["est"] == 0


def test_detalle_identifica_eventos(tiny, base_rules):
    ev = Evaluator(tiny, base_rules)
    det = {d["regla"].nombre: d for d in ev.detail(ind((0, 0), (0, 0), (2, 1)))}
    assert det["doc"]["eventos"] == [0, 1]
    assert det["sal"]["eventos"] == [0, 1]
    assert det["est"]["eventos"] == [0, 1]
    assert det["disp"]["eventos"] == []


def test_reglas_blandas_parametrizadas(tiny):
    rules = [Rule("sep", "SC", "eventos_clase_mismo_dia:max=1", 2),
             Rule("carga", "SC", "carga_diaria_desbalanceada", 3)]
    ev = Evaluator(tiny, rules)
    # e1 and e2 (c1) on the same day 1: 1 hour over max=1.
    # Load: l0 = [1, 1] gives std 0; l1 = [0, 1] gives std 0.5
    e = ev.evaluate(ind((0, 0), (2, 0), (3, 1)))
    assert list(e.violations) == pytest.approx([1, 0.5])
    # l0 = [2, 0] gives std 1; l1 = [0, 1] gives std 0.5
    e = ev.evaluate(ind((0, 0), (1, 0), (3, 1)))
    assert e.violations[1] == pytest.approx(1.5)


def test_preferencias_solo_si_el_docente_las_declara(tiny):
    tiny.teacher_preferred[1, 0] = True
    tiny.teacher_has_pref = tiny.teacher_preferred.any(axis=1)
    ev = Evaluator(tiny, [Rule("pref", "SC", "fuera_de_franja_preferida", 5)])
    assert ev.evaluate(ind((3, 0), (3, 0), (2, 1))).violations[0] == 1   # e2 outside
    assert ev.evaluate(ind((3, 0), (3, 0), (0, 1))).violations[0] == 0


def test_reglas_inactivas_se_ignoran(tiny, base_rules):
    base_rules[2].activa = False
    ev = Evaluator(tiny, base_rules)
    assert "doc" not in [r.nombre for r in ev.rules]


@pytest.mark.parametrize("cond", ["no_existe", "docente_no_disponible:x=1",
                                  "eventos_clase_mismo_dia:max", "eventos_clase_mismo_dia:max=a"])
def test_condiciones_invalidas(cond):
    with pytest.raises(ValueError):
        parse_condition(cond)


def test_tipo_invalido():
    with pytest.raises(ValueError):
        Rule("x", "XX", "docente_no_disponible", 1)
