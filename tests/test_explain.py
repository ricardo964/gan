import numpy as np

from engine import Evaluator
from explain import compare, explain


def test_explicacion_desglosa_F(tiny, base_rules):
    ev = Evaluator(tiny, base_rules)
    ind = np.array([(0, 0), (0, 0), (2, 1)])
    exp = explain(ev, ind)
    assert exp["F"] == sum(r["penalizacion"] for r in exp["reglas"])
    assert exp["H"] == 2 and not exp["factible"]
    top = exp["reglas"][0]
    assert top["penalizacion"] == 1000 and top["n_eventos"] == 2
    assert {e["evento"] for e in top["eventos"]} == {0, 1}
    assert exp["cobertura"] == 1.0


def test_horario_sin_violaciones(tiny, base_rules):
    exp = explain(Evaluator(tiny, base_rules), np.array([(0, 0), (1, 0), (2, 1)]))
    assert exp["F"] == 0 and exp["factible"] and exp["cobertura"] == 1.0


def test_comparar_k_mejores(tiny, base_rules):
    ev = Evaluator(tiny, base_rules)
    a = explain(ev, np.array([(0, 0), (0, 0), (2, 1)]))
    b = explain(ev, np.array([(0, 0), (1, 0), (2, 1)]))
    rows = {r["regla"]: r["valores"] for r in compare([a, b])}
    assert rows["doc"][0]["V"] == 1 and rows["doc"][1]["V"] == 0
