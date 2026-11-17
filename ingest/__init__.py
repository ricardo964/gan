"""Automatic data ingestion pipelines (Milestone 2, Table 8 and Table 14)."""
from .pipeline import SCHEMA, IngestReport, read_csv, read_files, read_xlsx, validate

__all__ = ["SCHEMA", "IngestReport", "read_csv", "read_files", "read_xlsx", "validate"]
