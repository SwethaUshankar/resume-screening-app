import os
import streamlit as st
from pdf_reader import extract_text_from_pdf
from skill_matcher import compare_skills
from agents import run_screening_pipeline, score_jobs_against_resume
from job_search import fetch_linkedin_jobs, TIME_FILTERS

# Title of the web app
st.title("Resume Screening App")

# Sidebar: settings and API keys
st.sidebar.header("Settings")

openai_key = os.getenv("OPENAI_API_KEY") or st.sidebar.text_input(
    "OpenAI API Key", type="password",
    help="Get one at platform.openai.com"
)

apify_token = os.getenv("APIFY_TOKEN") or st.sidebar.text_input(
    "Apify API Token", type="password",
    help="Free at apify.com -> Settings -> API tokens. Needed for LinkedIn job search."
)

# Resume upload is shared by both tabs
uploaded_resume = st.file_uploader("Upload Resume PDF", type=["pdf"])

# Two tabs: screen one resume vs one JD, or search live jobs
tab_screen, tab_jobs = st.tabs(["Resume Screening", "LinkedIn Job Search"])


# ---------------- TAB 1: Resume vs Job Description ----------------
with tab_screen:
    st.write("Paste a job description to screen the uploaded resume against it.")

    mode = st.radio("Screening Mode", ["AI Agents (OpenAI)", "Basic Keyword Match"], horizontal=True)
    job_description = st.text_area("Paste Job Description Here")

    if st.button("Screen Resume"):
        if uploaded_resume is None:
            st.warning("Please upload a resume PDF.")
        elif job_description.strip() == "":
            st.warning("Please paste the job description.")
        elif mode == "AI Agents (OpenAI)" and not openai_key:
            st.warning("Please enter your OpenAI API key in the sidebar.")
        else:
            resume_text = extract_text_from_pdf(uploaded_resume)

            if mode == "AI Agents (OpenAI)":
                status = st.status("Running AI screening pipeline...", expanded=True)
                try:
                    results = run_screening_pipeline(
                        openai_key, resume_text, job_description,
                        on_step=lambda msg: status.write(msg),
                    )
                    status.update(label="Screening complete!", state="complete", expanded=False)

                    match = results["match_result"]
                    report = results["report"]

                    st.write("## Screening Report")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Match Score", f"{match['match_percentage']:.0f}%")
                    col2.metric("Recommendation", report["recommendation"])
                    col3.metric("Experience Fit", match["experience_fit"].title())

                    st.info(match["reasoning"])
                    st.markdown(report["report"])

                    with st.expander("Matched / Missing Skills"):
                        st.write("**Matched:**", ", ".join(match["matched_skills"]) or "None")
                        st.write("**Missing:**", ", ".join(match["missing_skills"]) or "None")
                        st.write("**Bonus:**", ", ".join(match["bonus_skills"]) or "None")

                    with st.expander("Parsed Resume Details"):
                        st.json(results["parsed_resume"])

                    with st.expander("Job Requirements Extracted"):
                        st.json(results["analyzed_jd"])
                except Exception as e:
                    status.update(label="Screening failed", state="error")
                    st.error(f"Something went wrong: {e}")
            else:
                # Original keyword matching (no AI)
                resume_skills, jd_skills, matched_skills, missing_skills, match_percentage = compare_skills(resume_text, job_description)

                st.write("## Screening Report")
                st.metric("Match Percentage", f"{match_percentage:.2f}%")

                if match_percentage >= 75:
                    st.success("Strong match for this job description.")
                elif match_percentage >= 50:
                    st.info("Moderate match. The resume has some important skills, but can be improved.")
                else:
                    st.warning("Low match. The resume is missing many skills from the job description.")

                st.write("### Matched Skills")
                st.write("\n".join(f"- {s}" for s in matched_skills) or "No matched skills found.")
                st.write("### Missing Skills")
                st.write("\n".join(f"- {s}" for s in missing_skills) or "No missing skills found.")
                st.write("### Resume Skills Found")
                st.write("\n".join(f"- {s}" for s in resume_skills) or "No skills found in resume.")
                st.write("### Job Description Skills Found")
                st.write("\n".join(f"- {s}" for s in jd_skills) or "No skills found in job description.")


# ---------------- TAB 2: Live LinkedIn Job Search + ATS Scores ----------------
with tab_jobs:
    st.write("Find recently posted LinkedIn jobs and see your ATS score for each.")

    keywords_input = st.text_input(
        "Job titles / keywords (comma separated)",
        value="AI Engineer, Machine Learning Engineer",
    )
    location = st.text_input("Location", value="United States")

    col1, col2 = st.columns(2)
    time_label = col1.selectbox("Posted within", list(TIME_FILTERS.keys()))
    num_to_score = col2.slider("Jobs to ATS-score", 5, 25, 10,
                               help="More jobs = slower and slightly more API cost")

    if st.button("Find & Score Jobs"):
        if uploaded_resume is None:
            st.warning("Please upload a resume PDF (top of page).")
        elif not apify_token:
            st.warning("Please enter your Apify token in the sidebar.")
        elif not openai_key:
            st.warning("Please enter your OpenAI API key in the sidebar.")
        else:
            resume_text = extract_text_from_pdf(uploaded_resume)
            keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]

            # Step 1: fetch fresh jobs from LinkedIn (via Apify)
            with st.spinner(f"Searching LinkedIn jobs posted in: {time_label.lower()}..."):
                try:
                    jobs = fetch_linkedin_jobs(apify_token, keywords, location, time_label)
                except Exception as e:
                    st.error(f"Job search failed: {e}")
                    jobs = []

            # Keep only jobs that actually have a description to score
            jobs = [j for j in jobs if j["description"]]

            if not jobs:
                st.info("No jobs found. Try a wider time window or broader keywords.")
            else:
                st.success(f"Found {len(jobs)} jobs. Scoring top {min(num_to_score, len(jobs))} against your resume...")

                # Step 2: ATS-score each job with the AI agent
                progress = st.progress(0.0)
                scored = score_jobs_against_resume(
                    openai_key, resume_text, jobs[:num_to_score],
                    on_progress=lambda i, total: progress.progress(i / total),
                )
                progress.empty()

                # Step 3: show results, best matches first
                st.write("## Results (best match first)")
                for job in scored:
                    score = job["ats_score"]
                    icon = "🟢" if score >= 70 else "🟡" if score >= 50 else "🔴"

                    with st.expander(f"{icon} {score:.0f}% — {job['title']} @ {job['company']}"):
                        st.write(f"**Location:** {job['location']}  |  **Posted:** {job['posted']}")
                        st.write(f"**Verdict:** {job['verdict']}")
                        st.write("**Matched keywords:**", ", ".join(job["matched_keywords"]) or "None")
                        st.write("**Missing keywords:**", ", ".join(job["missing_keywords"]) or "None")
                        st.info(f"Tip: {job['quick_tip']}")
                        if job["url"]:
                            st.link_button("View on LinkedIn", job["url"])
