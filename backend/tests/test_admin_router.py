AUTH = {"X-API-Key": "admin-test-key"}


def test_admin_edit_invalid_uuid(client):
    resp = client.patch(
        "/admin/questions/not-a-uuid",
        json={"question_text": "new text"},
        headers=AUTH,
    )
    assert resp.status_code == 400


def test_admin_edit_not_found(client):
    resp = client.patch(
        "/admin/questions/00000000-0000-0000-0000-000000000000",
        json={"question_text": "new text"},
        headers=AUTH,
    )
    assert resp.status_code == 404


def test_admin_approve_not_found(client):
    resp = client.post(
        "/admin/questions/00000000-0000-0000-0000-000000000000/approve",
        headers=AUTH,
    )
    assert resp.status_code == 404


def test_admin_reject_not_found(client):
    resp = client.post(
        "/admin/questions/00000000-0000-0000-0000-000000000000/reject",
        headers=AUTH,
    )
    assert resp.status_code == 404


def test_admin_confirm_overlap_not_found(client):
    resp = client.post(
        "/admin/questions/00000000-0000-0000-0000-000000000000/confirm-overlap",
        headers=AUTH,
    )
    assert resp.status_code == 404


def test_admin_clear_overlap_not_found(client):
    resp = client.post(
        "/admin/questions/00000000-0000-0000-0000-000000000000/clear-overlap",
        headers=AUTH,
    )
    assert resp.status_code == 404


def test_admin_eval_score_not_found(client):
    resp = client.post(
        "/admin/evaluations/00000000-0000-0000-0000-000000000000/score",
        json={"score_overall": 8.0},
        headers=AUTH,
    )
    assert resp.status_code == 404