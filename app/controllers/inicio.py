"""Home panel: state of the fact base and the latest run."""
from flask import Blueprint, render_template

from ..models import repo

bp = Blueprint("inicio", __name__)


@bp.get("/")
def index():
    runs = repo.list_runs(1)
    return render_template("index.html", c=repo.counts(), ultima=runs[0] if runs else None)
