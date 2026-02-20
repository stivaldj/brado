from alembic import op
import sqlalchemy as sa


revision = "002_political_interview_core"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "interview_questions",
        sa.Column("id", sa.String(length=32), primary_key=True, nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("response_type", sa.String(length=32), nullable=False),
        sa.Column("dimensions_json", sa.JSON(), nullable=False),
        sa.Column("tags_json", sa.JSON(), nullable=False),
        sa.Column("active", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_interview_questions_active", "interview_questions", ["active"], unique=False)

    op.create_table(
        "interview_sessions",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("anon_user_hash", sa.CHAR(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_interview_sessions_started_at", "interview_sessions", ["started_at"], unique=False)
    op.create_index("ix_interview_sessions_anon_user_hash", "interview_sessions", ["anon_user_hash"], unique=False)

    op.create_table(
        "interview_answers",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("session_id", sa.String(length=36), sa.ForeignKey("interview_sessions.id"), nullable=False),
        sa.Column("question_id", sa.String(length=32), sa.ForeignKey("interview_questions.id"), nullable=False),
        sa.Column("answer_value", sa.Integer(), nullable=False),
        sa.Column("answered_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("session_id", "question_id", name="uq_interview_answer_once_per_question"),
    )
    op.create_index("ix_interview_answers_session_id", "interview_answers", ["session_id"], unique=False)

    op.create_table(
        "interview_results",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("session_id", sa.String(length=36), sa.ForeignKey("interview_sessions.id"), nullable=False, unique=True),
        sa.Column("vector_json", sa.JSON(), nullable=False),
        sa.Column("left_right_score", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("consistency", sa.Float(), nullable=False),
        sa.Column("ranking_json", sa.JSON(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_interview_results_generated_at", "interview_results", ["generated_at"], unique=False)

    op.create_table(
        "legislator_profiles",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("external_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("chamber", sa.String(length=16), nullable=False),
        sa.Column("party", sa.String(length=16), nullable=False),
        sa.Column("state", sa.String(length=2), nullable=True),
        sa.Column("vector_json", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("external_id", "chamber", name="uq_legislator_profiles_external_chamber"),
    )
    op.create_index("ix_legislator_profiles_party", "legislator_profiles", ["party"], unique=False)

    op.create_table(
        "party_profiles",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("acronym", sa.String(length=16), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("vector_json", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("party_profiles")
    op.drop_index("ix_legislator_profiles_party", table_name="legislator_profiles")
    op.drop_table("legislator_profiles")
    op.drop_index("ix_interview_results_generated_at", table_name="interview_results")
    op.drop_table("interview_results")
    op.drop_index("ix_interview_answers_session_id", table_name="interview_answers")
    op.drop_table("interview_answers")
    op.drop_index("ix_interview_sessions_anon_user_hash", table_name="interview_sessions")
    op.drop_index("ix_interview_sessions_started_at", table_name="interview_sessions")
    op.drop_table("interview_sessions")
    op.drop_index("ix_interview_questions_active", table_name="interview_questions")
    op.drop_table("interview_questions")
