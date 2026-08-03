"""Layout detection, region matching, and image cropping for page-level provenance.

This module provides the enrichment step that runs after OCR text extraction:
1. detect_layout — sends each page render to GLM-OCR with a layout prompt,
   returns structured RegionDetection lists per page.
2. match_region_for_question — picks the best question_block region for a
   given extracted question.
3. crop_and_store — crops a region from a page render image using Pillow and
   stores the result via the object-store adapter.

All functions degrade gracefully — failures return empty results, never raise.
"""

from __future__ import annotations

import io
import logging
import re
import uuid
from dataclasses import dataclass, asdict

from PIL import Image

from app.config import get_settings
from app.parsers.json_parser import extract_json_from_text
from app.prompts.layout_prompt import build_layout_prompt
from app.storage.object_store import put_object, read_object

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RegionDetection:
    type: str            # question_block | table | chart | figure
    label: str           # "Q3", "Table 1", ...
    page_index: int      # index into _page_images list
    bbox: dict           # {"x": float, "y": float, "w": float, "h": float}
    question_number: int | None  # parsed from label, e.g. "Q3" -> 3


@dataclass(frozen=True)
class CropResult:
    region: RegionDetection
    storage_path: str


def _parse_question_number(label: str) -> int | None:
    """Extract a question number from a region label like 'Q3', 'Question 7', '3'."""
    m = re.search(r"(\d+)", label)
    return int(m.group(1)) if m else None


def _parse_explicit_question_ref(label: str) -> int | None:
    """Extract only explicit question references, avoiding labels like "Table 1"."""
    m = re.search(r"\b(?:q|question)\s*#?\s*(\d+)\b", label or "", flags=re.IGNORECASE)
    return int(m.group(1)) if m else None


def _clamp_bbox(bbox: dict) -> dict:
    """Clamp normalized bbox values to [0, 1] and ensure w/h > 0."""
    return {
        "x": max(0.0, min(1.0, float(bbox.get("x", 0)))),
        "y": max(0.0, min(1.0, float(bbox.get("y", 0)))),
        "w": max(0.0, min(1.0, float(bbox.get("w", 0)))),
        "h": max(0.0, min(1.0, float(bbox.get("h", 0)))),
    }


def _is_valid_bbox(bbox: dict) -> bool:
    """Return True if bbox has meaningful area after clamping."""
    clamped = _clamp_bbox(bbox)
    return clamped["w"] > 0.005 and clamped["h"] > 0.005


def _parse_region_list(raw: list[dict], page_index: int) -> list[RegionDetection]:
    """Parse a list of region dicts from GLM-OCR output into RegionDetection objects."""
    regions: list[RegionDetection] = []
    valid_types = {"question_block", "table", "chart", "figure"}
    for item in raw:
        rtype = (item.get("type") or "").strip().lower()
        if rtype not in valid_types:
            # Accept common synonyms
            if "question" in rtype:
                rtype = "question_block"
            elif "table" in rtype:
                rtype = "table"
            elif "chart" in rtype or "graph" in rtype:
                rtype = "chart"
            elif "figure" in rtype or "image" in rtype or "diagram" in rtype:
                rtype = "figure"
            else:
                continue
        label = str(item.get("label", "")).strip()
        bbox = item.get("bbox")
        if not isinstance(bbox, dict):
            continue
        if not _is_valid_bbox(bbox):
            continue
        regions.append(RegionDetection(
            type=rtype,
            label=label or f"{rtype}_{page_index}",
            page_index=page_index,
            bbox=_clamp_bbox(bbox),
            question_number=_parse_question_number(label),
        ))
    return regions


async def detect_layout(
    page_images_data: list[dict],
    settings,
) -> dict[int, list[RegionDetection]]:
    """Send each page render to a vision model with the layout detection prompt.

    Returns {page_index: [RegionDetection, ...]}.
    Returns {} on any failure (graceful degradation — never raises).
    """
    from app.llm.ollama_provider import OllamaProvider
    from app.llm.base import ImageContent
    from app.llm.factory import get_provider, resolve_base_url
    import base64

    attempts = []
    glm_model = getattr(settings, "glm_ocr_model", "")
    if glm_model:
        attempts.append((
            "ollama",
            glm_model,
            OllamaProvider(
                base_url=settings.ollama_base_url,
                default_model=glm_model,
            ),
            True,
        ))

    anthropic_api_key = getattr(settings, "anthropic_api_key", "")
    if isinstance(anthropic_api_key, str) and anthropic_api_key:
        default_provider = getattr(settings, "default_annotation_provider", "")
        default_model = getattr(settings, "default_annotation_model", "")
        model = default_model if default_provider == "anthropic" and default_model else "claude-sonnet-4-6"
        attempts.append((
            "anthropic",
            model,
            get_provider(
                "anthropic",
                api_key=anthropic_api_key,
                base_url=resolve_base_url("anthropic", settings),
                default_model=model,
            ),
            False,
        ))

    if not attempts:
        return {}

    layout_data: dict[int, list[RegionDetection]] = {}

    try:
        for page_index, img_entry in enumerate(page_images_data):
            # Reconstruct page image — same fallback logic as _collect_page_images
            mime = img_entry.get("mime_type", "image/png")
            page_bytes: bytes | None = None

            if img_entry.get("path"):
                try:
                    from pathlib import Path
                    page_bytes = Path(img_entry["path"]).read_bytes()
                except (OSError, FileNotFoundError):
                    page_bytes = None

            if page_bytes is None and img_entry.get("storage_path"):
                try:
                    page_bytes = read_object(img_entry["storage_path"])
                except (OSError, FileNotFoundError, NotImplementedError):
                    page_bytes = None

            if page_bytes is None and img_entry.get("b64"):
                try:
                    page_bytes = base64.b64decode(img_entry["b64"])
                except Exception:
                    page_bytes = None

            if not page_bytes:
                logger.warning("detect_layout: could not load page %d image, skipping", page_index)
                continue

            b64 = base64.standard_b64encode(page_bytes).decode("utf-8")
            image_content = ImageContent(b64=b64, mime_type=mime)

            system, user = build_layout_prompt(
                img_entry.get("source_metadata") if isinstance(img_entry.get("source_metadata"), dict) else None
            )

            for provider_name, model, provider, _close_after in attempts:
                try:
                    result = await provider.complete_vision(
                        system=system,
                        user=user,
                        images=[image_content],
                        model=model,
                        max_tokens=4096,
                        temperature=0.0,
                    )

                    parsed = extract_json_from_text(result.raw_text, provider_name, model)
                    if isinstance(parsed, dict) and "regions" in parsed:
                        region_list = parsed["regions"]
                    elif isinstance(parsed, list):
                        region_list = parsed
                    else:
                        region_list = []

                    regions = _parse_region_list(region_list, page_index)
                    if regions:
                        layout_data[page_index] = regions
                        break
                except Exception as exc:
                    logger.warning(
                        "detect_layout: %s layout call failed for page %d: %s",
                        provider_name,
                        page_index,
                        exc,
                    )
    finally:
        for _provider_name, _model, provider, close_after in attempts:
            if close_after and hasattr(provider, "close"):
                await provider.close()

    return layout_data


def match_stimulus_regions_for_question(
    layout_data: dict[int, list[RegionDetection]],
    matched_question_region: RegionDetection | None,
) -> list[RegionDetection]:
    """Return table/chart/figure regions that likely belong to one question.

    The previous implementation returned every stimulus on the same page, which
    over-linked all page-level visuals to each question on that page. Prefer an
    explicit Q label if present, otherwise use conservative spatial proximity.
    """
    if matched_question_region is None:
        return []
    stimulus_types = {"table", "chart", "figure"}
    same_page = [
        r for r in layout_data.get(matched_question_region.page_index, [])
        if r.type in stimulus_types
    ]
    if not same_page:
        return []

    q_ref = matched_question_region.question_number or _parse_explicit_question_ref(matched_question_region.label)
    explicit_matches = [
        r for r in same_page
        if q_ref is not None and _parse_explicit_question_ref(r.label) == q_ref
    ]
    if explicit_matches:
        return explicit_matches

    q = matched_question_region.bbox
    q_left = q["x"]
    q_right = q["x"] + q["w"]
    q_top = q["y"]
    q_bottom = q["y"] + q["h"]
    q_center_x = q["x"] + q["w"] / 2

    matched: list[RegionDetection] = []
    for r in same_page:
        b = r.bbox
        r_left = b["x"]
        r_right = b["x"] + b["w"]
        r_top = b["y"]
        r_bottom = b["y"] + b["h"]
        r_center_x = b["x"] + b["w"] / 2

        horizontal_overlap = max(0.0, min(q_right, r_right) - max(q_left, r_left))
        horizontal_ratio = horizontal_overlap / max(0.001, min(q["w"], b["w"]))
        center_aligned = abs(r_center_x - q_center_x) <= max(q["w"], b["w"]) * 0.55
        vertical_overlap = max(0.0, min(q_bottom, r_bottom) - max(q_top, r_top))
        near_below = 0 <= r_top - q_bottom <= 0.08
        near_above = 0 <= q_top - r_bottom <= 0.04

        if (vertical_overlap > 0 or near_below or near_above) and (horizontal_ratio >= 0.25 or center_aligned):
            matched.append(r)

    return matched


def match_region_for_question(
    layout_data: dict[int, list[RegionDetection]],
    q_data: dict,
    question_index: int,
) -> RegionDetection | None:
    """Pick the best question_block region for one question.

    Match priority:
    1. RegionDetection.question_number == q_data['source_question_number']
    2. Same page index AND positional order fallback
    3. None if no confident match
    """
    q_num = q_data.get("source_question_number")
    if q_num is not None:
        try:
            q_num = int(q_num)
        except (TypeError, ValueError):
            q_num = None

    # Collect all question_block regions
    all_blocks: list[RegionDetection] = []
    for regions in layout_data.values():
        for r in regions:
            if r.type == "question_block":
                all_blocks.append(r)

    # Priority 1: match by question number
    if q_num is not None:
        for r in all_blocks:
            if r.question_number == q_num:
                return r

    # Priority 2: match by positional index (question_index -> nth block)
    if question_index < len(all_blocks):
        return all_blocks[question_index]

    return None


def crop_and_store(
    region: RegionDetection,
    page_images_data: list[dict],
    question_id: uuid.UUID,
    kind: str = "question_crop",
) -> CropResult | None:
    """Crop a region from a page render image and store via object_store.

    Returns CropResult on success, None on failure.
    """
    import base64

    if region.page_index >= len(page_images_data):
        return None

    img_entry = page_images_data[region.page_index]
    mime = img_entry.get("mime_type", "image/png")
    page_bytes: bytes | None = None

    if img_entry.get("path"):
        try:
            from pathlib import Path
            page_bytes = Path(img_entry["path"]).read_bytes()
        except (OSError, FileNotFoundError):
            page_bytes = None

    if page_bytes is None and img_entry.get("storage_path"):
        try:
            page_bytes = read_object(img_entry["storage_path"])
        except (OSError, FileNotFoundError, NotImplementedError):
            page_bytes = None

    if page_bytes is None and img_entry.get("b64"):
        try:
            page_bytes = base64.b64decode(img_entry["b64"])
        except Exception:
            page_bytes = None

    if not page_bytes:
        return None

    try:
        img = Image.open(io.BytesIO(page_bytes))
        img_w, img_h = img.size

        # Convert normalized bbox to pixel coordinates
        bbox = region.bbox
        left = int(bbox["x"] * img_w)
        upper = int(bbox["y"] * img_h)
        right = int((bbox["x"] + bbox["w"]) * img_w)
        lower = int((bbox["y"] + bbox["h"]) * img_h)

        # Clamp to image bounds
        left = max(0, min(left, img_w))
        upper = max(0, min(upper, img_h))
        right = max(left, min(right, img_w))
        lower = max(upper, min(lower, img_h))

        if right <= left or lower <= upper:
            logger.warning("crop_and_store: degenerate crop for question %s", question_id)
            return None

        cropped = img.crop((left, upper, right, lower))

        # Re-encode as PNG
        buf = io.BytesIO()
        cropped.save(buf, format="PNG")
        crop_bytes = buf.getvalue()
    except Exception as exc:
        logger.warning("crop_and_store: image crop failed for question %s: %s", question_id, exc)
        return None

    crop_id = uuid.uuid4().hex[:12]
    stored = put_object(
        kind,
        {
            "question_id": question_id,
            "page_number": region.page_index,
            "crop_id": crop_id,
            "ext": "png",
        },
        crop_bytes,
        filename=f"{crop_id}.png",
        mime_type="image/png",
    )

    return CropResult(region=region, storage_path=stored.storage_path)
