AUTH = {"X-API-Key": "admin-test-key"}


def test_ingest_pdf_no_file(client):
    resp = client.post("/ingest/official/pdf", headers=AUTH)
    assert resp.status_code == 422


def test_ingest_unofficial_no_file(client):
    resp = client.post("/ingest/unofficial/file", headers=AUTH)
    assert resp.status_code == 422


def test_ingest_batch_no_files(client):
    resp = client.post("/ingest/unofficial/batch", headers=AUTH)
    assert resp.status_code == 422


def test_reannotate_invalid_uuid(client):
    resp = client.post("/ingest/reannotate/not-a-uuid", headers=AUTH)
    assert resp.status_code == 400


def test_reannotate_not_found(client):
    resp = client.post("/ingest/reannotate/00000000-0000-0000-0000-000000000000", headers=AUTH)
    assert resp.status_code == 404