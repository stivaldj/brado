from alembic import op
import sqlalchemy as sa


revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "anchors",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("anchor_type", sa.String(length=64), nullable=False),
        sa.Column("entry_type", sa.String(length=255), nullable=False),
        sa.Column("root", sa.CHAR(length=64), nullable=False),
        sa.Column("anchored_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("provider_payload", sa.JSON(), nullable=False),
    )

    op.create_table(
        "ingestion_batches",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("batch_type", sa.String(length=128), nullable=False),
        sa.Column("range_start", sa.Date(), nullable=True),
        sa.Column("range_end", sa.Date(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("item_count", sa.Integer(), nullable=False),
        sa.Column("merkle_root", sa.CHAR(length=64), nullable=True),
        sa.Column("anchor_id", sa.String(length=36), sa.ForeignKey("anchors.id"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_ingestion_batch_type_started", "ingestion_batches", ["batch_type", "started_at"], unique=False)

    op.create_table(
        "raw_payloads",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("endpoint", sa.String(length=255), nullable=False),
        sa.Column("params_json", sa.JSON(), nullable=False),
        sa.Column("primary_key", sa.String(length=255), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("sha256", sa.CHAR(length=64), nullable=False),
        sa.Column("body_json", sa.JSON(), nullable=False),
        sa.Column("batch_id", sa.String(length=36), sa.ForeignKey("ingestion_batches.id"), nullable=False),
        sa.UniqueConstraint("source", "endpoint", "primary_key", "fetched_at", name="uq_raw_payload_version"),
    )
    op.create_index("ix_raw_payload_source_endpoint", "raw_payloads", ["source", "endpoint"], unique=False)
    op.create_index("ix_raw_payload_batch_id", "raw_payloads", ["batch_id"], unique=False)
    op.create_index("ix_raw_payload_fetched_at", "raw_payloads", ["fetched_at"], unique=False)

    op.create_table(
        "batch_items",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("batch_id", sa.String(length=36), sa.ForeignKey("ingestion_batches.id"), nullable=False),
        sa.Column("raw_payload_id", sa.String(length=36), sa.ForeignKey("raw_payloads.id"), nullable=False),
        sa.Column("item_sha256", sa.CHAR(length=64), nullable=False),
        sa.Column("leaf_index", sa.Integer(), nullable=False),
        sa.UniqueConstraint("batch_id", "raw_payload_id", name="uq_batch_raw_payload"),
    )
    op.create_index("ix_batch_items_batch_leaf", "batch_items", ["batch_id", "leaf_index"], unique=False)

    op.create_table(
        "job_state",
        sa.Column("job_name", sa.String(length=128), primary_key=True, nullable=False),
        sa.Column("cursor_json", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
    )

    op.create_table(
        "reconcile_reports",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("run_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("report_json", sa.JSON(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("reconcile_reports")
    op.drop_table("job_state")
    op.drop_index("ix_batch_items_batch_leaf", table_name="batch_items")
    op.drop_table("batch_items")
    op.drop_index("ix_raw_payload_fetched_at", table_name="raw_payloads")
    op.drop_index("ix_raw_payload_batch_id", table_name="raw_payloads")
    op.drop_index("ix_raw_payload_source_endpoint", table_name="raw_payloads")
    op.drop_table("raw_payloads")
    op.drop_index("ix_ingestion_batch_type_started", table_name="ingestion_batches")
    op.drop_table("ingestion_batches")
    op.drop_table("anchors")
