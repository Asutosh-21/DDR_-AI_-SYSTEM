import sys
import os

# Add project root to path so pipeline modules can import config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline.parser import parse_all
from pipeline.merger import generate_ddr
from pipeline.image_mapper import map_images_to_sections
from pipeline.report_builder import build_report
from config import GEMINI_API_KEY


def main():
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        print("ERROR: Please set your GEMINI_API_KEY in the .env file.")
        return

    print("=" * 50)
    print("  DDR AI SYSTEM - Report Generation Pipeline")
    print("=" * 50)

    # Stage 1: Parse both PDFs
    print("\n[1/4] Parsing input documents...")
    extracted_data = parse_all()

    # Stage 2: Generate structured DDR via Gemini
    print("\n[2/4] Generating DDR structure with Gemini AI...")
    ddr = generate_ddr(extracted_data)

    # Stage 3: Map images to DDR sections
    print("\n[3/4] Mapping images to report sections...")
    ddr_with_images = map_images_to_sections(ddr, extracted_data)

    # Stage 4: Build final DOCX report
    print("\n[4/4] Building final DDR report...")
    build_report(ddr_with_images)

    print("\n" + "=" * 50)
    print("  Done! Report saved to: outputs/DDR_Report.docx")
    print("=" * 50)


if __name__ == "__main__":
    main()
