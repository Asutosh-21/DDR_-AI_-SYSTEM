import fitz
import os
import json
from config import INSPECTION_PDF, THERMAL_PDF, EXTRACTED_DIR, IMAGES_DIR


def extract_pdf(pdf_path, doc_type):
    """Extract text per page and meaningful images from a PDF."""
    doc = fitz.open(pdf_path)
    pages_text = []
    images_meta = []

    os.makedirs(IMAGES_DIR, exist_ok=True)

    # For thermal PDFs: extract the single best image per page (no xref dedup)
    # For inspection PDFs: deduplicate by xref to avoid repeated embedded images
    is_thermal = (doc_type == "thermal")
    saved_xrefs = set()

    for page_num, page in enumerate(doc):
        text = page.get_text().strip()
        if text:
            pages_text.append({"page": page_num + 1, "text": text})

        page_imgs = page.get_images(full=True)

        if is_thermal:
            # Use get_image_info() — returns only images actually rendered on this page.
            # The thermal PDF embeds all 180 xrefs at document level (shared across all pages),
            # so get_images() returns 180 per page. get_image_info() returns only the ~6
            # actually placed on this page.
            # Each page has 2 JPEGs: thermal heatmap (top, lower Y) + visible light (bottom).
            # Pick the JPEG with the smallest bbox Y (topmost) = the thermal heatmap.
            rendered = page.get_image_info(xrefs=True)
            best = None
            best_y = float('inf')
            for item in rendered:
                xref = item.get("xref", 0)
                if not xref:
                    continue
                try:
                    base_image = doc.extract_image(xref)
                    ext = base_image.get("ext", "").lower()
                    w, h = base_image.get("width", 0), base_image.get("height", 0)
                    bbox_y = item.get("bbox", (0, float('inf')))[1]
                    if ext in ("jpeg", "jpg") and w > 200 and h > 200 and bbox_y < best_y:
                        best_y = bbox_y
                        best = (xref, base_image, w, h)
                except Exception:
                    continue
            if best:
                xref, base_image, w, h = best
                ext = base_image["ext"]
                img_filename = f"{doc_type}_p{page_num+1}_best.{ext}"
                img_path = os.path.join(IMAGES_DIR, img_filename)
                with open(img_path, "wb") as f:
                    f.write(base_image["image"])
                images_meta.append({
                    "page": page_num + 1,
                    "index": 0,
                    "path": img_path,
                    "width": w,
                    "height": h,
                    "doc_type": doc_type
                })
        else:
            # Inspection: extract all meaningful images, deduplicate by xref
            for img_index, img in enumerate(page_imgs):
                xref = img[0]
                if xref in saved_xrefs:
                    continue
                try:
                    base_image = doc.extract_image(xref)
                    w, h = base_image.get("width", 0), base_image.get("height", 0)
                    if w < 200 or h < 200:
                        continue
                    saved_xrefs.add(xref)
                    ext = base_image["ext"]
                    img_filename = f"{doc_type}_p{page_num+1}_{img_index}.{ext}"
                    img_path = os.path.join(IMAGES_DIR, img_filename)
                    with open(img_path, "wb") as f:
                        f.write(base_image["image"])
                    images_meta.append({
                        "page": page_num + 1,
                        "index": img_index,
                        "path": img_path,
                        "width": w,
                        "height": h,
                        "doc_type": doc_type
                    })
                except Exception:
                    continue

    doc.close()
    return pages_text, images_meta


def parse_all():
    """Parse both PDFs and save extracted data."""
    os.makedirs(EXTRACTED_DIR, exist_ok=True)

    print("Parsing Inspection Report...")
    insp_text, insp_images = extract_pdf(INSPECTION_PDF, "inspection")

    print("Parsing Thermal Report...")
    thermal_text, thermal_images = extract_pdf(THERMAL_PDF, "thermal")

    data = {
        "inspection": {"pages": insp_text, "images": insp_images},
        "thermal": {"pages": thermal_text, "images": thermal_images}
    }

    with open(f"{EXTRACTED_DIR}/extracted_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Extracted {len(insp_images)} inspection images, {len(thermal_images)} thermal images.")
    return data


if __name__ == "__main__":
    parse_all()
