import json
import re
import time
from google import genai
from config import GEMINI_API_KEY, GEMINI_MODEL, EXTRACTED_DIR


def load_prompt():
    with open("prompts/ddr_prompt.txt", "r", encoding="utf-8") as f:
        return f.read()


def compress_inspection_text(pages):
    """Extract only the meaningful content pages, skip appendix photo-only pages."""
    meaningful = []
    for p in pages:
        text = p["text"].strip()
        # Skip pages that are only photo labels (e.g. "Photo 1\nPhoto 2\n...")
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        non_photo_lines = [l for l in lines if not re.match(r'^Photo\s+\d+$', l)]
        if len(non_photo_lines) >= 3:
            meaningful.append(f"[Page {p['page']}]\n" + "\n".join(non_photo_lines))
    return "\n\n".join(meaningful)


def compress_thermal_text(pages):
    """Summarize thermal readings: extract hotspot, coldspot, image name per page."""
    summaries = []
    for p in pages:
        text = p["text"]
        hotspot = re.search(r'Hotspot\s*:\s*([\d.]+\s*[°ｰ]C)', text)
        coldspot = re.search(r'Coldspot\s*:\s*([\d.]+\s*[°ｰ]C)', text)
        img = re.search(r'Thermal image\s*:\s*(\S+)', text)
        page_num = p["page"]
        h = hotspot.group(1) if hotspot else "N/A"
        c = coldspot.group(1) if coldspot else "N/A"
        i = img.group(1) if img else "N/A"
        summaries.append(f"Thermal #{page_num}: Hotspot={h}, Coldspot={c}, File={i}")
    return "\n".join(summaries)


def call_gemini_with_retry(user_message, retries=3, wait=15):
    client = genai.Client(api_key=GEMINI_API_KEY)
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=user_message
            )
            return response.text
        except Exception as e:
            err = str(e)
            if "429" in err and attempt < retries - 1:
                print(f"  Rate limit hit. Waiting {wait}s before retry {attempt+2}/{retries}...")
                time.sleep(wait)
                wait *= 2  # exponential backoff
            else:
                raise


def call_gemini(inspection_text, thermal_text):
    system_prompt = load_prompt()
    user_message = f"""{system_prompt}

--- INSPECTION REPORT TEXT ---
{inspection_text}

--- THERMAL REPORT SUMMARY (30 readings) ---
{thermal_text}

Generate the DDR JSON now."""

    return call_gemini_with_retry(user_message)


def parse_json_response(raw_text):
    cleaned = re.sub(r"```(?:json)?", "", raw_text).strip().rstrip("`").strip()
    return json.loads(cleaned)


def generate_ddr(data):
    print("Compressing input data for free tier token limits...")
    inspection_text = compress_inspection_text(data["inspection"]["pages"])
    thermal_text = compress_thermal_text(data["thermal"]["pages"])

    print(f"  Inspection text: {len(inspection_text)} chars")
    print(f"  Thermal summary: {len(thermal_text)} chars")

    print("Sending data to Gemini...")
    raw_response = call_gemini(inspection_text, thermal_text)

    ddr = parse_json_response(raw_response)

    with open(f"{EXTRACTED_DIR}/ddr_structured.json", "w", encoding="utf-8") as f:
        json.dump(ddr, f, indent=2, ensure_ascii=False)

    print("DDR JSON generated successfully.")
    return ddr


if __name__ == "__main__":
    with open(f"{EXTRACTED_DIR}/extracted_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    generate_ddr(data)
