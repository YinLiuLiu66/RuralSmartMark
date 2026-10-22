from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..agents.runtime import RuntimeDep
from ..deps import SessionDep
from ..models import Artifact

router = APIRouter()


@router.get("/artifacts/{artifact_id}/file")
async def artifact_file(artifact_id: int, session: SessionDep, runtime: RuntimeDep) -> FileResponse:
    artifact = await session.get(Artifact, artifact_id)
    if artifact is None or not artifact.file_path:
        raise HTTPException(status_code=404, detail="artifact file not found")

    path = Path(artifact.file_path).resolve()
    root = runtime.artifact_dir.resolve()
    if not path.is_relative_to(root):
        raise HTTPException(status_code=403, detail="artifact path out of bounds")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="artifact file missing")

    media_type = "image/png" if path.suffix.lower() == ".png" else "application/octet-stream"
    return FileResponse(path, media_type=media_type, filename=path.name)
