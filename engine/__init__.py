"""Núcleo de cómputo MDGA (independiente de Flask y de la BD).

Recibe un `Problem` (arreglos NumPy) y una lista de `Rule`, y produce
horarios optimizados. La aplicación web y la persistencia se conectan a
él mediante callbacks, lo que mantiene la separación MVC del Hito 2.
"""
from .fitness import Evaluation, Evaluator, Rule
from .problem import Problem, utp_slots

__all__ = ["Problem", "Rule", "Evaluator", "Evaluation", "utp_slots"]
