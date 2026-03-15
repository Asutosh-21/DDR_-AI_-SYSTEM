import json
from config import EXTRACTED_DIR

# Inspection PDF: photos are embedded in content pages (not appendix)
# Page 3  → Area 1 (Hall) + Area 2 (Bedroom) — 14 images
# Page 4  → Area 3 (Master Bedroom) + Area 4 (Kitchen) — 10 images
# Page 5  → Area 4 (Kitchen cont.) + Area 5 (Master Bedroom Wall/External) — 7 images
# Page 6  → Area 6 (Parking) + Area 7 (Common Bathroom) — 8 images
# Page 9  → Checklist/WC — 1 image
# Page 20 → Summary — 1 image
INSPECTION_AREA_PAGE_MAP = {
    "hall":            [3],
    "bedroom":         [3, 4],
    "master bedroom":  [4, 5],
    "kitchen":         [4, 5],
    "external wall":   [5],
    "parking":         [6],
    "common bathroom": [6],
    "wc":              [9],
}

# Thermal PDF: 30 pages, 1 real thermal image per page (after dedup)
# Grouped evenly across 7 areas
THERMAL_AREA_PAGE_MAP = {
    "hall":            list(range(1, 5)),
    "bedroom":         list(range(5, 9)),
    "master bedroom":  list(range(9, 14)),
    "kitchen":         list(range(13, 17)),
    "external wall":   list(range(17, 20)),
    "parking":         list(range(20, 25)),
    "common bathroom": list(range(25, 31)),
}


def best_match(area_name, mapping):
    """Return pages for the best matching key in mapping."""
    area_lower = area_name.lower()
    # Longest key match first (most specific)
    for key in sorted(mapping.keys(), key=len, reverse=True):
        if key in area_lower:
            return mapping[key]
    # Word-level fallback
    for key in sorted(mapping.keys(), key=len, reverse=True):
        if any(word in area_lower for word in key.split()):
            return mapping[key]
    return []


def map_images_to_sections(ddr, extracted_data):
    """Assign inspection + thermal images to each area_wise_observation."""
    insp_images = extracted_data["inspection"]["images"]
    thermal_images = extracted_data["thermal"]["images"]

    # Build page → images lookup for fast access
    insp_by_page = {}
    for img in insp_images:
        insp_by_page.setdefault(img["page"], []).append(img["path"])

    thermal_by_page = {}
    for img in thermal_images:
        thermal_by_page.setdefault(img["page"], []).append(img["path"])

    for obs in ddr.get("area_wise_observations", []):
        area = obs["area"]

        # Inspection images — up to 4 per area
        insp_pages = best_match(area, INSPECTION_AREA_PAGE_MAP)
        insp_imgs = []
        for pg in insp_pages:
            insp_imgs.extend(insp_by_page.get(pg, []))
        obs["inspection_images"] = insp_imgs[:4]

        # Thermal images — up to 2 per area
        thermal_pages = best_match(area, THERMAL_AREA_PAGE_MAP)
        thermal_imgs = []
        for pg in thermal_pages:
            thermal_imgs.extend(thermal_by_page.get(pg, []))
        obs["thermal_images"] = thermal_imgs[:2]

    with open(f"{EXTRACTED_DIR}/ddr_with_images.json", "w", encoding="utf-8") as f:
        json.dump(ddr, f, indent=2, ensure_ascii=False)

    print("Images mapped to DDR sections.")
    return ddr


if __name__ == "__main__":
    with open(f"{EXTRACTED_DIR}/ddr_structured.json", "r", encoding="utf-8") as f:
        ddr = json.load(f)
    with open(f"{EXTRACTED_DIR}/extracted_data.json", "r", encoding="utf-8") as f:
        extracted_data = json.load(f)
    map_images_to_sections(ddr, extracted_data)
