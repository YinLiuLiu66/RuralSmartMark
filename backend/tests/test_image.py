from io import BytesIO
from pathlib import Path

from PIL import Image
from sqlalchemy import select

from ruralsmartmark.agents.orchestrator import _store_illustration
from ruralsmartmark.agents.runtime import AgentRuntime
from ruralsmartmark.config import get_settings
from ruralsmartmark.models import AgentRun, Batch
from ruralsmartmark.providers.image import (
    MockImageProvider,
    SiliconFlowImageProvider,
    get_image_provider,
    select_image_size,
)
from ruralsmartmark.providers.llm import MockLLMProvider
from ruralsmartmark.seed import seed_demo


def test_select_image_size_matches_supported_buckets():
    assert select_image_size(1024, 1024) == "512x512"
    assert select_image_size(1200, 800) == "1024x576"
    assert select_image_size(768, 1024) == "768x1024"
    assert select_image_size(1024, 1024, "768x1024") == "768x1024"


async def test_mock_image_provider_returns_png():
    content = await MockImageProvider().generate("demo", width=320, height=480)

    assert content.startswith(b"\x89PNG")
    image = Image.open(BytesIO(content))
    assert image.size == (320, 480)


def test_provider_selection_uses_mock_without_key():
    settings = get_settings().model_copy(update={"openai_api_key": ""})
    assert isinstance(get_image_provider(settings), MockImageProvider)

    with_key = get_settings().model_copy(update={"openai_api_key": "test-key"})
    assert isinstance(get_image_provider(with_key), SiliconFlowImageProvider)


class FakeImageProvider:
    name = "siliconflow"

    async def generate(self, prompt: str, *, width: int = 1024, height: int = 1024) -> bytes:
        return await MockImageProvider().generate(prompt, width=width, height=height)


async def test_illustration_is_stored_for_packaging_approval(session, tmp_path):
    await seed_demo(session)
    batch = await session.scalar(select(Batch).where(Batch.code == "ZT-DEMO-001"))
    assert batch is not None
    run = AgentRun(batch_id=batch.id, agent="packaging", status="approved")
    session.add(run)
    await session.flush()
    runtime = AgentRuntime(
        settings=get_settings(),
        llm=MockLLMProvider(),
        artifact_dir=tmp_path / "artifacts",
        allow_mock_fallback=True,
        image=FakeImageProvider(),
    )

    artifact = await _store_illustration(
        session,
        batch,
        run,
        {"ip_image_prompt": "演示插画提示词"},
        runtime,
    )
    await session.commit()

    assert artifact is not None
    assert artifact.kind == "illustration"
    assert artifact.file_path
    assert Path(artifact.file_path).is_file()
    assert artifact.content_json["demo"] is False
