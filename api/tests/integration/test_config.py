"""Integration test: GET /v1/config. See api/CLAUDE.md → App Config Endpoint."""


async def test_get_config_returns_seeded_defaults(client):
    response = await client.get("/v1/config")
    assert response.status_code == 200
    body = response.json()
    assert body["min_app_version"] == "1.0.0"
    assert body["latest_version"] == "1.0.0"
    assert body["force_update"] is False
    assert body["maintenance_mode"] is False
    assert body["maintenance_message"] is None
