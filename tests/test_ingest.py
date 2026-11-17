from pathlib import Path

from ingest import read_files, validate

DATA = Path(__file__).resolve().parents[1] / "datos" / "ejemplo_utp.xlsx"


def base():
    return {
        "salones": [{"codigo": "A1", "capacidad": "30"}],
        "docentes": [{"codigo": "D1", "nombre": "Ana"}],
        "materias": [{"codigo": "M1", "nombre": "IA", "horas_semanales": "3"}],
        "grupos": [{"codigo": "G1", "materia": "M1", "docente": "D1"}],
        "inscripciones": [{"grupo": "G1", "estudiante": "E1"}],
    }


def test_datos_validos():
    rep = validate(base())
    assert rep.ok, rep.errors
    assert rep.tables["salones"][0]["capacidad"] == 30


def test_xlsx_de_ejemplo_es_valido():
    tables, errors = read_files([(DATA.name, DATA.read_bytes())])
    assert not errors
    rep = validate(tables)
    assert rep.ok, rep.errors
    assert rep.summary()["grupos"] == 30


def test_csv_con_punto_y_coma():
    tables, errors = read_files([("salones.csv", b"codigo;capacidad\nA1;30\nA2;40\n")])
    assert not errors and len(tables["salones"]) == 2


def test_errores_de_tipo_referencia_y_unicidad():
    d = base()
    d["salones"].append({"codigo": "A1", "capacidad": "-5"})
    d["materias"][0]["horas_semanales"] = "2.5"
    d["grupos"].append({"codigo": "G2", "materia": "MX", "docente": "D9"})
    rep = validate(d)
    msgs = " | ".join(rep.errors)
    assert "debe ser entero" in msgs
    d["materias"][0]["horas_semanales"] = "3"
    msgs = " | ".join(validate(d).errors)
    assert "duplicado" in msgs and "capacidad debe ser positiva" in msgs
    assert "materia 'MX' no existe" in msgs and "docente 'D9' no existe" in msgs


def test_falta_entidad_y_formato():
    d = base()
    del d["grupos"]
    assert "falta la entidad 'grupos'" in validate(d).errors
    _, errors = read_files([("x.txt", b"")])
    assert errors


def test_coherencia_global():
    d = base()
    d["materias"][0]["horas_semanales"] = "61"
    rep = validate(d)
    assert any("infactible" in e for e in rep.errors)
    d = base()
    d["inscripciones"] = [{"grupo": "G1", "estudiante": f"E{i}"} for i in range(40)]
    assert any("no cabe" in w for w in validate(d).warnings)
