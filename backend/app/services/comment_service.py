from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ResearchComment, ResearchProject, User
from app.schemas.comment import CommentCreate, CommentResponse, CommentUpdate
from app.services.permission_service import PermissionService


class CommentService:
    def __init__(self) -> None:
        self.permissions = PermissionService()

    async def list_comments(
        self, db: AsyncSession, research_id: UUID, user_id: UUID
    ) -> list[CommentResponse]:
        project = await self._get_project(db, research_id)
        await self.permissions.require_view_research(db, project, user_id)
        result = await db.execute(
            select(ResearchComment, User)
            .join(User, User.id == ResearchComment.user_id)
            .where(
                ResearchComment.research_id == research_id,
                ResearchComment.deleted_at.is_(None),
                ResearchComment.parent_id.is_(None),
            )
            .order_by(ResearchComment.created_at.asc())
        )
        comments: list[CommentResponse] = []
        for comment, user in result.all():
            replies = await self._load_replies(db, comment.id)
            comments.append(self._to_response(comment, user, replies))
        return comments

    async def create_comment(
        self,
        db: AsyncSession,
        research_id: UUID,
        user_id: UUID,
        payload: CommentCreate,
    ) -> CommentResponse:
        project = await self._get_project(db, research_id)
        if not await self.permissions.can_comment_research(db, project, user_id):
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Cannot comment")
        if payload.parent_id:
            parent = await self._get_comment(db, payload.parent_id)
            if parent.research_id != research_id:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid parent comment")
        comment = ResearchComment(
            research_id=research_id,
            user_id=user_id,
            parent_id=payload.parent_id,
            content=payload.content.strip(),
            anchor_type=payload.anchor_type.value if payload.anchor_type else None,
            anchor_ref=payload.anchor_ref,
        )
        db.add(comment)
        await db.flush()
        user = await db.get(User, user_id)
        return self._to_response(comment, user, [])

    async def update_comment(
        self,
        db: AsyncSession,
        research_id: UUID,
        comment_id: UUID,
        user_id: UUID,
        payload: CommentUpdate,
    ) -> CommentResponse:
        project = await self._get_project(db, research_id)
        comment = await self._get_comment(db, comment_id)
        if comment.research_id != research_id or comment.deleted_at:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Comment not found")
        if not await self.permissions.can_manage_comment(
            db, project, user_id, comment.user_id
        ):
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Cannot edit comment")
        comment.content = payload.content.strip()
        comment.updated_at = datetime.now(UTC)
        await db.flush()
        user = await db.get(User, comment.user_id)
        return self._to_response(comment, user, [])

    async def delete_comment(
        self,
        db: AsyncSession,
        research_id: UUID,
        comment_id: UUID,
        user_id: UUID,
    ) -> None:
        project = await self._get_project(db, research_id)
        comment = await self._get_comment(db, comment_id)
        if comment.research_id != research_id or comment.deleted_at:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Comment not found")
        if not await self.permissions.can_manage_comment(
            db, project, user_id, comment.user_id
        ):
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Cannot delete comment")
        comment.deleted_at = datetime.now(UTC)
        await db.flush()

    async def _load_replies(
        self, db: AsyncSession, parent_id: UUID
    ) -> list[CommentResponse]:
        result = await db.execute(
            select(ResearchComment, User)
            .join(User, User.id == ResearchComment.user_id)
            .where(
                ResearchComment.parent_id == parent_id,
                ResearchComment.deleted_at.is_(None),
            )
            .order_by(ResearchComment.created_at.asc())
        )
        return [self._to_response(c, u, []) for c, u in result.all()]

    async def _get_project(self, db: AsyncSession, research_id: UUID) -> ResearchProject:
        result = await db.execute(
            select(ResearchProject).where(ResearchProject.id == research_id)
        )
        project = result.scalar_one_or_none()
        if project is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Research not found")
        return project

    async def _get_comment(self, db: AsyncSession, comment_id: UUID) -> ResearchComment:
        result = await db.execute(
            select(ResearchComment).where(ResearchComment.id == comment_id)
        )
        comment = result.scalar_one_or_none()
        if comment is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Comment not found")
        return comment

    @staticmethod
    def _to_response(
        comment: ResearchComment,
        user: User | None,
        replies: list[CommentResponse],
    ) -> CommentResponse:
        return CommentResponse(
            id=comment.id,
            research_id=comment.research_id,
            user_id=comment.user_id,
            parent_id=comment.parent_id,
            content=comment.content,
            anchor_type=comment.anchor_type,
            anchor_ref=comment.anchor_ref,
            author_name=user.full_name if user else None,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            replies=replies,
        )
