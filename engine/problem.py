"""Formal problem model (Milestone 2, sections 3.1 and 3.2).

- Package   q = (t, r): time slot and room (variable genes).
- Event     e = (l, c, S): teacher, class and students (fixed fields).
- Schedule  P = {(q, e)}: one package per event.

The chromosome of an individual is an integer array of shape (E, 2)
where column 0 is t (0..T-1) and column 1 is r (0..R-1). A population is
an (N, E, 2) array. The fixed fields l, c and S live in `Problem` and are
never modified by the genetic operators.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

T_COL, R_COL = 0, 1


@dataclass
class Problem:
    """Problem instance with dense (0-based) indices ready for NumPy."""

    # Time domain
    n_slots: int                    # T (60 at UTP)
    slot_day: np.ndarray            # (T,) day 0..D-1 of each time slot
    # Rooms
    room_capacity: np.ndarray       # (R,) capacity
    # Events (fixed fields l, c, S)
    event_teacher: np.ndarray       # (E,) teacher index l
    event_class: np.ndarray         # (E,) class/group index c
    class_students: np.ndarray      # (C, St) bool: S of each class
    # Teachers
    teacher_available: np.ndarray   # (L, T) bool
    teacher_preferred: np.ndarray   # (L, T) bool (no preferences = all False)
    # Labels for explanations and persistence (database ids / codes)
    slot_ids: list = field(default_factory=list)
    slot_labels: list = field(default_factory=list)     # e.g. "Lun 07:00"
    room_ids: list = field(default_factory=list)
    room_codes: list = field(default_factory=list)
    teacher_codes: list = field(default_factory=list)
    class_codes: list = field(default_factory=list)
    event_ids: list = field(default_factory=list)

    def __post_init__(self):
        self.slot_day = np.asarray(self.slot_day, dtype=np.int64)
        self.room_capacity = np.asarray(self.room_capacity, dtype=np.int64)
        self.event_teacher = np.asarray(self.event_teacher, dtype=np.int64)
        self.event_class = np.asarray(self.event_class, dtype=np.int64)
        self.class_students = np.asarray(self.class_students, dtype=bool)
        self.teacher_available = np.asarray(self.teacher_available, dtype=bool)
        self.teacher_preferred = np.asarray(self.teacher_preferred, dtype=bool)
        self.validate()
        # Derived
        self.class_size = self.class_students.sum(axis=1).astype(np.int64)
        self.event_size = self.class_size[self.event_class]          # |S| per event
        self.teacher_has_pref = self.teacher_preferred.any(axis=1)

    # Dimensions
    @property
    def n_events(self) -> int:
        return int(self.event_teacher.shape[0])

    @property
    def n_rooms(self) -> int:
        return int(self.room_capacity.shape[0])

    @property
    def n_teachers(self) -> int:
        return int(self.teacher_available.shape[0])

    @property
    def n_classes(self) -> int:
        return int(self.class_students.shape[0])

    @property
    def n_students(self) -> int:
        return int(self.class_students.shape[1])

    @property
    def n_days(self) -> int:
        return int(self.slot_day.max()) + 1 if self.slot_day.size else 0

    # Validation
    def validate(self) -> None:
        T = self.n_slots
        if self.slot_day.shape != (T,):
            raise ValueError("slot_day debe tener una entrada por franja")
        if self.event_teacher.shape != self.event_class.shape:
            raise ValueError("event_teacher y event_class deben tener la misma longitud")
        if self.n_events == 0:
            raise ValueError("el problema no tiene eventos")
        if self.n_rooms == 0:
            raise ValueError("el problema no tiene salas")
        if (self.room_capacity <= 0).any():
            raise ValueError("toda sala debe tener capacidad positiva")
        if self.teacher_available.shape[1] != T or self.teacher_preferred.shape[1] != T:
            raise ValueError("disponibilidad/preferencia docente debe ser (L, T)")
        if self.event_teacher.max() >= self.teacher_available.shape[0]:
            raise ValueError("evento con docente fuera de rango")
        if self.event_class.max() >= self.class_students.shape[0]:
            raise ValueError("evento con clase fuera de rango")

    # Chromosome
    def random_individual(self, rng: np.random.Generator) -> np.ndarray:
        """Random individual: t ~ U{0..T-1}, r ~ U{0..R-1} per event."""
        ind = np.empty((self.n_events, 2), dtype=np.int64)
        ind[:, T_COL] = rng.integers(0, self.n_slots, self.n_events)
        ind[:, R_COL] = rng.integers(0, self.n_rooms, self.n_events)
        return ind

    def random_population(self, n: int, rng: np.random.Generator) -> np.ndarray:
        pop = np.empty((n, self.n_events, 2), dtype=np.int64)
        pop[:, :, T_COL] = rng.integers(0, self.n_slots, (n, self.n_events))
        pop[:, :, R_COL] = rng.integers(0, self.n_rooms, (n, self.n_events))
        return pop

    def is_valid_individual(self, ind: np.ndarray) -> bool:
        return (
            ind.shape == (self.n_events, 2)
            and (ind[:, T_COL] >= 0).all() and (ind[:, T_COL] < self.n_slots).all()
            and (ind[:, R_COL] >= 0).all() and (ind[:, R_COL] < self.n_rooms).all()
        )


def utp_slots(days: int = 6, per_day: int = 10) -> np.ndarray:
    """Default UTP discretization: 60 time slots, 10 per day from Monday to Saturday."""
    return np.repeat(np.arange(days), per_day)
