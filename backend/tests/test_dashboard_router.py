AUTH = {"X-API-Key": "admin-test-key"}


def test_dashboard_page_loads(client):
    resp = client.get("/dashboard", headers=AUTH)
    assert resp.status_code == 200
    text = resp.text
    assert "DSAT backend control surface" in text
    assert "Official PDF ingest" in text
    assert "Unofficial PDF ingest" in text
    assert "Generate question" in text
    assert "Inspect backend state" in text


def test_dashboard_page_requires_auth(client):
    resp = client.get("/dashboard")
    assert resp.status_code == 403


def test_dashboard_jobs_requires_auth(client):
    resp = client.get("/dashboard/jobs")
    assert resp.status_code == 403


def test_dashboard_review_page_has_phase6_controls(client):
    resp = client.get("/dashboard/review", headers=AUTH)
    assert resp.status_code == 200
    text = resp.text
    assert "Review Queue" in text
    assert "Batch ID" in text
    assert "Reviewer provider" in text
    assert "Consensus" in text
    assert "rqApprove" in text
    assert "rqReject" in text
    assert "rqReviewSwarm" in text
    assert "rqRegenerate" in text


def test_dashboard_review_page_requires_auth(client):
    resp = client.get("/dashboard/review")
    assert resp.status_code == 403


def test_dashboard_review_items_requires_auth(client):
    resp = client.get("/dashboard/review-items")
    assert resp.status_code == 403


def test_dashboard_review_items_empty_state(client):
    resp = client.get("/dashboard/review-items", headers=AUTH)
    assert resp.status_code == 200
    assert "No generated candidates match the current filters" in resp.text
