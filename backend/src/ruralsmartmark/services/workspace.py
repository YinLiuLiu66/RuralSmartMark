from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AgentRun, Artifact, Batch
from ..schemas import AgentRunOut, ArtifactOut, BatchFullOut, BatchWorkspaceOut


async def load_workspace(session: AsyncSession, batch_id: int) -> BatchWorkspaceOut | None:
    batch = await session.get(Batch, batch_id)
    if batch is None:
        return None
    await session.refresh(batch)

    runs = list(
        (
            await session.execute(
                select(AgentRun).where(AgentRun.batch_id == batch_id).order_by(AgentRun.id.desc())
            )
        )
        .scalars()
        .all()
    )
    artifacts = list(
        (
            await session.execute(
                select(Artifact).where(Artifact.batch_id == batch_id).order_by(Artifact.id.desc())
            )
        )
        .scalars()
        .all()
    )

    artifact_items = []
    for artifact in artifacts:
        item = ArtifactOut.model_validate(artifact)
        if artifact.file_path:
            item.file_url = f"/api/artifacts/{artifact.id}/file"
        artifact_items.append(item)

    return BatchWorkspaceOut(
        batch=BatchFullOut.model_validate(batch),
        runs=[AgentRunOut.model_validate(run) for run in runs],
        artifacts=artifact_items,
    )
