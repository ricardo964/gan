"""MDGA compute core (independent of Flask and the database).

Takes a `Problem` (NumPy arrays) and a list of `Rule` objects and
produces optimized schedules. The web application and persistence plug
into it through callbacks, which keeps the MVC separation of Milestone 2.
"""
from .fitness import Evaluation, Evaluator, Rule
from .problem import Problem, utp_slots

__all__ = ["Problem", "Rule", "Evaluator", "Evaluation", "utp_slots"]
