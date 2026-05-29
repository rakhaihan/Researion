"""Documents knowledge base and research source modes

Revision ID: 004_documents_kb
Revises: 003_research_quality
Create Date: 2026-05-29

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_documents_kb"
down_revision: Union[str, None] = "003_research_quality"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

document_status_enum = postgresql.ENUM(
    "uploaded",
    "processing",
    "processed",
    "failed",
    name="document_status_enum",
    create_type=False,
)
research_source_mode_enum = postgresql.ENUM(
    "web_only",
    "documents_only",
    "hybrid",
    name="research_source_mode_enum",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    document_status_enum.create(bind, checkfirst=True)
    research_source_mode_enum.create(bind, checkfirst=True)

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.String(1000), nullable=False),
        sa.Column("status", document_status_enum, nullable=False, server_default="uploaded"),
        sa.Column("processing_step", sa.String(50), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_documents_user_id", "documents", ["user_id"])

    op.create_table(
        "document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("section_title", sa.String(500), nullable=True),
        sa.Column("embedding_id", sa.String(100), nullable=True),
        sa.Column("embedding", postgresql.JSONB(), nullable=True),
        sa.Column("chunk_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"])
    op.create_index("ix_document_chunks_user_id", "document_chunks", ["user_id"])

    op.add_column(
        "research_projects",
        sa.Column(
            "research_source_mode",
            research_source_mode_enum,
            nullable=False,
            server_default="web_only",
        ),
    )
    op.add_column(
        "research_projects",
        sa.Column("document_ids", postgresql.JSONB(), nullable=True),
    )

    op.add_column(
        "source_results",
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column(
        "source_results",
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("document_chunks.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column("source_results", sa.Column("page_number", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("source_results", "page_number")
    op.drop_column("source_results", "chunk_id")
    op.drop_column("source_results", "document_id")
    op.drop_column("research_projects", "document_ids")
    op.drop_column("research_projects", "research_source_mode")
    op.drop_index("ix_document_chunks_user_id")
    op.drop_index("ix_document_chunks_document_id")
    op.drop_table("document_chunks")
    op.drop_index("ix_documents_user_id")
    op.drop_table("documents")
    document_status_enum.drop(op.get_bind(), checkfirst=True)
    research_source_mode_enum.drop(op.get_bind(), checkfirst=True)
