"""PDF text extraction using pymupdf (fitz).
Extracts text per page and embedded images as base64 bytes for multimodal LLM processing.
"""
import base64
import fitz  # pymupdf


def parse_pdf(path: str) -> dict:
    """Extract text and images from a PDF file.
    Returns: {"pages": [{"page_number": int, "text": str, "images": [{"index": int, "b64": str}]}]}
    """
    doc = fitz.open(str(path))
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
        # For scanned pages (no text, no embedded images), rasterize the page itself
        if not text.strip() and not images:
            mat = fitz.Matrix(2.0, 2.0)  # 2x scale ≈ 144 DPI
            pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
            img_b64 = base64.standard_b64encode(pix.tobytes("png")).decode("utf-8")
            images.append({"index": 0, "b64": img_b64, "ext": "png", "rendered": True})
        pages.append({
            "page_number": page_num,
            "text": text,
            "images": images,
        })
    doc.close()
    return {"pages": pages, "source": str(path)}