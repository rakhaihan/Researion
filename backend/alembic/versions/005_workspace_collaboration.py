"""Workspace collaboration, sharing, versions, comments

Revision ID: 005_workspace_collab
Revises: 004_documents_kb
Create Date: 2026-05-29

"""

from typing import Sequence, Union
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005_workspace_collab"
down_revision: Union[str, None] = "004_documents_kb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

workspace_role_enum = postgresql.ENUM(
    "owner", "admin", "editor", "viewer", name="workspace_role_enum", create_type=False
)
share_visibility_enum = postgresql.ENUM(
    "private", "public", name="share_visibility_enum", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    workspace_role_enum.create(bind, checkfirst=True)
    share_visibility_enum.create(bind, checkfirst=True)

    op.create_table(
        "workspaces",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_workspaces_owner_id", "workspaces", ["owner_id"])

    op.create_table(
        "workspace_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", workspace_role_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member"),
    )
    op.create_index("ix_workspace_members_workspace_id", "workspace_members", ["workspace_id"])
    op.create_index("ix_workspace_members_user_id", "workspace_members", ["user_id"])

    op.add_column(
        "research_projects",
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "research_projects",
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "research_projects",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_research_projects_workspace_id",
        "research_projects",
        "workspaces",
        ["workspace_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_research_projects_workspace_id", "research_projects", ["workspace_id"])

    op.create_table(
        "report_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("research_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("markdown_content", sa.Text(), nullable=False),
        sa.Column("executive_summary", sa.Text(), nullable=False),
        sa.Column("detailed_analysis", sa.Text(), nullable=False),
        sa.Column("key_findings", postgresql.JSONB(), nullable=True),
        sa.Column("risks", postgresql.JSONB(), nullable=True),
        sa.Column("conclusion", sa.Text(), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column(
            "quality_status",
            postgresql.ENUM("passed", "warning", "failed", name="quality_status_enum", create_type=False),
            nullable=True,
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("change_reason", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["research_id"], ["research_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("research_id", "version_number", name="uq_report_version_number"),
    )

    op.create_table(
        "shared_report_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("research_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token", sa.String(128), nullable=False),
        sa.Column("visibility", share_visibility_enum, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("allow_download", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["research_id"], ["research_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_shared_report_links_token", "shared_report_links", ["token"], unique=True)

    op.create_table(
        "research_comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("research_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("anchor_type", sa.String(50), nullable=True),
        sa.Column("anchor_ref", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["research_id"], ["research_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["research_comments.id"], ondelete="CASCADE"),
    )

    # Backfill default workspace per user and assign research
    conn = op.get_bind()
    users = conn.execute(sa.text("SELECT id, full_name FROM users")).fetchall()
    for user_id, full_name in users:
        ws_id = uuid.uuid4()
        conn.execute(
            sa.text(
                """
                INSERT INTO workspaces (id, owner_id, name, description, is_default, created_at, updated_at)
                VALUES (:id, :owner_id, :name, NULL, true, NOW(), NOW())
                """
            ),
            {"id": ws_id, "owner_id": user_id, "name": f"{full_name}'s Workspace"},
        )
        conn.execute(
            sa.text(
                """
                INSERT INTO workspace_members (id, workspace_id, user_id, role, created_at)
                VALUES (:id, :workspace_id, :user_id, 'owner', NOW())
                """
            ),
            {"id": uuid.uuid4(), "workspace_id": ws_id, "user_id": user_id},
        )
        conn.execute(
            sa.text(
                "UPDATE research_projects SET workspace_id = :ws_id WHERE user_id = :user_id"
            ),
            {"ws_id": ws_id, "user_id": user_id},
        )


def downgrade() -> None:
    op.drop_table("research_comments")
    op.drop_table("shared_report_links")
    op.drop_table("report_versions")
    op.drop_constraint("fk_research_projects_workspace_id", "research_projects", type_="foreignkey")
    op.drop_index("ix_research_projects_workspace_id", table_name="research_projects")
    op.drop_column("research_projects", "archived_at")
    op.drop_column("research_projects", "is_pinned")
    op.drop_column("research_projects", "workspace_id")
    op.drop_table("workspace_members")
    op.drop_table("workspaces")
    share_visibility_enum.drop(op.get_bind(), checkfirst=True)
    workspace_role_enum.drop(op.get_bind(), checkfirst=True)
