# Skills we want to check in resume and job description
skills_list = [
    "Python",
    "SQL",
    "Streamlit",
    "FastAPI",
    "Machine Learning",
    "Deep Learning",
    "Generative AI",
    "OpenAI",
    "LangChain",
    "RAG",
    "Vector Database",
    "APIs",
    "Git",
    "GitHub",
    "Docker",
    "Pandas",
    "NumPy"
]
# Function to find skills from a text
def extract_skills(text, skills_list):
    found_skills = []

    # Convert full text to lowercase so matching is easier
    text = text.lower()

    for skill in skills_list:
        if skill.lower() in text:
            found_skills.append(skill)

    return found_skills

# Function to compare resume skills with job description skills
def compare_skills(resume_text, job_description):
    resume_skills = extract_skills(resume_text, skills_list)
    jd_skills = extract_skills(job_description, skills_list)

    matched_skills = list(set(resume_skills) & set(jd_skills))
    missing_skills = list(set(jd_skills) - set(resume_skills))

    if len(jd_skills) > 0:
        match_percentage = (len(matched_skills) / len(jd_skills)) * 100
    else:
        match_percentage = 0

    return resume_skills, jd_skills, matched_skills, missing_skills, match_percentage