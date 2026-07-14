from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from matcher import tailored_summary, match
from ingest import extract_text, resume_to_bullets

st.set_page_config(page_title="Resume ↔ Job Match", page_icon="📄")
st.title("📄 Resume ↔ Job Match")
st.caption("Upload your resume, paste a job description, and see how well you fit - plus a tailored summary.")

resume_file = st.file_uploader("Your resume (PDF)", type=["pdf"])
jd_text = st.text_area("Paste the job description", height=220)

if st.button("Analyze", type="primary"):
    if not resume_file or not jd_text.strip():
        st.warning("Please upload a resume and paste a job description.")
        st.stop()

    with st.spinner("Reading resume, embedding, and matching…"):
        bullets = resume_to_bullets(extract_text(resume_file))
        result = match(bullets, jd_text)
        summary = tailored_summary(result["top_bullets"], jd_text)

    st.metric("Overall coverage", f"{result['overall']:.2f}")

    st.subheader("Requirement-by-requirement")
    rows = [{
        "Requirement": r["requirement"],
        "Your best match": r["best_match"],
        "Score": round(r["score"], 3),
        "Status": "✅ OK" if r["covered"] else "⚠️ GAP",
    } for r in result["requirements"]]
    st.dataframe(rows, use_container_width=True, hide_index=True)

    st.subheader("Lead with these bullets")
    for b in result["top_bullets"]:
        st.write("• ", b)

    st.subheader("Tailored summary")
    st.write(summary)
