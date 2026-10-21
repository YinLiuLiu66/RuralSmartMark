"""M4 Agent 任务验收：mock 模型下的发起 / 产出 / 三态流转 / 权限（#25/#26）。"""

import pytest
from fastapi.testclient import TestClient

from ruralsmartmark.agents import llm
from ruralsmartmark.app import app

client = TestClient(app)

FORM = {"Content-Type": "application/x-www-form-urlencoded"}


@pytest.fixture(autouse=True)
def _force_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    # 测试一律走 mock：不联网、不依赖真实 key，空内容兜底仍可断言
    monkeypatch.setattr(llm, "is_configured", lambda: False)


def _token(username: str = "operator", password: str = "operator-demo") -> str:
    resp = client.post(
        "/api/auth/token",
        data={"username": username, "password": password},
        headers=FORM,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _auth(username: str = "operator") -> dict[str, str]:
    password = "operator-demo" if username == "operator" else "coop-demo"
    return {"Authorization": f"Bearer {_token(username, password)}"}


def _create(agent_type: str, headers: dict[str, str]) -> dict:
    resp = client.post(
        "/api/agent-tasks", json={"agent_type": agent_type}, headers=headers
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _get(task_id: int, headers: dict[str, str]) -> dict:
    resp = client.get(f"/api/agent-tasks/{task_id}", headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_create_requires_auth() -> None:
    resp = client.post("/api/agent-tasks", json={"agent_type": "story"})
    assert resp.status_code == 401


def test_invalid_agent_type_422() -> None:
    resp = client.post(
        "/api/agent-tasks", json={"agent_type": "design"}, headers=_auth()
    )
    assert resp.status_code == 422


def test_story_task_runs_to_done_and_creates_draft() -> None:
    headers = _auth()
    task = _create("story", headers)

    # BackgroundTasks 在 TestClient 内同步执行完，GET 已是终态
    task = _get(task["id"], headers)
    assert task["status"] == "done"
    assert len(task["artifacts"]) == 1
    artifact = task["artifacts"][0]
    assert artifact["kind"] == "story"
    assert artifact["status"] == "draft"
    assert "麻江" in artifact["content"]
    assert "IP 定位：" in artifact["content"]

    listed = client.get("/api/agent-tasks", headers=headers)
    assert listed.status_code == 200
    assert any(t["id"] == task["id"] for t in listed.json())


def test_artifact_three_state_flow_and_final_lock() -> None:
    headers = _auth()
    task = _get(_create("copy", headers)["id"], headers)
    artifact = task["artifacts"][0]

    resp = client.patch(
        f"/api/agent-artifacts/{artifact['id']}",
        json={"content": "人工润色后的文案", "status": "polished"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "polished"
    assert resp.json()["content"] == "人工润色后的文案"

    resp = client.patch(
        f"/api/agent-artifacts/{artifact['id']}",
        json={"status": "final"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "final"

    resp = client.patch(
        f"/api/agent-artifacts/{artifact['id']}",
        json={"content": "定稿后还想改"},
        headers=headers,
    )
    assert resp.status_code == 409


def test_patch_requires_a_field() -> None:
    headers = _auth()
    task = _get(_create("story", headers)["id"], headers)
    resp = client.patch(
        f"/api/agent-artifacts/{task['artifacts'][0]['id']}",
        json={},
        headers=headers,
    )
    assert resp.status_code == 422


def test_coop_can_create_and_edit_own_draft_but_not_finalize() -> None:
    coop = _auth("coop")
    task = _get(_create("story", coop)["id"], coop)
    artifact = task["artifacts"][0]

    resp = client.patch(
        f"/api/agent-artifacts/{artifact['id']}",
        json={"content": "合作社自己改的草稿"},
        headers=coop,
    )
    assert resp.status_code == 200, resp.text

    resp = client.patch(
        f"/api/agent-artifacts/{artifact['id']}",
        json={"status": "polished"},
        headers=coop,
    )
    assert resp.status_code == 403


def test_coop_cannot_edit_others_artifact() -> None:
    operator = _auth()
    task = _get(_create("story", operator)["id"], operator)
    resp = client.patch(
        f"/api/agent-artifacts/{task['artifacts'][0]['id']}",
        json={"content": "越权修改"},
        headers=_auth("coop"),
    )
    assert resp.status_code == 403


def test_llm_failure_marks_task_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _boom(*args: object, **kwargs: object) -> str:
        raise llm.LLMError("模拟端点失败")

    monkeypatch.setattr(llm, "is_configured", lambda: True)
    monkeypatch.setattr(llm, "complete", _boom)

    headers = _auth()
    task = _create("story", headers)
    task = _get(task["id"], headers)
    assert task["status"] == "failed"
    assert task["artifacts"] == []
