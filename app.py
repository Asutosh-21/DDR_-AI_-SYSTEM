import streamlit as st
import sys
import os
import json
import time
import shutil
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="DDR AI System",
    page_icon="🏗️",
    layout="wide"
)

# ── Styles ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.main-title   { font-size:2.2rem; font-weight:700; color:#1F497D; }
.section-head { font-size:1.15rem; font-weight:700; color:#1F497D;
                border-left:4px solid #1F497D; padding-left:10px;
                margin-top:1.5rem; margin-bottom:0.5rem; }
.badge-mod    { background:#fff3cd; color:#856404; padding:5px 14px;
                border-radius:12px; font-weight:700; font-size:1rem; }
.badge-high   { background:#f8d7da; color:#721c24; padding:5px 14px;
                border-radius:12px; font-weight:700; font-size:1rem; }
.badge-low    { background:#d4edda; color:#155724; padding:5px 14px;
                border-radius:12px; font-weight:700; font-size:1rem; }
.badge-crit   { background:#d63031; color:#fff; padding:5px 14px;
                border-radius:12px; font-weight:700; font-size:1rem; }
.missing-item { background:#ffffff; border:1px solid #e0e0e0;
                border-left:4px solid #e67e22; border-radius:6px;
                padding:10px 14px; margin-bottom:8px;
                color:#333333; font-size:0.95rem; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ──────────────────────────────────────────────────────────────────
def severity_badge(level):
    cls = {"moderate": "badge-mod", "high": "badge-high",
           "low": "badge-low", "critical": "badge-crit"}.get(level.lower(), "badge-mod")
    return f'<span class="{cls}">⚠ {level}</span>'


def load_images(paths, max_imgs=4):
    imgs = []
    for p in (paths or []):
        if p and os.path.exists(p):
            try:
                imgs.append(Image.open(p))
                if len(imgs) >= max_imgs:
                    break
            except Exception:
                pass
    return imgs


def run_pipeline(insp_path, thermal_path):
    from config import GEMINI_API_KEY
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        st.error("❌ GEMINI_API_KEY not set in .env file.")
        return None

    # Save uploaded files temporarily
    os.makedirs("Data Input", exist_ok=True)
    with open("Data Input/Sample Report.pdf", "wb") as f:
        f.write(insp_path.read())
    with open("Data Input/Thermal Images.pdf", "wb") as f:
        f.write(thermal_path.read())

    # Clear previous extracted data
    if os.path.exists("extracted"):
        shutil.rmtree("extracted")
    os.makedirs("extracted/images", exist_ok=True)

    progress = st.progress(0, text="Stage 1/4 — Parsing documents...")
    from pipeline.parser import parse_all
    extracted_data = parse_all()
    progress.progress(25, text="Stage 2/4 — Generating DDR with Gemini AI...")

    from pipeline.merger import generate_ddr
    ddr = generate_ddr(extracted_data)
    progress.progress(60, text="Stage 3/4 — Mapping images to sections...")

    from pipeline.image_mapper import map_images_to_sections
    ddr = map_images_to_sections(ddr, extracted_data)
    progress.progress(80, text="Stage 4/4 — Building DOCX report...")

    from pipeline.report_builder import build_report
    build_report(ddr)
    progress.progress(100, text="✅ Done!")
    time.sleep(0.5)
    progress.empty()
    return ddr


def render_ddr(ddr):
    # ── 1. Property Issue Summary ────────────────────────────────────────────
    st.markdown('<div class="section-head">1. Property Issue Summary</div>', unsafe_allow_html=True)
    st.info(ddr.get("property_issue_summary", "Not Available"))

    # ── 2. Area-wise Observations ────────────────────────────────────────────
    st.markdown('<div class="section-head">2. Area-wise Observations</div>', unsafe_allow_html=True)
    for i, obs in enumerate(ddr.get("area_wise_observations", []), 1):
        with st.expander(f"📍 Area {i}: {obs.get('area', 'Unknown')}", expanded=(i == 1)):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**🔴 Issue Observed (Negative Side)**")
                st.write(obs.get("negative_side", "Not Available"))
                st.markdown("**🟢 Source / Cause Area (Positive Side)**")
                st.write(obs.get("positive_side", "Not Available"))
                st.markdown("**🌡️ Thermal Finding**")
                st.write(obs.get("thermal_finding", "Not Available"))

            with col2:
                insp_imgs = load_images(obs.get("inspection_images", []))
                thermal_imgs = load_images(obs.get("thermal_images", []), max_imgs=2)

                if insp_imgs:
                    st.markdown("**📷 Inspection Photos**")
                    img_cols = st.columns(min(len(insp_imgs), 2))
                    for j, img in enumerate(insp_imgs):
                        img_cols[j % 2].image(img, use_container_width=True)
                else:
                    st.caption("📷 Inspection Photos: Image Not Available")

                if thermal_imgs:
                    st.markdown("**🌡️ Thermal Images**")
                    t_cols = st.columns(min(len(thermal_imgs), 2))
                    for j, img in enumerate(thermal_imgs):
                        t_cols[j % 2].image(img, use_container_width=True)
                else:
                    st.caption("🌡️ Thermal Images: Image Not Available")

    # ── 3. Probable Root Cause ───────────────────────────────────────────────
    st.markdown('<div class="section-head">3. Probable Root Cause</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div style="background:#fff8e1;border-left:4px solid #f39c12;padding:14px 16px;'
        f'border-radius:6px;color:#333;font-size:0.95rem;">{ddr.get("probable_root_cause", "Not Available")}</div>',
        unsafe_allow_html=True
    )

    # ── 4. Severity Assessment ───────────────────────────────────────────────
    st.markdown('<div class="section-head">4. Severity Assessment</div>', unsafe_allow_html=True)
    sev = ddr.get("severity_assessment", {})
    level = sev.get("level", "Not Available")
    reasoning = sev.get("reasoning", "Not Available")
    st.markdown(severity_badge(level), unsafe_allow_html=True)
    st.markdown(
        f'<div style="background:#f9f9f9;border:1px solid #ddd;padding:12px 16px;'
        f'border-radius:6px;color:#333;font-size:0.95rem;margin-top:8px;">{reasoning}</div>',
        unsafe_allow_html=True
    )

    # ── 5. Recommended Actions ───────────────────────────────────────────────
    st.markdown('<div class="section-head">5. Recommended Actions</div>', unsafe_allow_html=True)
    for i, action in enumerate(ddr.get("recommended_actions", ["Not Available"]), 1):
        st.markdown(
            f'<div style="background:#f0fff4;border:1px solid #c3e6cb;border-left:4px solid #28a745;'
            f'padding:10px 14px;border-radius:6px;color:#333;font-size:0.95rem;margin-bottom:6px;">'
            f'<b>{i}.</b> {action}</div>',
            unsafe_allow_html=True
        )

    # ── 6. Additional Notes ──────────────────────────────────────────────────
    st.markdown('<div class="section-head">6. Additional Notes</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div style="background:#f8f9fa;border:1px solid #dee2e6;padding:14px 16px;'
        f'border-radius:6px;color:#333;font-size:0.95rem;">{ddr.get("additional_notes", "Not Available")}</div>',
        unsafe_allow_html=True
    )

    # ── 7. Missing / Unclear Info ────────────────────────────────────────────
    st.markdown('<div class="section-head">7. Missing or Unclear Information</div>', unsafe_allow_html=True)
    missing = ddr.get("missing_or_unclear_info", [])
    if missing:
        for item in missing:
            st.markdown(
                f'<div class="missing-item">⚠️ &nbsp;{item}</div>',
                unsafe_allow_html=True
            )
    else:
        st.markdown(
            '<div class="missing-item">✅ &nbsp;No missing or unclear information identified.</div>',
            unsafe_allow_html=True
        )

    # ── Download Button ──────────────────────────────────────────────────────
    st.markdown("---")
    docx_path = "outputs/DDR_Report.docx"
    if os.path.exists(docx_path):
        with open(docx_path, "rb") as f:
            st.download_button(
                label="⬇️ Download DDR Report (.docx)",
                data=f,
                file_name="DDR_Report.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )


# ── Main App ─────────────────────────────────────────────────────────────────
def main():
    st.markdown('<div class="main-title">🏗️ DDR AI System</div>', unsafe_allow_html=True)
    st.markdown("**Detailed Diagnostic Report Generator** — Upload inspection documents and get a structured AI-generated report.")
    st.markdown("---")

    # Sidebar
    with st.sidebar:
        st.header("📂 Upload Documents")
        insp_file = st.file_uploader("Inspection Report (PDF)", type=["pdf"], key="insp")
        thermal_file = st.file_uploader("Thermal Images Report (PDF)", type=["pdf"], key="thermal")

        st.markdown("---")
        st.markdown("**How it works:**")
        st.markdown("""
1. 📄 Parse both PDFs (text + images)
2. 🤖 Gemini AI structures the DDR
3. 🖼️ Images mapped to sections
4. 📝 DOCX report generated
        """)

        generate_btn = st.button("🚀 Generate DDR Report", use_container_width=True,
                                  type="primary", disabled=not (insp_file and thermal_file))

    # Load existing DDR if available, or run pipeline
    ddr_path = "extracted/ddr_with_images.json"

    if generate_btn and insp_file and thermal_file:
        with st.spinner("Running AI pipeline..."):
            ddr = run_pipeline(insp_file, thermal_file)
        if ddr:
            st.success("✅ DDR Report generated successfully!")
            render_ddr(ddr)

    elif os.path.exists(ddr_path):
        st.info("📋 Showing last generated report. Upload new documents and click Generate to refresh.")
        with open(ddr_path, "r", encoding="utf-8") as f:
            ddr = json.load(f)
        render_ddr(ddr)

    else:
        st.markdown("""
        <div style='text-align:center; padding:60px; color:#888;'>
            <h3>👈 Upload both PDF documents in the sidebar to get started</h3>
            <p>Inspection Report + Thermal Images Report → AI-generated DDR</p>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
