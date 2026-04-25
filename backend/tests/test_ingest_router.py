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


import pytest


@pytest.mark.asyncio
async def test_safe_read_content_length_too_large():
    """_safe_read raises 413 when Content-Length header exceeds limit."""
    from fastapi import HTTPException
    from unittest.mock import MagicMock
    from app.routers.ingest import _safe_read

    mock_file = MagicMock()
    mock_file.headers = {"content-length": str(51 * 1024 * 1024)}

    with pytest.raises(HTTPException) as exc_info:
        await _safe_read(mock_file, 50 * 1024 * 1024)

    assert exc_info.value.status_code == 413


@pytest.mark.asyncio
async def test_safe_read_body_too_large():
    """_safe_read raises 413 when actual body exceeds limit (no Content-Length header)."""
    from fastapi import HTTPException
    from unittest.mock import MagicMock, AsyncMock
    from app.routers.ingest import _safe_read

    mock_file = MagicMock()
    mock_file.headers = {}
    mock_file.read = AsyncMock(return_value=b"x" * (51 * 1024 * 1024))

    with pytest.raises(HTTPException) as exc_info:
        await _safe_read(mock_file, 50 * 1024 * 1024)

    assert exc_info.value.status_code == 413