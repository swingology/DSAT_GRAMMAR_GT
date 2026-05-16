"""Unit tests for layout detection, region matching, and image cropping."""

import base64
import io
import uuid
from dataclasses import asdict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image

from app.storage.crop_detector import (
    CropResult,
    RegionDetection,
    _clamp_bbox,
    _is_valid_bbox,
    _parse_question_number,
    _parse_region_list,
    crop_and_store,
    detect_layout,
    match_region_for_question,
    match_stimulus_regions_for_question,
)


# ── _parse_question_number ────────────────────────────────────────────────────

def test_parse_question_number_from_q_prefix():
    assert _parse_question_number("Q3") == 3
    assert _parse_question_number("Q27") == 27


def test_parse_question_number_from_plain_number():
    assert _parse_question_number("14") == 14


def test_parse_question_number_from_question_label():
    assert _parse_question_number("Question 7") == 7


def test_parse_question_number_returns_none_for_no_digits():
    assert _parse_question_number("Table A") is None
    assert _parse_question_number("") is None


def test_parse_question_number_from_mixed_label():
    assert _parse_question_number("Q3a") == 3


# ── _clamp_bbox / _is_valid_bbox ─────────────────────────────────────────────

def test_clamp_bbox_within_bounds():
    result = _clamp_bbox({"x": 0.1, "y": 0.2, "w": 0.5, "h": 0.3})
    assert result == {"x": 0.1, "y": 0.2, "w": 0.5, "h": 0.3}


def test_clamp_bbox_clamps_out_of_range():
    result = _clamp_bbox({"x": -0.5, "y": 1.5, "w": 2.0, "h": -0.1})
    assert result["x"] == 0.0
    assert result["y"] == 1.0
    assert result["w"] == 1.0
    assert result["h"] == 0.0


def test_is_valid_bbox_accepts_meaningful_area():
    assert _is_valid_bbox({"x": 0.1, "y": 0.2, "w": 0.5, "h": 0.5})


def test_is_valid_bbox_rejects_tiny_area():
    assert not _is_valid_bbox({"x": 0.1, "y": 0.2, "w": 0.001, "h": 0.001})


# ── _parse_region_list ───────────────────────────────────────────────────────

def test_parse_region_list_valid_types():
    raw = [
        {"type": "question_block", "label": "Q1", "bbox": {"x": 0.0, "y": 0.0, "w": 0.5, "h": 0.5}},
        {"type": "table", "label": "Table 1", "bbox": {"x": 0.5, "y": 0.0, "w": 0.5, "h": 0.5}},
        {"type": "chart", "label": "Chart A", "bbox": {"x": 0.0, "y": 0.5, "w": 0.5, "h": 0.5}},
        {"type": "figure", "label": "Fig 1", "bbox": {"x": 0.5, "y": 0.5, "w": 0.5, "h": 0.5}},
    ]
    regions = _parse_region_list(raw, page_index=2)
    assert len(regions) == 4
    assert regions[0].type == "question_block"
    assert regions[0].question_number == 1
    assert regions[0].page_index == 2
    assert regions[1].type == "table"
    assert regions[1].question_number == 1  # "Table 1" contains digit "1"


def test_parse_region_list_synonyms():
    raw = [
        {"type": "question", "label": "Q5", "bbox": {"x": 0, "y": 0, "w": 1, "h": 1}},
        {"type": "graph", "label": "G1", "bbox": {"x": 0, "y": 0, "w": 1, "h": 1}},
        {"type": "diagram", "label": "D1", "bbox": {"x": 0, "y": 0, "w": 1, "h": 1}},
        {"type": "image", "label": "Img1", "bbox": {"x": 0, "y": 0, "w": 1, "h": 1}},
    ]
    regions = _parse_region_list(raw, page_index=0)
    assert len(regions) == 4
    assert regions[0].type == "question_block"
    assert regions[1].type == "chart"
    assert regions[2].type == "figure"
    assert regions[3].type == "figure"


def test_parse_region_list_skips_invalid():
    raw = [
        {"type": "question_block", "label": "Q1"},  # no bbox
        {"type": "unknown_type", "label": "X", "bbox": {"x": 0, "y": 0, "w": 1, "h": 1}},
        {"type": "question_block", "label": "", "bbox": {"x": 0, "y": 0, "w": 0.001, "h": 0.001}},  # too small
    ]
    regions = _parse_region_list(raw, page_index=0)
    assert len(regions) == 0


def test_parse_region_list_generates_label_from_type():
    raw = [
        {"type": "question_block", "label": "", "bbox": {"x": 0, "y": 0, "w": 0.5, "h": 0.5}},
    ]
    regions = _parse_region_list(raw, page_index=3)
    assert regions[0].label == "question_block_3"


# ── match_region_for_question ─────────────────────────────────────────────────

def _make_region(q_num, page=0):
    return RegionDetection(
        type="question_block",
        label=f"Q{q_num}",
        page_index=page,
        bbox={"x": 0.0, "y": 0.0, "w": 0.5, "h": 0.5},
        question_number=q_num,
    )


def test_match_by_question_number():
    regions = {0: [_make_region(1), _make_region(2), _make_region(3)]}
    result = match_region_for_question(regions, {"source_question_number": 2}, 0)
    assert result is not None
    assert result.question_number == 2


def test_match_by_positional_index():
    regions = {0: [_make_region(1), _make_region(2)]}
    result = match_region_for_question(regions, {"source_question_number": None}, 1)
    assert result is not None
    assert result.question_number == 2


def test_match_returns_none_for_empty_layout():
    result = match_region_for_question({}, {"source_question_number": 1}, 0)
    assert result is None


def test_match_returns_none_for_out_of_range_index():
    regions = {0: [_make_region(1)]}
    result = match_region_for_question(regions, {"source_question_number": None}, 5)
    assert result is None


def test_match_ignores_non_question_block_regions():
    table = RegionDetection(
        type="table", label="Table 1", page_index=0,
        bbox={"x": 0, "y": 0, "w": 0.5, "h": 0.5}, question_number=None,
    )
    regions = {0: [table]}
    result = match_region_for_question(regions, {"source_question_number": None}, 0)
    assert result is None


def test_match_number_takes_priority_over_position():
    r1 = _make_region(1)
    r2 = _make_region(2)
    r3 = _make_region(3)
    regions = {0: [r1, r2, r3]}
    # question_index=0 would match r1 by position, but q_num=3 should match r3
    result = match_region_for_question(regions, {"source_question_number": 3}, 0)
    assert result.question_number == 3


def test_match_stimulus_filters_by_explicit_question_label():
    q2 = _make_region(2)
    q2_chart = RegionDetection(
        type="chart",
        label="Q2 chart",
        page_index=0,
        bbox={"x": 0.1, "y": 0.6, "w": 0.4, "h": 0.2},
        question_number=2,
    )
    q3_table = RegionDetection(
        type="table",
        label="Q3 table",
        page_index=0,
        bbox={"x": 0.55, "y": 0.6, "w": 0.35, "h": 0.2},
        question_number=3,
    )

    result = match_stimulus_regions_for_question({0: [q2, q2_chart, q3_table]}, q2)

    assert result == [q2_chart]


def test_match_stimulus_does_not_treat_table_number_as_question_number():
    q2 = RegionDetection(
        type="question_block",
        label="Q2",
        page_index=0,
        bbox={"x": 0.1, "y": 0.1, "w": 0.45, "h": 0.25},
        question_number=2,
    )
    nearby_table = RegionDetection(
        type="table",
        label="Table 1",
        page_index=0,
        bbox={"x": 0.12, "y": 0.36, "w": 0.4, "h": 0.2},
        question_number=1,
    )

    result = match_stimulus_regions_for_question({0: [q2, nearby_table]}, q2)

    assert result == [nearby_table]


def test_match_stimulus_rejects_unrelated_same_page_visual():
    q1 = RegionDetection(
        type="question_block",
        label="Q1",
        page_index=0,
        bbox={"x": 0.05, "y": 0.05, "w": 0.35, "h": 0.2},
        question_number=1,
    )
    distant_chart = RegionDetection(
        type="chart",
        label="Chart",
        page_index=0,
        bbox={"x": 0.6, "y": 0.75, "w": 0.35, "h": 0.2},
        question_number=None,
    )

    result = match_stimulus_regions_for_question({0: [q1, distant_chart]}, q1)

    assert result == []


# ── crop_and_store ────────────────────────────────────────────────────────────

def _make_png_bytes(width=400, height=600):
    """Create a small white PNG image in memory."""
    img = Image.new("RGB", (width, height), "white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_crop_and_store_with_temp_file(tmp_path, monkeypatch):
    from app.config import get_settings
    from app.storage import object_store

    monkeypatch.setenv("OBJECT_STORAGE_LOCAL_ROOT", str(tmp_path))
    get_settings.cache_clear()
    object_store.load_storage_layout.cache_clear()

    # Write a page image to a temp file
    png_bytes = _make_png_bytes(400, 600)
    page_file = tmp_path / "page_000.png"
    page_file.write_bytes(png_bytes)

    page_images_data = [{"path": str(page_file), "mime_type": "image/png"}]
    region = RegionDetection(
        type="question_block",
        label="Q1",
        page_index=0,
        bbox={"x": 0.1, "y": 0.2, "w": 0.5, "h": 0.3},
        question_number=1,
    )
    question_id = uuid.uuid4()

    result = crop_and_store(region, page_images_data, question_id)
    assert result is not None
    assert isinstance(result, CropResult)
    assert result.region is region
    assert result.storage_path.startswith("local-s3://page-crops/")

    # Verify the cropped image is readable
    crop_bytes = object_store.read_object(result.storage_path)
    cropped_img = Image.open(io.BytesIO(crop_bytes))
    # Expected: 0.5 * 400 = 200 width, 0.3 * 600 = 180 height
    assert cropped_img.size[0] == 200
    assert cropped_img.size[1] == 180


def test_crop_and_store_with_b64_fallback(tmp_path, monkeypatch):
    from app.config import get_settings
    from app.storage import object_store

    monkeypatch.setenv("OBJECT_STORAGE_LOCAL_ROOT", str(tmp_path))
    get_settings.cache_clear()
    object_store.load_storage_layout.cache_clear()

    png_bytes = _make_png_bytes(400, 600)
    b64 = base64.standard_b64encode(png_bytes).decode("utf-8")

    page_images_data = [{"b64": b64, "mime_type": "image/png"}]
    region = RegionDetection(
        type="question_block",
        label="Q1",
        page_index=0,
        bbox={"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0},
        question_number=1,
    )
    question_id = uuid.uuid4()

    result = crop_and_store(region, page_images_data, question_id)
    assert result is not None
    # Full-page crop should match original dimensions
    crop_bytes = object_store.read_object(result.storage_path)
    cropped_img = Image.open(io.BytesIO(crop_bytes))
    assert cropped_img.size == (400, 600)


def test_crop_and_store_returns_none_for_missing_page():
    region = RegionDetection(
        type="question_block",
        label="Q1",
        page_index=5,  # out of range
        bbox={"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0},
        question_number=1,
    )
    result = crop_and_store(region, [], uuid.uuid4())
    assert result is None


def test_crop_and_store_returns_none_for_unloadable_image():
    # No path, no storage_path, no b64
    page_images_data = [{"mime_type": "image/png"}]
    region = RegionDetection(
        type="question_block",
        label="Q1",
        page_index=0,
        bbox={"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0},
        question_number=1,
    )
    result = crop_and_store(region, page_images_data, uuid.uuid4())
    assert result is None


def test_crop_and_store_returns_none_for_degenerate_bbox(tmp_path, monkeypatch):
    from app.config import get_settings
    from app.storage import object_store

    monkeypatch.setenv("OBJECT_STORAGE_LOCAL_ROOT", str(tmp_path))
    get_settings.cache_clear()
    object_store.load_storage_layout.cache_clear()

    png_bytes = _make_png_bytes(400, 600)
    page_file = tmp_path / "page_000.png"
    page_file.write_bytes(png_bytes)

    page_images_data = [{"path": str(page_file), "mime_type": "image/png"}]
    region = RegionDetection(
        type="question_block",
        label="Q1",
        page_index=0,
        bbox={"x": 0.5, "y": 0.5, "w": 0.0, "h": 0.0},  # zero area
        question_number=1,
    )

    # _clamp_bbox makes w/h = 0.0, _is_valid_bbox rejects, but crop_and_store
    # uses raw bbox for pixel conversion. With w=0, right == left → degenerate.
    result = crop_and_store(region, page_images_data, uuid.uuid4())
    assert result is None


# ── detect_layout ─────────────────────────────────────────────────────────────

def _make_page_image_entry(png_bytes):
    b64 = base64.standard_b64encode(png_bytes).decode("utf-8")
    return {"b64": b64, "mime_type": "image/png"}


@pytest.mark.asyncio
async def test_detect_layout_returns_regions(tmp_path, monkeypatch):
    from app.config import get_settings
    from app.storage import object_store

    monkeypatch.setenv("OBJECT_STORAGE_LOCAL_ROOT", str(tmp_path))
    get_settings.cache_clear()
    object_store.load_storage_layout.cache_clear()

    png_bytes = _make_png_bytes()
    page_images_data = [_make_page_image_entry(png_bytes)]

    fake_response = MagicMock()
    fake_response.raw_text = '[{"type": "question_block", "label": "Q1", "bbox": {"x": 0.1, "y": 0.2, "w": 0.5, "h": 0.3}}]'

    with patch("app.llm.ollama_provider.OllamaProvider") as MockProvider:
        mock_provider = AsyncMock()
        mock_provider.complete_vision = AsyncMock(return_value=fake_response)
        mock_provider.close = AsyncMock()
        MockProvider.return_value = mock_provider

        with patch("app.storage.crop_detector.extract_json_from_text") as mock_extract:
            mock_extract.return_value = [
                {"type": "question_block", "label": "Q1", "bbox": {"x": 0.1, "y": 0.2, "w": 0.5, "h": 0.3}},
            ]

            settings = MagicMock()
            settings.glm_ocr_model = "glm-ocr:latest"
            settings.ollama_base_url = "http://localhost:11434"

            result = await detect_layout(page_images_data, settings)

    assert 0 in result
    assert len(result[0]) == 1
    assert result[0][0].type == "question_block"
    assert result[0][0].question_number == 1


@pytest.mark.asyncio
async def test_detect_layout_returns_empty_when_model_not_set():
    settings = MagicMock()
    settings.glm_ocr_model = ""

    result = await detect_layout([], settings)
    assert result == {}


@pytest.mark.asyncio
async def test_detect_layout_returns_empty_on_exception(tmp_path, monkeypatch):
    from app.config import get_settings
    from app.storage import object_store

    monkeypatch.setenv("OBJECT_STORAGE_LOCAL_ROOT", str(tmp_path))
    get_settings.cache_clear()
    object_store.load_storage_layout.cache_clear()

    png_bytes = _make_png_bytes()
    page_images_data = [_make_page_image_entry(png_bytes)]

    with patch("app.llm.ollama_provider.OllamaProvider") as MockProvider:
        mock_provider = AsyncMock()
        mock_provider.complete_vision = AsyncMock(side_effect=RuntimeError("model not found"))
        mock_provider.close = AsyncMock()
        MockProvider.return_value = mock_provider

        settings = MagicMock()
        settings.glm_ocr_model = "glm-ocr:latest"
        settings.ollama_base_url = "http://localhost:11434"

        result = await detect_layout(page_images_data, settings)

    assert result == {}


@pytest.mark.asyncio
async def test_detect_layout_falls_back_to_anthropic(tmp_path, monkeypatch):
    from app.config import get_settings
    from app.storage import object_store

    monkeypatch.setenv("OBJECT_STORAGE_LOCAL_ROOT", str(tmp_path))
    get_settings.cache_clear()
    object_store.load_storage_layout.cache_clear()

    png_bytes = _make_png_bytes()
    page_images_data = [_make_page_image_entry(png_bytes)]

    fake_response = MagicMock()
    fake_response.raw_text = '[{"type": "chart", "label": "Q2 chart", "bbox": {"x": 0.2, "y": 0.3, "w": 0.4, "h": 0.2}}]'

    with patch("app.llm.ollama_provider.OllamaProvider") as MockProvider:
        glm_provider = AsyncMock()
        glm_provider.complete_vision = AsyncMock(side_effect=RuntimeError("glm unavailable"))
        glm_provider.close = AsyncMock()
        MockProvider.return_value = glm_provider

        anthropic_provider = AsyncMock()
        anthropic_provider.complete_vision = AsyncMock(return_value=fake_response)
        with patch("app.llm.factory.get_provider", return_value=anthropic_provider):
            with patch("app.storage.crop_detector.extract_json_from_text") as mock_extract:
                mock_extract.return_value = [
                    {"type": "chart", "label": "Q2 chart", "bbox": {"x": 0.2, "y": 0.3, "w": 0.4, "h": 0.2}},
                ]

                settings = MagicMock()
                settings.glm_ocr_model = "glm-ocr:latest"
                settings.ollama_base_url = "http://localhost:11434"
                settings.anthropic_api_key = "test-key"
                settings.default_annotation_provider = "anthropic"
                settings.default_annotation_model = "claude-sonnet-4-6"

                result = await detect_layout(page_images_data, settings)

    assert 0 in result
    assert result[0][0].type == "chart"
    anthropic_provider.complete_vision.assert_awaited_once()
