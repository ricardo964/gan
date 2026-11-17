"""Pipelines de ingesta automática de datos (Hito 2, Tabla 8 y Tabla 14)."""
from .pipeline import SCHEMA, IngestReport, read_csv, read_files, read_xlsx, validate

__all__ = ["SCHEMA", "IngestReport", "read_csv", "read_files", "read_xlsx", "validate"]
