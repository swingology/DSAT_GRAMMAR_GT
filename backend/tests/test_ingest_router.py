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


def test_reannotate_accepts_json_body(client):
    """provider_name/model_name in JSON body — valid shape returns 404 (question not found), not 422."""
    resp = client.post(
        "/ingest/reannotate/00000000-0000-0000-0000-000000000000",
        headers={**AUTH, "Content-Type": "application/json"},
        json={"provider_name": "openai", "model_name": "gpt-4o"},
    )
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


def test_validate_upload_mime_rejects_unknown_type():
    from fastapi import HTTPException
    from app.routers.ingest import _validate_upload_mime

    with pytest.raises(HTTPException) as exc_info:
        _validate_upload_mime("application/x-msdownload")

    assert exc_info.value.status_code == 415


def test_validate_upload_mime_normalizes_parameters():
    from app.routers.ingest import _validate_upload_mime

    assert _validate_upload_mime("text/plain; charset=utf-8") == "text/plain"


def test_parse_pdf_content_removes_temp_file(monkeypatch):
    from pathlib import Path
    from app.routers import ingest

    seen_path = None

    def fake_parse_pdf(path):
        nonlocal seen_path
        seen_path = Path(path)
        assert seen_path.exists()
        return {"pages": [{"text": "question text"}]}

    monkeypatch.setattr(ingest, "parse_pdf", fake_parse_pdf)

    result = ingest._parse_pdf_content(b"%PDF-1.4 fake")

    assert result["pages"][0]["text"] == "question text"
    assert seen_path is not None
    assert not seen_path.exists()


@pytest.mark.asyncio
async def test_save_asset_sanitizes_filename_and_avoids_overwrite(tmp_path, monkeypatch):
    from pathlib import Path
    from app.storage.local_store import save_asset

    monkeypatch.setenv("LOCAL_ARCHIVE_MIRROR", str(tmp_path))

    first = Path(await save_asset("../same name?.pdf", b"one", subfolder="official"))
    second = Path(await save_asset("../same name?.pdf", b"two", subfolder="official"))

    assert first.parent == tmp_path / "official"
    assert second.parent == tmp_path / "official"
    assert first.name.endswith("same_name_.pdf")
    assert second.name.endswith("same_name_.pdf")
    assert first != second
    assert first.read_bytes() == b"one"
    assert second.read_bytes() == b"two"


@pytest.mark.asyncio
async def test_save_asset_rejects_escaping_subfolder(tmp_path, monkeypatch):
    from app.storage.local_store import save_asset

    monkeypatch.setenv("LOCAL_ARCHIVE_MIRROR", str(tmp_path))

    with pytest.raises(ValueError):
        await save_asset("upload.pdf", b"data", subfolder="../outside")


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
