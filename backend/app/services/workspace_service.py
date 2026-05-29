from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, Workspace, WorkspaceMember, WorkspaceRole
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceMemberCreate,
    WorkspaceMemberResponse,
    WorkspaceMemberUpdate,
    WorkspaceResponse,
    WorkspaceUpdate,
)
from app.services.permission_service import PermissionService
from app.services.user_service import UserService


class WorkspaceService:
    def __init__(self) -> None:
        self.permissions = PermissionService()
        self.user_service = UserService()

    async def ensure_default_workspace(self, db: AsyncSession, user: User) -> Workspace:
        result = await db.execute(
            select(Workspace).where(Workspace.owner_id == user.id, Workspace.is_default.is_(True))
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        workspace = Workspace(
            owner_id=user.id,
            name=f"{user.full_name}'s Workspace",
            is_default=True,
        )
        db.add(workspace)
        await db.flush()
        member = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=user.id,
            role=WorkspaceRole.OWNER,
        )
        db.add(member)
        await db.flush()
        await db.refresh(workspace)
        return workspace

    async def get_default_workspace_id(self, db: AsyncSession, user_id: UUID) -> UUID:
        result = await db.execute(
            select(Workspace).where(Workspace.owner_id == user_id, Workspace.is_default.is_(True))
        )
        workspace = result.scalar_one_or_none()
        if workspace is None:
            user = await self.user_service.get_by_id(db, user_id)
            if user is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
            workspace = await self.ensure_default_workspace(db, user)
        return workspace.id

    async def create_workspace(
        self, db: AsyncSession, user_id: UUID, payload: WorkspaceCreate
    ) -> WorkspaceResponse:
        workspace = Workspace(
            owner_id=user_id,
            name=payload.name.strip(),
            description=payload.description,
            is_default=False,
        )
        db.add(workspace)
        await db.flush()
        db.add(
            WorkspaceMember(
                workspace_id=workspace.id,
                user_id=user_id,
                role=WorkspaceRole.OWNER,
            )
        )
        await db.flush()
        await db.refresh(workspace)
        return self._to_response(workspace, WorkspaceRole.OWNER)

    async def list_workspaces(self, db: AsyncSession, user_id: UUID) -> list[WorkspaceResponse]:
        ws_ids = await self.permissions.accessible_workspace_ids(db, user_id)
        if not ws_ids:
            return []
        result = await db.execute(select(Workspace).where(Workspace.id.in_(ws_ids)))
        workspaces = list(result.scalars().all())
        responses: list[WorkspaceResponse] = []
        for ws in workspaces:
            role = await self.permissions.get_role(db, ws.id, user_id)
            responses.append(self._to_response(ws, role))
        return sorted(responses, key=lambda w: (not w.is_default, w.name.lower()))

    async def get_workspace(
        self, db: AsyncSession, workspace_id: UUID, user_id: UUID
    ) -> WorkspaceResponse:
        workspace = await self._get_workspace(db, workspace_id)
        if not await self.permissions.can_view_workspace(db, workspace_id, user_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Workspace not found")
        role = await self.permissions.get_role(db, workspace_id, user_id)
        return self._to_response(workspace, role)

    async def update_workspace(
        self,
        db: AsyncSession,
        workspace_id: UUID,
        user_id: UUID,
        payload: WorkspaceUpdate,
    ) -> WorkspaceResponse:
        workspace = await self._get_workspace(db, workspace_id)
        await self.permissions.require_workspace_role(
            db, workspace_id, user_id, WorkspaceRole.ADMIN
        )
        if payload.name is not None:
            workspace.name = payload.name.strip()
        if payload.description is not None:
            workspace.description = payload.description
        await db.flush()
        await db.refresh(workspace)
        role = await self.permissions.get_role(db, workspace_id, user_id)
        return self._to_response(workspace, role)

    async def delete_workspace(
        self, db: AsyncSession, workspace_id: UUID, user_id: UUID
    ) -> None:
        workspace = await self._get_workspace(db, workspace_id)
        if workspace.owner_id != user_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Only owner can delete workspace")
        if workspace.is_default:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete default workspace",
            )
        await db.delete(workspace)
        await db.flush()

    async def list_members(
        self, db: AsyncSession, workspace_id: UUID, user_id: UUID
    ) -> list[WorkspaceMemberResponse]:
        if not await self.permissions.can_view_workspace(db, workspace_id, user_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Workspace not found")
        result = await db.execute(
            select(WorkspaceMember, User)
            .join(User, User.id == WorkspaceMember.user_id)
            .where(WorkspaceMember.workspace_id == workspace_id)
        )
        return [
            WorkspaceMemberResponse(
                id=member.id,
                workspace_id=member.workspace_id,
                user_id=member.user_id,
                role=member.role,
                email=user.email,
                full_name=user.full_name,
                created_at=member.created_at,
            )
            for member, user in result.all()
        ]

    async def add_member(
        self,
        db: AsyncSession,
        workspace_id: UUID,
        user_id: UUID,
        payload: WorkspaceMemberCreate,
    ) -> WorkspaceMemberResponse:
        await self.permissions.require_workspace_role(
            db, workspace_id, user_id, WorkspaceRole.ADMIN
        )
        if payload.role == WorkspaceRole.OWNER:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Cannot assign owner role")
        invitee = await self.user_service.get_by_email(db, payload.email)
        if invitee is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
        existing = await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == invitee.id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status.HTTP_409_CONFLICT, detail="User is already a member")
        member = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=invitee.id,
            role=WorkspaceRole(payload.role.value),
        )
        db.add(member)
        await db.flush()
        await db.refresh(member)
        return WorkspaceMemberResponse(
            id=member.id,
            workspace_id=member.workspace_id,
            user_id=member.user_id,
            role=member.role,
            email=invitee.email,
            full_name=invitee.full_name,
            created_at=member.created_at,
        )

    async def update_member(
        self,
        db: AsyncSession,
        workspace_id: UUID,
        member_id: UUID,
        user_id: UUID,
        payload: WorkspaceMemberUpdate,
    ) -> WorkspaceMemberResponse:
        await self.permissions.require_workspace_role(
            db, workspace_id, user_id, WorkspaceRole.ADMIN
        )
        if payload.role == WorkspaceRole.OWNER:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Cannot assign owner role")
        member = await self._get_member(db, workspace_id, member_id)
        if member.role == WorkspaceRole.OWNER:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Cannot change owner role")
        member.role = WorkspaceRole(payload.role.value)
        await db.flush()
        user = await self.user_service.get_by_id(db, member.user_id)
        return WorkspaceMemberResponse(
            id=member.id,
            workspace_id=member.workspace_id,
            user_id=member.user_id,
            role=member.role,
            email=user.email if user else None,
            full_name=user.full_name if user else None,
            created_at=member.created_at,
        )

    async def remove_member(
        self,
        db: AsyncSession,
        workspace_id: UUID,
        member_id: UUID,
        user_id: UUID,
    ) -> None:
        await self.permissions.require_workspace_role(
            db, workspace_id, user_id, WorkspaceRole.ADMIN
        )
        member = await self._get_member(db, workspace_id, member_id)
        if member.role == WorkspaceRole.OWNER:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Cannot remove workspace owner")
        await db.delete(member)
        await db.flush()

    async def _get_workspace(self, db: AsyncSession, workspace_id: UUID) -> Workspace:
        result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
        workspace = result.scalar_one_or_none()
        if workspace is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Workspace not found")
        return workspace

    async def _get_member(
        self, db: AsyncSession, workspace_id: UUID, member_id: UUID
    ) -> WorkspaceMember:
        result = await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.id == member_id,
                WorkspaceMember.workspace_id == workspace_id,
            )
        )
        member = result.scalar_one_or_none()
        if member is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Member not found")
        return member

    @staticmethod
    def _to_response(workspace: Workspace, role: WorkspaceRole | None) -> WorkspaceResponse:
        return WorkspaceResponse(
            id=workspace.id,
            owner_id=workspace.owner_id,
            name=workspace.name,
            description=workspace.description,
            is_default=workspace.is_default,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at,
            role=role,
        )
