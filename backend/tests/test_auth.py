"""M1-c 鉴权测试：401 / 403 / 200 全路径（真实 PG，账号由 conftest seed）。"""

from fastapi.testclient import TestClient

from ruralsmartmark.app import app

client = TestClient(app)

FORM = {"Content-Type": "application/x-www-form-urlencoded"}


def _token(username: str, password: str) -> str:
    resp = client.post(
        "/api/auth/token",
        data={"username": username, "password": password},
        headers=FORM,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def test_Health() -> None:
    assert client.get("/api/health").json()["status"] == "ok"


def test_token_wrong_password_401() -> None:
    resp = client.post(
        "/api/auth/token",
        data={"username": "operator", "password": "bad"},
        headers=FORM,
    )
    assert resp.status_code == 401


def test_token_unknown_user_401() -> None:
    resp = client.post(
        "/api/auth/token", data={"username": "nobody", "password": "x"}, headers=FORM
    )
    assert resp.status_code == 401


def test_me_without_token_401() -> None:
    assert client.get("/api/auth/me").status_code == 401


def test_me_with_bad_token_401() -> None:
    resp = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert resp.status_code == 401


def test_me_operator_200() -> None:
    token = _token("operator", "operator-demo")
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == "operator"
    assert body["role"] == "operator"


def test_sim_control_without_token_401() -> None:
    resp = client.post("/api/sim/control", json={"action": "pause"})
    assert resp.status_code == 401


def test_sim_control_wrong_role_403() -> None:
    # 合作社角色无 sim 控制权（03 §4 权限矩阵）
    token = _token("coop", "coop-demo")
    resp = client.post(
        "/api/sim/control",
        json={"action": "pause"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_sim_control_operator_200() -> None:
    token = _token("operator", "operator-demo")
    resp = client.post(
        "/api/sim/control",
        json={"action": "pause"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["detail"] == "not implemented until M2"
