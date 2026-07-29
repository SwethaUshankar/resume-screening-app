import streamlit as st
from pdf_reader import extract_text_from_pdf
from skill_matcher import compare_skills

# Title of the web app
st.title("Resume Screening App")

# Small explanation under the title
st.write("Upload a resume and paste a job description to start screening.")

# Upload box for resume PDF
uploaded_resume = st.file_uploader("Upload Resume PDF", type=["pdf"])

# Text box for job description
job_description = st.text_area("Paste Job Description Here")

# Button to start screening
if st.button("Screen Resume"):

    # If no resume is uploaded
    if uploaded_resume is None:
        st.warning("Please upload a resume PDF.")

    # If job description is empty
    elif job_description.strip() == "":
        st.warning("Please paste the job description.")

    # If both resume and job description are given
    else:
        st.success("Resume and job description received!")

        # Extract text from resume PDF
        resume_text = extract_text_from_pdf(uploaded_resume)

        # Compare resume skills and job description skills
        resume_skills, jd_skills, matched_skills, missing_skills, match_percentage = compare_skills(resume_text,job_description)

        # Clean screening report
        st.write("## Screening Report")

        st.metric("Match Percentage", f"{match_percentage:.2f}%")

        if match_percentage >= 75:
            st.success("Strong match for this job description.")
        elif match_percentage >= 50:
            st.info("Moderate match. The resume has some important skills, but can be improved.")
        else:
            st.warning("Low match. The resume is missing many skills from the job description.")

        st.write("### Matched Skills")
        if matched_skills:
            for skill in matched_skills:
                st.write(f"- {skill}")
        else:
            st.write("No matched skills found.")

        st.write("### Missing Skills")
        if missing_skills:
            for skill in missing_skills:
                st.write(f"- {skill}")
        else:
            st.write("No missing skills found.")

        st.write("### Resume Skills Found")
        if resume_skills:
            for skill in resume_skills:
                st.write(f"- {skill}")
        else:
            st.write("No skills found in resume.")

        st.write("### Job Description Skills Found")
        if jd_skills:
           for skill in jd_skills:
            st.write(f"- {skill}")
        else:
            st.write("No skills found in job description.")