from datetime import datetime

from sqlalchemy import (
    DDL,
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    event,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ProductProfile(TimestampMixin, Base):
    __tablename__ = "product_profile"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    county: Mapped[str] = mapped_column(String(120))
    province: Mapped[str] = mapped_column(String(80), default="")
    category: Mapped[str] = mapped_column(String(80))
    form: Mapped[str] = mapped_column(String(120))
    specs: Mapped[dict] = mapped_column(JSON, default=dict)
    palette: Mapped[dict] = mapped_column(JSON, default=dict)
    scene_preset: Mapped[str] = mapped_column(String(80), default="orchard")
    knowledge_dir: Mapped[str] = mapped_column(String(255), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)


class Batch(TimestampMixin, Base):
    __tablename__ = "batch"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("product_profile.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    quantity_kg: Mapped[float] = mapped_column(Float, default=500.0)
    state: Mapped[str] = mapped_column(String(40), default="raw", index=True)
    current_station: Mapped[str] = mapped_column(String(40), default="intake")
    story_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    packaging_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    marketing_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    pricing_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    trace_code: Mapped[str | None] = mapped_column(
        String(40), unique=True, nullable=True, index=True
    )


class AgentRun(Base):
    __tablename__ = "agent_run"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("batch.id", ondelete="CASCADE"), index=True)
    agent: Mapped[str] = mapped_column(String(40), index=True)
    status: Mapped[str] = mapped_column(String(40), default="queued", index=True)
    input_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    guard_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tokens: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Artifact(Base):
    __tablename__ = "artifact"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("batch.id", ondelete="CASCADE"), index=True)
    agent_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("agent_run.id", ondelete="SET NULL"), nullable=True
    )
    kind: Mapped[str] = mapped_column(String(40), index=True)
    content_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class KnowledgeDoc(Base):
    __tablename__ = "knowledge_doc"
    __table_args__ = (
        Index("uq_knowledge_doc_product_doc", "product_id", "doc_key", unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("product_profile.id", ondelete="CASCADE"), index=True
    )
    doc_key: Mapped[str] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(40), index=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    credibility: Mapped[str] = mapped_column(String(20), default="todo")


class Benchmark(Base):
    __tablename__ = "benchmark"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("product_profile.id", ondelete="CASCADE"), index=True
    )
    channel: Mapped[str] = mapped_column(String(80))
    competitor: Mapped[str] = mapped_column(String(120))
    spec: Mapped[str] = mapped_column(String(120))
    price_per_kg: Mapped[float] = mapped_column(Float)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Kol(Base):
    __tablename__ = "kol"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    platform: Mapped[str] = mapped_column(String(80))
    followers: Mapped[int] = mapped_column(Integer, default=0)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    region: Mapped[str] = mapped_column(String(120), default="")
    rate: Mapped[str] = mapped_column(String(80), default="")
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)


class ScanEvent(Base):
    __tablename__ = "scan_event"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("batch.id", ondelete="CASCADE"), index=True)
    trace_code: Mapped[str] = mapped_column(String(40), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    channel: Mapped[str] = mapped_column(String(80), default="qr")
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)


class ChatMessage(Base):
    __tablename__ = "chat_message"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("batch.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ControllerSession(TimestampMixin, Base):
    __tablename__ = "controller_session"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("product_profile.id", ondelete="SET NULL"), nullable=True, index=True
    )
    batch_id: Mapped[int | None] = mapped_column(
        ForeignKey("batch.id", ondelete="SET NULL"), nullable=True, index=True
    )
    draft_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    pending_action_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    summary_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)


event.listen(
    ControllerSession.__table__,
    "after_create",
    DDL(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_controller_session_blank "
        "ON controller_session ((1)) "
        "WHERE product_id IS NULL AND batch_id IS NULL"
    ),
)


class ControllerMessage(Base):
    __tablename__ = "controller_message"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("controller_session.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    action_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
