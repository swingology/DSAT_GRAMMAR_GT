import uuid


def test_put_and_read_raw_official_pdf(tmp_path, monkeypatch):
    from app.config import get_settings
    from app.storage import object_store

    monkeypatch.setenv("OBJECT_STORAGE_LOCAL_ROOT", str(tmp_path))
    get_settings.cache_clear()
    object_store.load_storage_layout.cache_clear()

    asset_id = uuid.uuid4()
    stored = object_store.put_object(
        "raw_source_pdf",
        {
            "asset_id": asset_id,
            "content_origin": "official",
            "source_exam_code": "PT01",
            "source_subject_code": "verbal",
            "source_section_code": "01",
            "source_module_code": "01",
        },
        b"pdf-bytes",
        filename="../Practice Test 1.pdf",
        mime_type="application/pdf",
    )

    assert stored.storage_path.startswith("local-s3://raw-sources/")
    assert "official/PT01/verbal/section_01/module_01" in stored.storage_path
    assert stored.local_path is not None
    assert stored.local_path.exists()
    assert object_store.read_object(stored.storage_path) == b"pdf-bytes"


def test_put_rendered_page_uses_configured_page_key(tmp_path, monkeypatch):
    from app.config import get_settings
    from app.storage import object_store

    monkeypatch.setenv("OBJECT_STORAGE_LOCAL_ROOT", str(tmp_path))
    get_settings.cache_clear()
    object_store.load_storage_layout.cache_clear()

    asset_id = uuid.uuid4()
    stored = object_store.put_object(
        "rendered_page",
        {
            "asset_id": asset_id,
            "content_origin": "unofficial",
            "page_number": 6,
            "ext": "png",
        },
        b"png-bytes",
        filename="page.png",
        mime_type="image/png",
    )

    assert stored.storage_path == f"local-s3://page-renders/unofficial/{asset_id}/page_006.png"
    assert object_store.read_object(stored.storage_path) == b"png-bytes"
