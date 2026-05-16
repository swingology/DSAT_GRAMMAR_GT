"""PDF extraction using pymupdf (fitz).

Extracts text, embedded images, and a full-page render for each page. The
full-page render is used by OCR/layout enrichment for charts, tables, figures,
and vector graphics that may not appear as embedded image objects.
"""
import base64
import fitz  # pymupdf


def _render_page_b64(page) -> str:
    mat = fitz.Matrix(2.0, 2.0)  # 2x scale, about 144 DPI
    pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
    return base64.standard_b64encode(pix.tobytes("png")).decode("utf-8")


def parse_pdf(path: str, max_pages: int = 100) -> dict:
    """Extract text and images from a PDF file.
    Returns pages with text, embedded images, and one full-page render.
    """
    doc = fitz.open(str(path))
    if len(doc) > max_pages:
        doc.close()
        raise ValueError(f"PDF has {len(doc)} pages; limit is {max_pages}")
    pages = []
    for page_num, page in enumerate(doc):
        text = page.get_text("text")
        images = []
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            if base_image:
                img_b64 = base64.standard_b64encode(base_image["image"]).decode("utf-8")
                images.append({"index": img_index, "b64": img_b64, "ext": base_image.get("ext", "png")})
        page_render = {"index": 0, "b64": _render_page_b64(page), "ext": "png", "rendered": True}
        # Backward compatibility for scanned pages: expose the render in images
        # when there are no embedded images for the OCR gate.
        if not text.strip() and not images:
            images.append(page_render)
        pages.append({
            "page_number": page_num,
            "text": text,
            "images": images,
            "render": page_render,
        })
    doc.close()
    return {"pages": pages, "source": str(path)}
