import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine import Problem, Rule  # noqa: E402


@pytest.fixture
def tiny():
    """4 franjas (2 días), 2 salas, 2 docentes, 2 clases, 3 estudiantes.

    c0 = {s0, s1}, c1 = {s1, s2}; e0=(l0,c0), e1=(l0,c1), e2=(l1,c1).
    El docente l0 no está disponible en la franja 3.
    """
    avail = np.ones((2, 4), dtype=bool)
    avail[0, 3] = False
    return Problem(
        n_slots=4,
        slot_day=[0, 0, 1, 1],
        room_capacity=[10, 30],
        event_teacher=[0, 0, 1],
        event_class=[0, 1, 1],
        class_students=[[1, 1, 0], [0, 1, 1]],
        teacher_available=avail,
        teacher_preferred=np.zeros((2, 4), dtype=bool),
    )


@pytest.fixture
def base_rules():
    return [
        Rule("disp", "HC", "docente_no_disponible", 1000),
        Rule("cap", "HC", "estudiantes_excede_capacidad", 1000),
        Rule("doc", "HC", "docente_dos_eventos_misma_franja", 1000),
        Rule("cla", "HC", "clase_dos_eventos_misma_franja", 1000),
        Rule("sal", "HC", "sala_dos_eventos_misma_franja", 1000),
        Rule("est", "SC", "estudiante_dos_eventos_misma_franja", 10),
    ]
