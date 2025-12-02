import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import io
import re

st.set_page_config(page_title="Contract Guardian", layout="wide", page_icon="🔍")
st.title("Contract Guardian")
st.markdown("**Upload a contract PDF/photo or paste text → instantly see every hidden trap in plain English.**")
st.markdown("— Built by Daryl Shaw © 2025")

RED_FLAGS = {
    "One-Sided Control": {"patterns": [r"\bsole discretion\b", r"\bat (our|their) sole discretion\b", r"\breserves? the right\b", r"\bmay (modify|change|amend|terminate)\b", r"\bwithout (prior )?notice\b", r"\bat any time\b"], "explanation": "They can change the deal anytime — even after you sign.", "risk": "high"},
    "Auto-Renewal Trap": {"patterns": [r"\bauto[-\s]?renew\b", r"\bautomatic renewal\b", r"\bnon[-\s]?cancellable\b", r"\bearly termination fee\b"], "explanation": "You’re locked in and it’s hard or expensive to get out.", "risk": "high"},
    "No Liability": {"patterns": [r"\bhold harmless\b", r"\bindemnify\b", r"\bno liability\b", r"\blimitation of liability\b", r"\bwaive.*claims?\b"], "explanation": "If they mess up, you can’t sue — even if it’s their fault.", "risk": "critical"},
    "Forced Arbitration": {"patterns": [r"\bbinding arbitration\b", r"\bclass action waiver\b", r"\bwaive.*jury\b"], "explanation": "No real court, no class action. You fight alone.", "risk": "critical"},
    "Hidden Fees": {"patterns": [r"\badditional fees?\b", r"\bvariable.*rate\b", r"\bprice.*increase\b"], "explanation": "They can raise prices or add surprise charges later.", "risk": "high"},
    "No Warranty": {"patterns": [r"\bas[- ]?is\b", r"\bwithout warranty\b", r"\bno guarantee\b"], "explanation": "If it breaks or doesn’t work — you’re on your own.", "risk": "medium"},
    "Vague = They Win": {"patterns": [r"\breasonable\b", r"\bas (we|they) (deem|determine)\b", r"\bin (our|their) judgment\b"], "explanation": "They decide what “reasonable” means. Guess who wins?", "risk": "medium"}
}

tab1, tab2 = st.tabs(["Upload PDF/Image", "Paste Text"])
extracted_text = ""

with tab1:
    uploaded = st.file_uploader("Choose PDF, PNG, JPG", type=["pdf","png","jpg","jpeg"])
    if uploaded:
        with st.spinner("Reading with OCR…"):
            bytes_data = uploaded.read()
            if uploaded.type == "application/pdf":
                images = convert_from_bytes(bytes_data, dpi=200)
                for img in images:
                    extracted_text += pytesseract.image_to_string(img) + "\n"
            else:
                img = Image.open(io.BytesIO(bytes_data))
                extracted_text = pytesseract.image_to_string(img)
        st.success("Text extracted!")

with tab2:
    pasted = st.text_area("Or paste contract text here", height=250)
    if pasted:
        extracted_text = pasted

if extracted_text.strip():
    findings = []
    highlighted = extracted_text
    risk_score = 0
    weights = {"medium":3, "high":6, "critical":10}

    for category, data in RED_FLAGS.items():
        for pattern in data["patterns"]:
            for match in re.finditer(pattern, extracted_text, re.IGNORECASE):
                findings.append({"cat": category, "phrase": match.group(0), "exp": data["explanation"], "risk": data["risk"]})
                highlighted = re.sub(re.escape(match.group(0)), f"**<span style='background-color:#ff9999;padding:2px 5px;border-radius:3px'>{match.group(0)}</span>**", highlighted, flags=re.IGNORECASE)
                risk_score += weights[data["risk"]]

    col1, col2 = st.columns([2,1])
    with col1:
        st.markdown("### Contract with Red Flags Highlighted")
        st.markdown(highlighted, unsafe_allow_html=True)
    with col2:
        st.markdown("### Risk Summary")
        if risk_score == 0:
            st.success("No major red flags found!")
        elif risk_score <= 12:
            st.info(f"Low–Medium Risk ({risk_score} pts)")
        elif risk_score <= 30:
            st.warning(f"High Risk ({risk_score} pts)")
        else:
            st.error(f"Critical Risk – Walk away!")

        st.markdown("### Issues Found")
        for i, f in enumerate(findings, 1):
            emoji = {"medium":"medium","high":"high","critical":"critical"}[f["risk"]]
            st.markdown(f"**{i}. {emoji} {f['cat']}**")
            st.caption(f"“{f['phrase']}”")
            st.write(f["exp"])
            st.markdown("---")

    report = "# Contract Guardian Report\n\n"
    for f in findings:
        report += f"- {f['cat']}: “{f['phrase']}” → {f['exp']}\n"
    st.download_button("Download Report", report, "contract_report.txt")
else:
    st.info("Upload or paste a contract to start scanning")

st.caption("© 2025 Daryl Shaw – Contract Guardian. All rights reserved.")
