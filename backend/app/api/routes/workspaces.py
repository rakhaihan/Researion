from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, resolve_current_user
from app.db.models import User
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceMemberCreate,
    WorkspaceMemberResponse,
    WorkspaceMemberUpdate,
    WorkspaceResponse,
    WorkspaceUpdate,
)
from app.services.workspace_service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


def get_workspace_service() -> WorkspaceService:
    return WorkspaceService()


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    payload: WorkspaceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(resolve_current_user),
    service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceResponse:
    return await service.create_workspace(db, current_user.id, payload)


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(resolve_current_user),
    service: WorkspaceService = Depends(get_workspace_service),
) -> list[WorkspaceResponse]:
    return await service.list_workspaces(db, current_user.id)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(resolve_current_user),
    service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceResponse:
    return await service.get_workspace(db, workspace_id, current_user.id)


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: UUID,
    payload: WorkspaceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(resolve_current_user),
    service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceResponse:
    return await service.update_workspace(db, workspace_id, current_user.id, payload)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(resolve_current_user),
    service: WorkspaceService = Depends(get_workspace_service),
) -> None:
    await service.delete_workspace(db, workspace_id, current_user.id)


@router.get("/{workspace_id}/members", response_model=list[WorkspaceMemberResponse])
async def list_members(
    workspace_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(resolve_current_user),
    service: WorkspaceService = Depends(get_workspace_service),
) -> list[WorkspaceMemberResponse]:
    return await service.list_members(db, workspace_id, current_user.id)


@router.post(
    "/{workspace_id}/members",
    response_model=WorkspaceMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_member(
    workspace_id: UUID,
    payload: WorkspaceMemberCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(resolve_current_user),
    service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceMemberResponse:
    return await service.add_member(db, workspace_id, current_user.id, payload)


@router.patch(
    "/{workspace_id}/members/{member_id}",
    response_model=WorkspaceMemberResponse,
)
async def update_member(
    workspace_id: UUID,
    member_id: UUID,
    payload: WorkspaceMemberUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(resolve_current_user),
    service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceMemberResponse:
    return await service.update_member(
        db, workspace_id, member_id, current_user.id, payload
    )


@router.delete("/{workspace_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    workspace_id: UUID,
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(resolve_current_user),
    service: WorkspaceService = Depends(get_workspace_service),
) -> None:
    await service.remove_member(db, workspace_id, member_id, current_user.id)
