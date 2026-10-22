import json
import os

import pytest
from test_second_product import AGENTS, _seed_majiang

from ruralsmartmark.config import get_settings

pytestmark = [
    pytest.mark.skipif(
        os.getenv("RSM_REAL_LLM") != "1",
        reason="真实 LLM 冒烟会消耗额度；显式设置 RSM_REAL_LLM=1 才跑",
    ),
    pytest.mark.skipif(
        not get_settings().openai_api_key,
        reason="没有配置 OPENAI_API_KEY，真实 LLM 冒烟跳过",
    ),
]


async def test_real_llm_second_product_does_not_fall_back(session, client):
    _, batch = await _seed_majiang(session)

    workspace = None
    for agent in AGENTS:
        started = await client.post(f"/api/batches/{batch.id}/pipeline/start")
        assert started.status_code == 200, started.text
        workspace = started.json()
        run = next(
            item
            for item in workspace["runs"]
            if item["agent"] == agent and item["status"] == "waiting_review"
        )
        assert run["model"] != "mock", f"{agent} 降级到了 mock：{run['output_json']}"
        assert not (run["output_json"] or {}).get("fallback_reason"), f"{agent} 有 fallback"

        approved = await client.post(
            f"/api/batches/{batch.id}/agents/{agent}/approve",
            json={},
        )
        assert approved.status_code == 200, approved.text
        workspace = approved.json()

    assert workspace is not None
    assert workspace["batch"]["state"] == "traced"
    trace_code = workspace["batch"]["trace_code"]
    assert trace_code == f"MJ{batch.id:04d}"

    trace = (await client.get(f"/api/trace/{trace_code}")).json()
    assert trace["product"]["name"] == "麻江蓝莓"
    assert trace["product"]["brand_name"] == "雾岭蓝"
    assert trace["story"]["ip_name"] == "雾岭守莓人"
    assert trace["pricing"]["premium_pct"] == 172.7

    serialized = json.dumps(trace, ensure_ascii=False)
    for forbidden in ("昭通", "乌蒙", "山风", "苹果"):
        assert forbidden not in serialized
