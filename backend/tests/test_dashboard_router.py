def test_dashboard_page_loads(client):
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    text = resp.text
    assert "DSAT backend control surface" in text
    assert "Official PDF ingest" in text
    assert "Unofficial PDF ingest" in text
    assert "Generate question" in text
    assert "Inspect backend state" in text


def test_dashboard_jobs_requires_auth(client):
    resp = client.get("/dashboard/jobs")
    assert resp.status_code == 403
