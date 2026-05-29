from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ResearchProject, Workspace, WorkspaceMember, WorkspaceRole

ROLE_RANK = {
    WorkspaceRole.VIEWER: 1,
    WorkspaceRole.EDITOR: 2,
    WorkspaceRole.ADMIN: 3,
    WorkspaceRole.OWNER: 4,
}


class PermissionService:
    async def get_membership(
        self,
        db: AsyncSession,
        workspace_id: UUID,
        user_id: UUID,
    ) -> WorkspaceMember | None:
        if await self._is_workspace_owner(db, workspace_id, user_id):
            result = await db.execute(
                select(WorkspaceMember).where(
                    WorkspaceMember.workspace_id == workspace_id,
                    WorkspaceMember.user_id == user_id,
                )
            )
            member = result.scalar_one_or_none()
            if member:
                return member
            return WorkspaceMember(
                workspace_id=workspace_id,
                user_id=user_id,
                role=WorkspaceRole.OWNER,
            )
        result = await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_role(
        self,
        db: AsyncSession,
        workspace_id: UUID,
        user_id: UUID,
    ) -> WorkspaceRole | None:
        member = await self.get_membership(db, workspace_id, user_id)
        return member.role if member else None

    async def can_view_workspace(
        self, db: AsyncSession, workspace_id: UUID, user_id: UUID
    ) -> bool:
        return (await self.get_role(db, workspace_id, user_id)) is not None

    async def can_manage_workspace(
        self, db: AsyncSession, workspace_id: UUID, user_id: UUID
    ) -> bool:
        role = await self.get_role(db, workspace_id, user_id)
        return role in {WorkspaceRole.OWNER, WorkspaceRole.ADMIN}

    async def can_create_research(
        self, db: AsyncSession, workspace_id: UUID, user_id: UUID
    ) -> bool:
        role = await self.get_role(db, workspace_id, user_id)
        return role in {WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.EDITOR}

    async def can_edit_research(
        self, db: AsyncSession, project: ResearchProject, user_id: UUID
    ) -> bool:
        if project.workspace_id is None:
            return project.user_id == user_id
        return await self.can_create_research(db, project.workspace_id, user_id)

    async def can_run_research(
        self, db: AsyncSession, project: ResearchProject, user_id: UUID
    ) -> bool:
        return await self.can_edit_research(db, project, user_id)

    async def can_view_research(
        self, db: AsyncSession, project: ResearchProject, user_id: UUID
    ) -> bool:
        if project.user_id == user_id:
            return True
        if project.workspace_id is None:
            return False
        return await self.can_view_workspace(db, project.workspace_id, user_id)

    async def can_share_research(
        self, db: AsyncSession, project: ResearchProject, user_id: UUID
    ) -> bool:
        if project.user_id == user_id:
            return True
        if project.workspace_id is None:
            return False
        role = await self.get_role(db, project.workspace_id, user_id)
        return role in {WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.EDITOR}

    async def can_comment_research(
        self, db: AsyncSession, project: ResearchProject, user_id: UUID
    ) -> bool:
        return await self.can_view_research(db, project, user_id)

    async def can_manage_comment(
        self,
        db: AsyncSession,
        project: ResearchProject,
        user_id: UUID,
        comment_user_id: UUID,
    ) -> bool:
        if comment_user_id == user_id:
            return True
        if project.workspace_id and await self.can_manage_workspace(
            db, project.workspace_id, user_id
        ):
            return True
        return False

    async def require_workspace_role(
        self,
        db: AsyncSession,
        workspace_id: UUID,
        user_id: UUID,
        minimum: WorkspaceRole,
    ) -> WorkspaceRole:
        role = await self.get_role(db, workspace_id, user_id)
        if role is None or ROLE_RANK[role] < ROLE_RANK[minimum]:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return role

    async def require_view_research(
        self,
        db: AsyncSession,
        project: ResearchProject,
        user_id: UUID,
    ) -> None:
        if not await self.can_view_research(db, project, user_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Research project not found")

    async def require_run_research(
        self,
        db: AsyncSession,
        project: ResearchProject,
        user_id: UUID,
    ) -> None:
        if not await self.can_run_research(db, project, user_id):
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Cannot run this research")

    async def accessible_workspace_ids(
        self, db: AsyncSession, user_id: UUID
    ) -> list[UUID]:
        owned = await db.execute(select(Workspace.id).where(Workspace.owner_id == user_id))
        member = await db.execute(
            select(WorkspaceMember.workspace_id).where(WorkspaceMember.user_id == user_id)
        )
        ids = {row[0] for row in owned.all()} | {row[0] for row in member.all()}
        return list(ids)

    async def _is_workspace_owner(
        self, db: AsyncSession, workspace_id: UUID, user_id: UUID
    ) -> bool:
        result = await db.execute(
            select(Workspace).where(Workspace.id == workspace_id, Workspace.owner_id == user_id)
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    def research_access_filter(user_id: UUID, workspace_ids: list[UUID]):
        clauses = [ResearchProject.user_id == user_id]
        if workspace_ids:
            clauses.append(ResearchProject.workspace_id.in_(workspace_ids))
        return or_(*clauses)
