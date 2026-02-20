import pytest

pytest.importorskip("sqlalchemy")

from app.db.sql import Base


@pytest.mark.integration
def test_expected_tables_present() -> None:
    table_names = set(Base.metadata.tables.keys())
    assert "raw_payloads" in table_names
    assert "ingestion_batches" in table_names
    assert "batch_items" in table_names
    assert "anchors" in table_names
    assert "job_state" in table_names
    assert "reconcile_reports" in table_names
