import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"  # free tier model

INSPECTION_PDF = "Data Input/Sample Report.pdf"
THERMAL_PDF = "Data Input/Thermal Images.pdf"

EXTRACTED_DIR = "extracted"
IMAGES_DIR = "extracted/images"
OUTPUT_DIR = "outputs"
OUTPUT_DOCX = "outputs/DDR_Report.docx"
