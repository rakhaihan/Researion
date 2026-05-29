import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class ResearchType(str, enum.Enum):
    MARKET_RESEARCH = "Market Research"
    STOCK_CRYPTO = "Stock/Crypto Research"
    ACADEMIC = "Academic Research"
    COMPETITOR = "Competitor Analysis"
    TECHNOLOGY_TREND = "Technology Trend Analysis"


class ResearchDepth(str, enum.Enum):
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    research_projects: Mapped[list["ResearchProject"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )


class QualityStatus(str, enum.Enum):
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"


class ResearchStatus(str, enum.Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PLANNING = "planning"
    SEARCHING = "searching"
    EVALUATING = "evaluating"
    SUMMARIZING = "summarizing"
    ANALYZING = "analyzing"
    CRITIQUING = "critiquing"
    WRITING = "writing"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchProject(Base):
    __tablename__ = "research_projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    research_type: Mapped[ResearchType] = mapped_column(
        Enum(ResearchType, name="research_type_enum"), nullable=False
    )
    depth: Mapped[ResearchDepth] = mapped_column(
        Enum(ResearchDepth, name="research_depth_enum"),
        nullable=False,
        default=ResearchDepth.STANDARD,
    )
    status: Mapped[ResearchStatus] = mapped_column(
        Enum(ResearchStatus, name="research_status_enum"),
        nullable=False,
        default=ResearchStatus.PENDING,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    quality_status: Mapped[QualityStatus | None] = mapped_column(
        Enum(QualityStatus, name="quality_status_enum"),
        nullable=True,
    )
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    owner: Mapped["User"] = relationship(back_populates="research_projects")
    quality_evaluation: Mapped["ResearchQualityEvaluation | None"] = relationship(
        back_populates="research",
        cascade="all, delete-orphan",
        uselist=False,
    )
    questions: Mapped[list["ResearchQuestion"]] = relationship(
        back_populates="research",
        cascade="all, delete-orphan",
        order_by="ResearchQuestion.priority",
    )
    sources: Mapped[list["SourceResult"]] = relationship(
        back_populates="research",
        cascade="all, delete-orphan",
    )
    final_report: Mapped["FinalReport | None"] = relationship(
        back_populates="research",
        cascade="all, delete-orphan",
        uselist=False,
    )
    jobs: Mapped[list["ResearchJob"]] = relationship(
        back_populates="research",
        cascade="all, delete-orphan",
        order_by="ResearchJob.created_at.desc()",
    )


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchStep(str, enum.Enum):
    PLANNING = "planning"
    SEARCHING = "searching"
    EVALUATING_SOURCES = "evaluating_sources"
    SUMMARIZING = "summarizing"
    ANALYZING = "analyzing"
    CRITIQUING = "critiquing"
    WRITING_REPORT = "writing_report"
    COMPLETED = "completed"


STEP_PROGRESS: dict[str, int] = {
    ResearchStep.PLANNING.value: 10,
    ResearchStep.SEARCHING.value: 25,
    ResearchStep.EVALUATING_SOURCES.value: 40,
    ResearchStep.SUMMARIZING.value: 55,
    ResearchStep.ANALYZING.value: 70,
    ResearchStep.CRITIQUING.value: 85,
    ResearchStep.WRITING_REPORT.value: 95,
    ResearchStep.COMPLETED.value: 100,
}


class ResearchJob(Base):
    __tablename__ = "research_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    research_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("research_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_id: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True, index=True)
    current_step: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status_enum"),
        nullable=False,
        default=JobStatus.QUEUED,
    )
    progress_percentage: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    job_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    research: Mapped["ResearchProject"] = relationship(back_populates="jobs")


class ResearchQuestion(Base):
    __tablename__ = "research_questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    research_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("research_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    research: Mapped["ResearchProject"] = relationship(back_populates="questions")
    sources: Mapped[list["SourceResult"]] = relationship(back_populates="question")


class SourceResult(Base):
    __tablename__ = "source_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    research_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("research_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("research_questions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    citation_key: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    snippet: Mapped[str] = mapped_column(Text, nullable=False, default="")
    credibility_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    credibility_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    published_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    raw_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    accessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    research: Mapped["ResearchProject"] = relationship(back_populates="sources")
    question: Mapped["ResearchQuestion | None"] = relationship(back_populates="sources")
    summary: Mapped["SourceSummary | None"] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
        uselist=False,
    )


class SourceSummary(Base):
    __tablename__ = "source_summaries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("source_results.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    citation_key: Mapped[str | None] = mapped_column(String(10), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    key_points: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    limitations: Mapped[str | None] = mapped_column(Text, nullable=True)
    useful_quotes: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    source: Mapped["SourceResult"] = relationship(back_populates="summary")


class FinalReport(Base):
    __tablename__ = "final_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    research_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("research_projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    executive_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    detailed_analysis: Mapped[str] = mapped_column(Text, nullable=False, default="")
    key_findings: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    risks: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    conclusion: Mapped[str] = mapped_column(Text, nullable=False, default="")
    markdown_content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    critique_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    analysis_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    research: Mapped["ResearchProject"] = relationship(back_populates="final_report")


class ResearchQualityEvaluation(Base):
    __tablename__ = "research_quality_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    research_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("research_projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    citation_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    source_diversity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    source_credibility_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    freshness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    completeness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    quality_status: Mapped[QualityStatus] = mapped_column(
        Enum(QualityStatus, name="quality_status_enum"),
        nullable=False,
        default=QualityStatus.WARNING,
    )
    warnings: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    recommendations: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    citation_validation: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    claim_check: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    research: Mapped["ResearchProject"] = relationship(back_populates="quality_evaluation")
