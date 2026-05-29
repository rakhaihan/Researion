"""Add research quality evaluation

Revision ID: 003_research_quality
Revises: 002_backfill_default_dev_user
Create Date: 2026-05-29

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_research_quality"
down_revision: Union[str, None] = "002_backfill_default_dev_user"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

quality_status_enum = postgresql.ENUM(
    "passed",
    "warning",
    "failed",
    name="quality_status_enum",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    quality_status_enum.create(bind, checkfirst=True)

    op.add_column(
        "research_projects",
        sa.Column("quality_status", quality_status_enum, nullable=True),
    )
    op.add_column(
        "research_projects",
        sa.Column("quality_score", sa.Float(), nullable=True),
    )

    op.create_table(
        "research_quality_evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "research_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_projects.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("citation_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("source_diversity_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("source_credibility_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("freshness_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("completeness_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("overall_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("quality_status", quality_status_enum, nullable=False, server_default="warning"),
        sa.Column("warnings", postgresql.JSONB(), nullable=True),
        sa.Column("recommendations", postgresql.JSONB(), nullable=True),
        sa.Column("citation_validation", postgresql.JSONB(), nullable=True),
        sa.Column("claim_check", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_research_quality_evaluations_research_id",
        "research_quality_evaluations",
        ["research_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_research_quality_evaluations_research_id")
    op.drop_table("research_quality_evaluations")
    op.drop_column("research_projects", "quality_score")
    op.drop_column("research_projects", "quality_status")
    quality_status_enum.drop(op.get_bind(), checkfirst=True)
