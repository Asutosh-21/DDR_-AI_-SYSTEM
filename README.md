# DDR AI System — Detailed Diagnostic Report Generator Assignment Project

An AI-powered pipeline that reads raw building inspection documents and thermal imaging reports, then generates a structured, client-ready **Detailed Diagnostic Report (DDR)** — complete with inline images, severity assessment, and recommended actions.

---

## What It Does

| Input | Output |
|---|---|
| Inspection Report (PDF) | Structured DDR Report (DOCX) |
| Thermal Images Report (PDF) | Interactive Web UI (Streamlit) |

The system extracts text and images from both documents, merges them intelligently using **Gemini 2.5 Flash AI**, and produces a professional 7-section DDR report with inspection photos and thermal images placed under the correct area observations.

---

## Project Architecture

```
DDR AI SYSTEM/
├── Data Input/
│   ├── Sample Report.pdf          ← Inspection report (input)
│   └── Thermal Images.pdf         ← Thermal imaging report (input)
│
├── pipeline/
│   ├── parser.py                  ← Stage 1: Extract text + images from PDFs
│   ├── merger.py                  ← Stage 2: Gemini AI → structured DDR JSON
│   ├── image_mapper.py            ← Stage 3: Map images to DDR sections
│   └── report_builder.py          ← Stage 4: Build final DOCX report
│
├── prompts/
│   └── ddr_prompt.txt             ← Gemini instruction prompt
│
├── extracted/                     ← Auto-generated during pipeline run
│   ├── images/                    ← Extracted photos (inspection + thermal)
│   ├── extracted_data.json        ← Raw parsed text + image metadata
│   ├── ddr_structured.json        ← Gemini DDR output (7 sections)
│   └── ddr_with_images.json       ← Final DDR with mapped images
│
├── outputs/
│   └── DDR_Report.docx            ← Final client-ready report
│
├── .env                           ← API key (not committed)
├── app.py                         ← Streamlit web UI
├── config.py                      ← Settings and file paths
├── main.py                        ← CLI entry point
└── requirements.txt               ← Python dependencies
```

---

## Pipeline Flow

```
  Inspection PDF ──┐
                   ├──► [Stage 1] parser.py
  Thermal PDF    ──┘         │
                             │  extracted text + images
                             ▼
                    [Stage 2] merger.py
                         Gemini 2.5 Flash
                             │
                             │  structured DDR JSON (7 sections)
                             ▼
                    [Stage 3] image_mapper.py
                             │
                             │  images assigned to each area section
                             ▼
                    [Stage 4] report_builder.py
                             │
                             ▼
                      DDR_Report.docx
```

### Stage Details

| Stage | File | What it does |
|---|---|---|
| 1 — Parse | `parser.py` | Extracts text per page from both PDFs. For inspection: deduplicates images by xref, filters out icons (<200px). For thermal: picks the largest image per page (actual thermal photo) |
| 2 — Merge | `merger.py` | Compresses input to fit free-tier token limits, sends to Gemini 2.5 Flash, parses strict JSON response into 7 DDR sections |
| 3 — Map | `image_mapper.py` | Matches each DDR area to the correct page range in both PDFs, assigns up to 4 inspection photos + 2 thermal images per section |
| 4 — Build | `report_builder.py` | Writes formatted DOCX with headings, section labels, inline images, bullet lists, and dividers |

---

## DDR Output Structure

The generated report contains all 7 required sections:

```
1. Property Issue Summary
2. Area-wise Observations
   └── Per area: Issue observed | Source/cause | Thermal finding | Photos
3. Probable Root Cause
4. Severity Assessment (Level + Reasoning)
5. Recommended Actions
6. Additional Notes
7. Missing or Unclear Information
```

---

## Tech Stack

| Layer | Tool | Purpose |
|---|---|---|
| PDF Parsing | `PyMuPDF (fitz)` | Text extraction + image extraction from PDFs |
| AI / LLM | `Gemini 2.5 Flash` | Reasoning, merging, structuring DDR JSON |
| Report Generation | `python-docx` | Building formatted DOCX with inline images |
| Image Handling | `Pillow` | Opening and validating extracted images |
| Web UI | `Streamlit` | Interactive demo interface |
| Config | `python-dotenv` | API key management via `.env` |

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/ddr-ai-system.git
cd ddr-ai-system
```

### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```




## Web UI Overview

| Section | Description |
|---|---|
| Sidebar | Upload both PDFs + Generate button |
| Section 1 | Property Issue Summary |
| Section 2 | Area-wise Observations (expandable cards with inline photos) |
| Section 3 | Probable Root Cause |
| Section 4 | Severity badge (Low / Moderate / High / Critical) + reasoning |
| Section 5 | Recommended Actions (numbered green cards) |
| Section 6 | Additional Notes |
| Section 7 | Missing or Unclear Information (orange-bordered cards) |
| Download | One-click DOCX download button |

---



## Limitations

- **Scanned PDFs** (image-only, no text layer) are not supported — requires OCR
- **Thermal image-to-area mapping** is sequential (not GPS or label based) — works well for standard reports
- **Free tier quota** — Gemini free tier has daily limits; if exhausted, wait 24 hours or use a paid key
- **English only** — prompt is in English; non-English reports need prompt translation

---



## License

MIT License 
