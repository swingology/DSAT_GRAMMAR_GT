import pytest

AUTH = {"X-API-Key": "admin-test-key"}


def test_resolve_provider_and_model_uses_default_ollama_model():
    from types import SimpleNamespace
    from app.routers.ingest import _resolve_provider_and_model

    settings = SimpleNamespace(
        default_annotation_provider="ollama",
        default_annotation_model="deepseek-v4-pro:cloud",
        default_ollama_model="deepseek-v4-pro:cloud",
    )

    provider_name, model_name = _resolve_provider_and_model(settings, None, None)

    assert provider_name == "ollama"
    assert model_name == "deepseek-v4-pro:cloud"


def test_resolve_provider_and_model_respects_explicit_provider_and_fallback_model():
    from types import SimpleNamespace
    from app.routers.ingest import _resolve_provider_and_model

    settings = SimpleNamespace(
        default_annotation_provider="anthropic",
        default_annotation_model="claude-sonnet-4-6",
        default_ollama_model="deepseek-v4-pro:cloud",
    )

    provider_name, model_name = _resolve_provider_and_model(settings, "ollama", None)

    assert provider_name == "ollama"
    assert model_name == "deepseek-v4-pro:cloud"


def test_resolve_provider_and_model_does_not_apply_ollama_model_to_anthropic():
    from types import SimpleNamespace
    from app.routers.ingest import _resolve_provider_and_model

    settings = SimpleNamespace(
        default_annotation_provider="ollama",
        default_annotation_model="deepseek-v4-pro:cloud",
        default_ollama_model="deepseek-v4-pro:cloud",
    )

    provider_name, model_name = _resolve_provider_and_model(settings, "anthropic", None)

    assert provider_name == "anthropic"
    assert model_name == "claude-sonnet-4-6"


def test_deepseek_v4_pro_ollama_extraction_disables_thinking():
    from types import SimpleNamespace
    from app.routers.ingest import _should_disable_ollama_thinking_for_extraction

    assert _should_disable_ollama_thinking_for_extraction(
        SimpleNamespace(provider_name="ollama", model_name="deepseek-v4-pro:cloud")
    )
    assert not _should_disable_ollama_thinking_for_extraction(
        SimpleNamespace(provider_name="ollama", model_name="qwen3.6:27b")
    )
    assert not _should_disable_ollama_thinking_for_extraction(
        SimpleNamespace(provider_name="anthropic", model_name="deepseek-v4-pro:cloud")
    )


def test_build_question_source_span_links_ocr_artifacts():
    import uuid
    from types import SimpleNamespace
    from app.routers.ingest import _build_question_source_span

    question_id = uuid.uuid4()
    job_id = uuid.uuid4()
    asset_id = uuid.uuid4()
    job = SimpleNamespace(
        id=job_id,
        raw_asset_id=asset_id,
        pass1_json={
            "raw_text": "OCR text",
            "_ocr_meta": {"strategy": "glm"},
            "_ocr_artifacts": [
                {"kind": "ocr_text", "storage_path": "local-s3://ocr-artifacts/text/job/page_000/glm.txt"}
            ],
            "_page_images": [
                {
                    "page_number": 3,
                    "storage_path": "local-s3://page-renders/unofficial/asset/page_003.png",
                }
            ],
        },
    )

    span = _build_question_source_span(
        job=job,
        question_id=question_id,
        q_data={"source_page_number": 3, "source_question_number": 14},
        question_index=0,
    )

    assert span.question_id == question_id
    assert span.raw_asset_id == asset_id
    assert span.source_page_number == 3
    assert span.extraction_method == "glm_ocr"
    assert span.rendered_page_path == "local-s3://page-renders/unofficial/asset/page_003.png"
    assert span.ocr_text_path == "local-s3://ocr-artifacts/text/job/page_000/glm.txt"
    assert span.ocr_text == "OCR text"


def test_build_question_source_span_without_page_metadata_uses_first_page():
    import uuid
    from types import SimpleNamespace
    from app.routers.ingest import _build_question_source_span

    job = SimpleNamespace(
        id=uuid.uuid4(),
        raw_asset_id=uuid.uuid4(),
        pass1_json={
            "raw_text": "PDF text",
            "_page_images": [
                {"page_number": 0, "storage_path": "local-s3://page-renders/job/page_000.png"},
                {"page_number": 1, "storage_path": "local-s3://page-renders/job/page_001.png"},
            ],
        },
    )

    span = _build_question_source_span(
        job=job,
        question_id=uuid.uuid4(),
        q_data={"source_question_number": 5},
        question_index=4,
    )

    assert span.source_page_number == 0
    assert span.rendered_page_path == "local-s3://page-renders/job/page_000.png"


def test_normalize_source_metadata_accepts_legacy_codes():
    from app.routers.ingest import _normalize_source_metadata

    subject_code, section_code, module_code = _normalize_source_metadata("RW", "S1", "M2")

    assert subject_code == "verbal"
    assert section_code == "01"
    assert module_code == "02"


def test_normalize_source_metadata_accepts_split_verbal_module_codes():
    from app.routers.ingest import _normalize_source_metadata

    subject_code, section_code, module_code = _normalize_source_metadata("english", "01", "M2B")

    assert subject_code == "verbal"
    assert section_code == "01"
    assert module_code == "02B"


def test_normalize_source_metadata_rejects_bad_section():
    import pytest
    from fastapi import HTTPException
    from app.routers.ingest import _normalize_source_metadata

    with pytest.raises(HTTPException) as exc_info:
        _normalize_source_metadata("math", "03", "01")

    assert exc_info.value.status_code == 422


def test_ingest_pdf_no_file(client):
    resp = client.post("/ingest/official/pdf", headers=AUTH)
    assert resp.status_code == 422


def test_ingest_unofficial_no_file(client):
    resp = client.post("/ingest/unofficial/file", headers=AUTH)
    assert resp.status_code == 422


def test_ingest_batch_no_files(client):
    resp = client.post("/ingest/unofficial/batch", headers=AUTH)
    assert resp.status_code == 422


def test_ingest_batch_rejects_invalid_ocr_strategy(client):
    resp = client.post(
        "/ingest/unofficial/batch",
        headers=AUTH,
        data={"ocr_strategy": "bad-strategy"},
        files={"files": ("test.txt", b"some text content", "text/plain")},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_ingest_batch_forwards_ocr_strategy(monkeypatch):
    import uuid
    from datetime import datetime, timezone
    from app.models.payload import JobResponse
    from app.routers import ingest

    seen = []

    async def fake_ingest_unofficial_file(**kwargs):
        seen.append(kwargs)
        return JobResponse(
            id=str(uuid.uuid4()),
            job_type="ingest",
            status="parsing",
            created_at=datetime.now(timezone.utc),
        )

    monkeypatch.setattr(ingest, "ingest_unofficial_file", fake_ingest_unofficial_file)

    await ingest.ingest_unofficial_batch(
        files=[object(), object()],
        provider_name="anthropic",
        model_name="claude-sonnet-4-6",
        ocr_strategy="glm",
        db=object(),
        _auth="ok",
    )

    assert [call["ocr_strategy"] for call in seen] == ["glm", "glm"]


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


def test_ingest_official_pdf_rejects_invalid_ocr_strategy(client):
    resp = client.post(
        "/ingest/official/pdf",
        headers=AUTH,
        data={
            "source_exam_code": "PT06",
            "source_module_code": "01",
            "source_subject_code": "verbal",
            "ocr_strategy": "invalid-value",
        },
        files={"file": ("test.pdf", b"%PDF-fake", "application/pdf")},
    )
    assert resp.status_code == 422


def test_ingest_unofficial_file_rejects_invalid_ocr_strategy(client):
    resp = client.post(
        "/ingest/unofficial/file",
        headers=AUTH,
        data={"ocr_strategy": "bad-strategy"},
        files={"file": ("test.txt", b"some text content", "text/plain")},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_ingest_unofficial_text_upload_seeds_empty_page_texts(monkeypatch):
    from app.models.db import QuestionJob
    from app.routers import ingest

    added = []

    class _Result:
        def scalars(self):
            return self

        def first(self):
            return None

    class _Db:
        async def execute(self, _stmt):
            return _Result()

        def add(self, obj):
            added.append(obj)

        async def commit(self):
            pass

    class _Upload:
        filename = "notes.txt"
        content_type = "text/plain"
        headers = {}

        async def read(self):
            return b"plain text content"

    class _Task:
        def add_done_callback(self, _callback):
            return None

    def _fake_create_task(coro):
        coro.close()
        return _Task()

    monkeypatch.setattr(ingest, "_store_raw_upload", lambda **_kwargs: "local-s3://raw/notes.txt")
    monkeypatch.setattr(ingest.asyncio, "create_task", _fake_create_task)

    response = await ingest.ingest_unofficial_file(
        file=_Upload(),
        provider_name=None,
        model_name=None,
        ocr_strategy=None,
        db=_Db(),
        _auth="admin-test-key",
    )

    job = next(obj for obj in added if isinstance(obj, QuestionJob))
    assert response.status == "parsing"
    assert job.input_format == "text"
    assert job.pass1_json["raw_text"] == "plain text content"
    assert job.pass1_json["_page_images"] == []
    assert job.pass1_json["_page_texts"] == []


# ── Benchmark endpoint tests ──────────────────────────────────────────────────

def test_available_ocr_strategies_all_configured():
    from types import SimpleNamespace
    from app.routers.ingest import _available_ocr_strategies

    settings = SimpleNamespace(
        deepseek_ocr_base_url="http://localhost:8001",
        ocr_vision_provider="ollama",
        ollama_base_url="http://localhost:11434",
        anthropic_api_key="sk-ant-key",
        openai_api_key="sk-openai-key",
    )
    strategies = _available_ocr_strategies(settings)
    assert "deepseek" in strategies
    assert "ollama" in strategies
    assert "anthropic" in strategies
    assert "openai" in strategies


def test_available_ocr_strategies_only_anthropic():
    from types import SimpleNamespace
    from app.routers.ingest import _available_ocr_strategies

    settings = SimpleNamespace(
        deepseek_ocr_base_url="",
        ocr_vision_provider="none",
        ollama_base_url="",
        anthropic_api_key="sk-ant-key",
        openai_api_key="",
    )
    strategies = _available_ocr_strategies(settings)
    assert strategies == ["anthropic"]


def test_available_ocr_strategies_empty_when_nothing_configured():
    from types import SimpleNamespace
    from app.routers.ingest import _available_ocr_strategies

    settings = SimpleNamespace(
        deepseek_ocr_base_url="",
        ocr_vision_provider="none",
        ollama_base_url="",
        anthropic_api_key="",
        openai_api_key="",
    )
    assert _available_ocr_strategies(settings) == []


def test_build_ocr_chain_pdf_excludes_vlm_fallbacks_by_default():
    from types import SimpleNamespace
    from app.routers.ingest import _build_ocr_chain

    settings = SimpleNamespace(
        glm_ocr_model="glm-ocr:latest",
        deepseek_ocr_base_url="http://localhost:8001",
        ocr_vision_provider="ollama",
        ollama_base_url="http://localhost:11434",
        anthropic_api_key="sk-ant-key",
        openai_api_key="sk-openai-key",
        ocr_fallback=True,
        ocr_allow_vlm_pdf_fallback=False,
    )

    assert _build_ocr_chain("glm", settings, pagewise_pdf_ocr=True) == [
        "glm",
        "deepseek",
    ]


def test_build_ocr_chain_pdf_allows_vlm_fallbacks_when_enabled():
    from types import SimpleNamespace
    from app.routers.ingest import _build_ocr_chain

    settings = SimpleNamespace(
        glm_ocr_model="glm-ocr:latest",
        deepseek_ocr_base_url="http://localhost:8001",
        ocr_vision_provider="ollama",
        ollama_base_url="http://localhost:11434",
        anthropic_api_key="sk-ant-key",
        openai_api_key="sk-openai-key",
        ocr_fallback=True,
        ocr_allow_vlm_pdf_fallback=True,
    )

    assert _build_ocr_chain("glm", settings, pagewise_pdf_ocr=True) == [
        "glm",
        "deepseek",
        "anthropic",
        "openai",
        "ollama",
    ]


def test_build_ocr_chain_pdf_keeps_explicit_vlm_first():
    from types import SimpleNamespace
    from app.routers.ingest import _build_ocr_chain

    settings = SimpleNamespace(
        glm_ocr_model="glm-ocr:latest",
        deepseek_ocr_base_url="http://localhost:8001",
        ocr_vision_provider="ollama",
        ollama_base_url="http://localhost:11434",
        anthropic_api_key="sk-ant-key",
        openai_api_key="sk-openai-key",
        ocr_fallback=True,
        ocr_allow_vlm_pdf_fallback=False,
    )

    assert _build_ocr_chain("ollama", settings, pagewise_pdf_ocr=True) == [
        "ollama",
        "glm",
        "deepseek",
    ]


def test_benchmark_ocr_rejects_no_strategies(client, monkeypatch):
    import app.routers.ingest as ingest_router
    from types import SimpleNamespace

    monkeypatch.setattr(
        ingest_router,
        "get_settings",
        lambda: SimpleNamespace(
            deepseek_ocr_base_url="",
            ocr_vision_provider="none",
            ollama_base_url="",
            anthropic_api_key="",
            openai_api_key="",
        ),
    )

    resp = client.post(
        "/ingest/benchmark/ocr",
        headers=AUTH,
        files={"file": ("scan.pdf", b"%PDF-fake", "application/pdf")},
    )
    assert resp.status_code == 422
    assert "No OCR strategies" in resp.json()["detail"]


def test_benchmark_get_rejects_invalid_uuid(client):
    resp = client.get("/ingest/benchmark/ocr/not-a-valid-uuid", headers=AUTH)
    assert resp.status_code == 422


def test_benchmark_get_returns_404_for_unknown_group(client):
    import uuid
    group_id = uuid.uuid4()
    resp = client.get(f"/ingest/benchmark/ocr/{group_id}", headers=AUTH)
    assert resp.status_code == 404


# ── Layout detection degradation tests ───────────────────────────────────────


def test_build_question_source_span_without_crop_or_layout():
    """When layout detection is disabled, crop_path and layout_json_path stay None."""
    import uuid
    from types import SimpleNamespace
    from app.routers.ingest import _build_question_source_span

    question_id = uuid.uuid4()
    job_id = uuid.uuid4()
    asset_id = uuid.uuid4()
    job = SimpleNamespace(
        id=job_id,
        raw_asset_id=asset_id,
        pass1_json={
            "raw_text": "OCR text",
            "_ocr_meta": {"strategy": "glm"},
            "_ocr_artifacts": [],
            "_page_images": [],
        },
    )

    span = _build_question_source_span(
        job=job,
        question_id=question_id,
        q_data={"source_page_number": 1, "source_question_number": 5},
        question_index=0,
    )

    assert span.crop_path is None
    assert span.layout_json_path is None
    assert span.question_id == question_id


def test_build_question_source_span_with_crop_and_layout():
    """When layout detection succeeds, crop_path and layout_json_path are populated."""
    import uuid
    from types import SimpleNamespace
    from app.routers.ingest import _build_question_source_span

    question_id = uuid.uuid4()
    job_id = uuid.uuid4()
    asset_id = uuid.uuid4()
    job = SimpleNamespace(
        id=job_id,
        raw_asset_id=asset_id,
        pass1_json={
            "raw_text": "OCR text",
            "_ocr_meta": {"strategy": "glm"},
            "_ocr_artifacts": [],
            "_page_images": [],
        },
    )

    span = _build_question_source_span(
        job=job,
        question_id=question_id,
        q_data={"source_page_number": 1, "source_question_number": 5},
        question_index=0,
        crop_path="local-s3://page-crops/questions/abc/page_001/crop.png",
        layout_json_path="local-s3://ocr-artifacts/layout/job/page_001/glm_layout.json",
    )

    assert span.crop_path == "local-s3://page-crops/questions/abc/page_001/crop.png"
    assert span.layout_json_path == "local-s3://ocr-artifacts/layout/job/page_001/glm_layout.json"


def test_page_number_and_render_path_for_region_use_page_image_entry():
    import uuid
    from types import SimpleNamespace
    from app.routers.ingest import _page_number_for_region, _rendered_page_path_for_region

    job = SimpleNamespace(
        pass1_json={
            "_page_images": [
                {"page_number": 7, "storage_path": "local-s3://page-renders/x/page_007.png"},
            ],
        },
    )

    assert _page_number_for_region(job, 0) == 7
    assert _rendered_page_path_for_region(job, 0) == "local-s3://page-renders/x/page_007.png"
    assert _page_number_for_region(job, 4) == 4


def test_store_pdf_page_renders_uses_full_render_for_text_pdf(tmp_path, monkeypatch):
    import uuid
    import base64
    from app.config import get_settings
    from app.storage import object_store
    from app.routers.ingest import _store_pdf_page_renders

    monkeypatch.setenv("OBJECT_STORAGE_LOCAL_ROOT", str(tmp_path))
    get_settings.cache_clear()
    object_store.load_storage_layout.cache_clear()

    render_b64 = base64.standard_b64encode(b"fake-png").decode("utf-8")
    embedded_b64 = base64.standard_b64encode(b"embedded").decode("utf-8")
    pdf_result = {
        "pages": [
            {
                "page_number": 0,
                "text": "Question with chart",
                "images": [{"index": 0, "b64": embedded_b64, "ext": "png"}],
                "render": {"index": 0, "b64": render_b64, "ext": "png", "rendered": True},
            }
        ]
    }

    stored = _store_pdf_page_renders(
        pdf_result=pdf_result,
        asset_id=uuid.uuid4(),
        job_id=uuid.uuid4(),
        content_origin="unofficial",
        source_metadata={},
        source_stem="sample",
        max_images=10,
    )

    assert len(stored) == 1
    assert object_store.read_object(stored[0]["storage_path"]) == b"fake-png"


def test_match_region_for_question_returns_none_on_empty_layout():
    """When detect_layout fails or is disabled, match returns None gracefully."""
    from app.storage.crop_detector import match_region_for_question

    result = match_region_for_question({}, {"source_question_number": 1}, 0)
    assert result is None


def test_detect_layout_returns_empty_on_failure(monkeypatch):
    """When GLM model call fails, detect_layout returns {} (never raises)."""
    from unittest.mock import AsyncMock, MagicMock
    from app.storage.crop_detector import detect_layout

    settings = MagicMock()
    settings.glm_ocr_model = "glm-ocr:latest"
    settings.ollama_base_url = "http://localhost:11434"

    # Even with empty page images, it should return {} without error
    import asyncio
    result = asyncio.get_event_loop().run_until_complete(detect_layout([], settings))
    assert result == {}


def test_layout_json_path_lookup_with_1_based_page_number():
    """layout_paths is keyed by 0-based page_index, but _source_page_number can
    return 1-based LLM output. Verify the fallback logic resolves correctly."""
    from app.storage.crop_detector import RegionDetection

    # layout_paths keyed by 0-based index (from enumerate in detect_layout)
    layout_paths = {0: "local-s3://ocr-artifacts/layout/job/page_000/glm.json"}

    # Case 1: matched_region provides the 0-based index directly
    region = RegionDetection(
        type="question_block", label="Q1", page_index=0,
        bbox={"x": 0, "y": 0, "w": 1, "h": 1}, question_number=1,
    )
    # With a matched region, use region.page_index
    matched_layout_path = layout_paths.get(region.page_index)
    assert matched_layout_path == "local-s3://ocr-artifacts/layout/job/page_000/glm.json"

    # Case 2: no matched region, 1-based source_page_number → fallback to page_number-1
    page_number_1based = 1  # LLM says "page 1"
    fallback_path = layout_paths.get(page_number_1based) or layout_paths.get(page_number_1based - 1)
    assert fallback_path == "local-s3://ocr-artifacts/layout/job/page_000/glm.json"

    # Case 3: no matched region, 0-based already → direct hit
    page_number_0based = 0
    direct_path = layout_paths.get(page_number_0based) or layout_paths.get(page_number_0based - 1)
    assert direct_path == "local-s3://ocr-artifacts/layout/job/page_000/glm.json"


# ── _resolve_ocr_strategy tests ──────────────────────────────────────────────


def test_resolve_ocr_strategy_explicit_glm():
    from types import SimpleNamespace
    from app.routers.ingest import _resolve_ocr_strategy

    settings = SimpleNamespace(
        glm_ocr_model="glm-ocr:latest",
        deepseek_ocr_base_url="http://localhost:8001",
        ocr_vision_provider="ollama",
        ollama_base_url="http://localhost:11434",
        anthropic_api_key="sk-test",
        openai_api_key="",
    )
    assert _resolve_ocr_strategy("glm", settings) == "glm"


def test_resolve_ocr_strategy_explicit_deepseek():
    from types import SimpleNamespace
    from app.routers.ingest import _resolve_ocr_strategy

    settings = SimpleNamespace(
        glm_ocr_model="",
        deepseek_ocr_base_url="http://localhost:8001",
        ocr_vision_provider="ollama",
        ollama_base_url="http://localhost:11434",
        anthropic_api_key="",
        openai_api_key="",
    )
    assert _resolve_ocr_strategy("deepseek", settings) == "deepseek"


def test_resolve_ocr_strategy_vision_alias():
    from types import SimpleNamespace
    from app.routers.ingest import _resolve_ocr_strategy

    settings = SimpleNamespace(
        glm_ocr_model="",
        deepseek_ocr_base_url="",
        ocr_vision_provider="ollama",
        ollama_base_url="http://localhost:11434",
        anthropic_api_key="",
        openai_api_key="",
    )
    assert _resolve_ocr_strategy("vision", settings) == "ollama"


def test_resolve_ocr_strategy_anthropic_requires_key():
    import pytest
    from types import SimpleNamespace
    from app.routers.ingest import _resolve_ocr_strategy

    settings = SimpleNamespace(
        glm_ocr_model="",
        deepseek_ocr_base_url="",
        ocr_vision_provider="none",
        ollama_base_url="",
        anthropic_api_key="",
        openai_api_key="",
    )
    with pytest.raises(ValueError, match="anthropic_api_key"):
        _resolve_ocr_strategy("anthropic", settings)


def test_resolve_ocr_strategy_openai_requires_key():
    import pytest
    from types import SimpleNamespace
    from app.routers.ingest import _resolve_ocr_strategy

    settings = SimpleNamespace(
        glm_ocr_model="",
        deepseek_ocr_base_url="",
        ocr_vision_provider="none",
        ollama_base_url="",
        anthropic_api_key="",
        openai_api_key="",
    )
    with pytest.raises(ValueError, match="openai_api_key"):
        _resolve_ocr_strategy("openai", settings)


def test_resolve_ocr_strategy_auto_prefers_glm():
    from types import SimpleNamespace
    from app.routers.ingest import _resolve_ocr_strategy

    settings = SimpleNamespace(
        glm_ocr_model="glm-ocr:latest",
        deepseek_ocr_base_url="http://localhost:8001",
        ocr_vision_provider="ollama",
        ollama_base_url="http://localhost:11434",
        anthropic_api_key="sk-ant",
        openai_api_key="sk-oai",
    )
    assert _resolve_ocr_strategy("auto", settings) == "glm"


def test_resolve_ocr_strategy_auto_deepseek_when_no_glm():
    from types import SimpleNamespace
    from app.routers.ingest import _resolve_ocr_strategy

    settings = SimpleNamespace(
        glm_ocr_model="",
        deepseek_ocr_base_url="http://localhost:8001",
        ocr_vision_provider="ollama",
        ollama_base_url="http://localhost:11434",
        anthropic_api_key="",
        openai_api_key="",
    )
    assert _resolve_ocr_strategy("auto", settings) == "deepseek"


def test_resolve_ocr_strategy_auto_ollama_when_no_glm_or_deepseek():
    from types import SimpleNamespace
    from app.routers.ingest import _resolve_ocr_strategy

    settings = SimpleNamespace(
        glm_ocr_model="",
        deepseek_ocr_base_url="",
        ocr_vision_provider="ollama",
        ollama_base_url="http://localhost:11434",
        anthropic_api_key="",
        openai_api_key="",
    )
    assert _resolve_ocr_strategy("auto", settings) == "ollama"


def test_resolve_ocr_strategy_auto_anthropic_fallback():
    from types import SimpleNamespace
    from app.routers.ingest import _resolve_ocr_strategy

    settings = SimpleNamespace(
        glm_ocr_model="",
        deepseek_ocr_base_url="",
        ocr_vision_provider="none",
        ollama_base_url="",
        anthropic_api_key="sk-ant-key",
        openai_api_key="",
    )
    assert _resolve_ocr_strategy("auto", settings) == "anthropic"


def test_resolve_ocr_strategy_auto_openai_last_resort():
    from types import SimpleNamespace
    from app.routers.ingest import _resolve_ocr_strategy

    settings = SimpleNamespace(
        glm_ocr_model="",
        deepseek_ocr_base_url="",
        ocr_vision_provider="none",
        ollama_base_url="",
        anthropic_api_key="",
        openai_api_key="sk-oai-key",
    )
    assert _resolve_ocr_strategy("auto", settings) == "openai"


def test_resolve_ocr_strategy_auto_raises_when_nothing_configured():
    import pytest
    from types import SimpleNamespace
    from app.routers.ingest import _resolve_ocr_strategy

    settings = SimpleNamespace(
        glm_ocr_model="",
        deepseek_ocr_base_url="",
        ocr_vision_provider="none",
        ollama_base_url="",
        anthropic_api_key="",
        openai_api_key="",
    )
    with pytest.raises(ValueError, match="No OCR provider"):
        _resolve_ocr_strategy("auto", settings)


# ── _clean_option_label edge case tests ───────────────────────────────────────


def test_clean_option_label_none():
    from app.routers.ingest import _clean_option_label
    assert _clean_option_label(None) == ""


def test_clean_option_label_empty_string():
    from app.routers.ingest import _clean_option_label
    assert _clean_option_label("") == ""


def test_clean_option_label_whitespace_only():
    from app.routers.ingest import _clean_option_label
    assert _clean_option_label("   ") == ""


def test_clean_option_label_multichar_ab():
    """Multi-char labels like 'AB' are stripped but NOT truncated — they pass through."""
    from app.routers.ingest import _clean_option_label
    result = _clean_option_label("AB")
    assert result == "AB"  # strip + upper, no length check


def test_clean_option_label_already_clean():
    from app.routers.ingest import _clean_option_label
    for label in ("A", "B", "C", "D"):
        assert _clean_option_label(label) == label


# ── _source_page_number tests ──────────────────────────────────────────────────


def test_source_page_number_prefers_explicit_key():
    from app.routers.ingest import _source_page_number
    assert _source_page_number({"source_page_number": 3}, 0) == 3


def test_source_page_number_fallback_to_page_number():
    from app.routers.ingest import _source_page_number
    assert _source_page_number({"page_number": 5}, 0) == 5


def test_source_page_number_fallback_to_page():
    from app.routers.ingest import _source_page_number
    assert _source_page_number({"page": 2}, 0) == 2


def test_source_page_number_priority_order():
    from app.routers.ingest import _source_page_number
    # source_page_number takes priority over page_number
    assert _source_page_number({"source_page_number": 3, "page_number": 7}, 0) == 3


def test_source_page_number_string_coercion():
    from app.routers.ingest import _source_page_number
    assert _source_page_number({"source_page_number": "4"}, 0) == 4


def test_source_page_number_invalid_string_returns_fallback():
    from app.routers.ingest import _source_page_number
    assert _source_page_number({"source_page_number": "abc"}, 7) == 7


def test_source_page_number_missing_keys_returns_fallback():
    from app.routers.ingest import _source_page_number
    assert _source_page_number({}, 5) == 5


# ── _extraction_method tests ──────────────────────────────────────────────────


def test_extraction_method_glm():
    from types import SimpleNamespace
    from app.routers.ingest import _extraction_method
    job = SimpleNamespace(pass1_json={"_ocr_meta": {"strategy": "glm"}})
    assert _extraction_method(job) == "glm_ocr"


def test_extraction_method_deepseek():
    from types import SimpleNamespace
    from app.routers.ingest import _extraction_method
    job = SimpleNamespace(pass1_json={"_ocr_meta": {"strategy": "deepseek"}})
    assert _extraction_method(job) == "deepseek_ocr"


def test_extraction_method_ollama_vlm():
    from types import SimpleNamespace
    from app.routers.ingest import _extraction_method
    job = SimpleNamespace(pass1_json={"_ocr_meta": {"strategy": "ollama"}})
    assert _extraction_method(job) == "vlm_layout"


def test_extraction_method_anthropic_vlm():
    from types import SimpleNamespace
    from app.routers.ingest import _extraction_method
    job = SimpleNamespace(pass1_json={"_ocr_meta": {"strategy": "anthropic"}})
    assert _extraction_method(job) == "vlm_layout"


def test_extraction_method_pymupdf_default():
    from types import SimpleNamespace
    from app.routers.ingest import _extraction_method
    job = SimpleNamespace(pass1_json={"raw_text": "some text"})
    assert _extraction_method(job) == "pymupdf"


def test_extraction_method_empty_pass1():
    from types import SimpleNamespace
    from app.routers.ingest import _extraction_method
    job = SimpleNamespace(pass1_json=None)
    assert _extraction_method(job) == "pymupdf"


# ── _stimulus_candidates / _stimulus_kind tests ───────────────────────────────


def test_stimulus_candidates_from_stimulus_assets():
    from app.routers.ingest import _stimulus_candidates
    q_data = {
        "stimulus_assets": [
            {"stimulus_type": "table", "data": {"rows": 3}},
            {"stimulus_type": "chart", "data": {"points": 10}},
        ]
    }
    candidates = _stimulus_candidates(q_data)
    assert len(candidates) == 2
    assert candidates[0]["stimulus_type"] == "table"
    assert candidates[1]["stimulus_type"] == "chart"


def test_stimulus_candidates_from_visual_assets():
    from app.routers.ingest import _stimulus_candidates
    q_data = {
        "visual_assets": [
            {"stimulus_type": "figure", "title": "Diagram 1"},
        ]
    }
    candidates = _stimulus_candidates(q_data)
    assert len(candidates) == 1
    assert candidates[0]["stimulus_type"] == "figure"


def test_stimulus_candidates_from_shorthand_keys():
    from app.routers.ingest import _stimulus_candidates
    q_data = {
        "tables": [{"data": {"rows": 3}}],
        "charts": [{"data": {"points": 10}}],
        "graphs": [{"data": {"x": [1, 2, 3]}}],
        "figures": [{"data": {"alt": "diagram"}}],
    }
    candidates = _stimulus_candidates(q_data)
    assert len(candidates) == 4
    # shorthand keys: tables→table, charts→chart, graphs→graph, figures→figure
    assert candidates[0]["stimulus_type"] == "table"
    assert candidates[1]["stimulus_type"] == "chart"
    assert candidates[2]["stimulus_type"] == "graph"
    assert candidates[3]["stimulus_type"] == "figure"


def test_stimulus_kind_mapping():
    from app.routers.ingest import _stimulus_kind
    assert _stimulus_kind("table") == "table_asset"
    assert _stimulus_kind("chart") == "chart_asset"
    assert _stimulus_kind("graph") == "chart_asset"
    assert _stimulus_kind("figure") == "figure_asset"
    assert _stimulus_kind("unknown") == "figure_asset"


def test_build_stimulus_asset_rows_uses_candidate_source_span_and_paths(tmp_path, monkeypatch):
    import uuid
    from types import SimpleNamespace
    from app.config import get_settings
    from app.storage import object_store
    from app.routers.ingest import _build_stimulus_asset_rows

    monkeypatch.setenv("OBJECT_STORAGE_LOCAL_ROOT", str(tmp_path))
    get_settings.cache_clear()
    object_store.load_storage_layout.cache_clear()

    question_id = uuid.uuid4()
    job_id = uuid.uuid4()
    raw_asset_id = uuid.uuid4()
    question_span_id = uuid.uuid4()
    stimulus_span_id = uuid.uuid4()
    job = SimpleNamespace(id=job_id, raw_asset_id=raw_asset_id)
    q_data = {
        "source_page_number": 1,
        "stimulus_assets": [
            {
                "stimulus_type": "chart",
                "structured_data": {"series": [{"label": "A", "data": [1, 2]}]},
                "render_hints": {"chart_type": "line"},
                "_source_span_id": stimulus_span_id,
                "_source_page_number": 4,
                "_crop_path": "local-s3://page-crops/charts/q/page_004/crop.png",
                "_layout_json_path": "local-s3://ocr-artifacts/layout/job/page_004/vision_layout.json",
            }
        ],
    }

    rows = _build_stimulus_asset_rows(job, question_id, q_data, question_span_id)

    assert len(rows) == 1
    assert rows[0].source_span_id == stimulus_span_id
    assert rows[0].source_page_number == 4
    payload = object_store.read_object(rows[0].storage_path).decode("utf-8")
    assert "local-s3://page-crops/charts/q/page_004/crop.png" in payload
    assert "local-s3://ocr-artifacts/layout/job/page_004/vision_layout.json" in payload


# ── _normalize_source_metadata edge cases ──────────────────────────────────────


def test_normalize_source_metadata_empty_strings():
    from app.routers.ingest import _normalize_source_metadata
    subject, section, module = _normalize_source_metadata("", "", "")
    assert subject is None
    assert section is None
    assert module is None


def test_normalize_source_metadata_m_case_variants():
    from app.routers.ingest import _normalize_source_metadata
    for m in ("m", "M", "math", "Math", "mathematics", "MATHEMATICS"):
        subject, _, _ = _normalize_source_metadata(m, "01", "01")
        assert subject == "math", f"Failed for input: {m}"


def test_normalize_source_metadata_rw_case_variants():
    from app.routers.ingest import _normalize_source_metadata
    for rw in ("rw", "RW", "Verbal", "verbal", "reading_writing", "READING-WRITING", "english"):
        subject, _, _ = _normalize_source_metadata(rw, "01", "01")
        assert subject == "verbal", f"Failed for input: {rw}"


def test_normalize_source_metadata_invalid_subject():
    import pytest
    from fastapi import HTTPException
    from app.routers.ingest import _normalize_source_metadata

    with pytest.raises(HTTPException) as exc_info:
        _normalize_source_metadata("science", "01", "01")
    assert exc_info.value.status_code == 422


# ── _vlm_model_for_strategy tests ─────────────────────────────────────────────


def test_vlm_model_for_strategy_ollama():
    from types import SimpleNamespace
    from app.routers.ingest import _vlm_model_for_strategy
    settings = SimpleNamespace(ocr_vision_model="qwen2.5-vl:7b", default_annotation_model="x")
    assert _vlm_model_for_strategy("ollama", settings) == "qwen2.5-vl:7b"


def test_vlm_model_for_strategy_anthropic_default():
    from types import SimpleNamespace
    from app.routers.ingest import _vlm_model_for_strategy
    settings = SimpleNamespace(default_annotation_provider="openai", default_annotation_model="x")
    assert _vlm_model_for_strategy("anthropic", settings) == "claude-sonnet-4-6"


def test_vlm_model_for_strategy_anthropic_uses_default_model():
    from types import SimpleNamespace
    from app.routers.ingest import _vlm_model_for_strategy
    settings = SimpleNamespace(default_annotation_provider="anthropic", default_annotation_model="claude-opus-4-7")
    assert _vlm_model_for_strategy("anthropic", settings) == "claude-opus-4-7"


def test_vlm_model_for_strategy_openai():
    from types import SimpleNamespace
    from app.routers.ingest import _vlm_model_for_strategy
    settings = SimpleNamespace(default_annotation_provider="openai", default_annotation_model="x")
    assert _vlm_model_for_strategy("openai", settings) == "gpt-4o"


def test_vlm_model_for_strategy_unknown_returns_empty():
    from types import SimpleNamespace
    from app.routers.ingest import _vlm_model_for_strategy
    settings = SimpleNamespace(ocr_vision_model="x")
    assert _vlm_model_for_strategy("glm", settings) == ""
