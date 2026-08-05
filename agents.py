import json
from openai import OpenAI

# Model used by all agents (cheap and fast)
MODEL = "gpt-4o-mini"


# Helper function: send a prompt to OpenAI and get JSON back
def run_agent(client, system_prompt, user_content):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    return json.loads(response.choices[0].message.content)


# Agent 1: Resume Parser
# Reads the raw resume text and pulls out structured information
def resume_parser_agent(client, resume_text):
    system_prompt = """You are a resume parsing agent.
Extract structured information from the resume text.
Return JSON with exactly these keys:
- "name": candidate name (string, or "Unknown")
- "skills": list of technical and soft skills found
- "experience": list of jobs, each with "title", "company", "duration"
- "education": list of degrees/certifications
- "years_of_experience": estimated total years (number)"""

    return run_agent(client, system_prompt, resume_text)


# Agent 2: Job Description Analyzer
# Reads the job description and figures out what the employer wants
def jd_analyzer_agent(client, job_description):
    system_prompt = """You are a job description analysis agent.
Analyze the job description and return JSON with exactly these keys:
- "job_title": the role title (string)
- "required_skills": list of must-have skills
- "nice_to_have_skills": list of preferred but optional skills
- "min_years_experience": minimum years required (number, 0 if not stated)
- "key_responsibilities": list of main duties"""

    return run_agent(client, system_prompt, job_description)


# Agent 3: Matcher
# Compares the parsed resume against the analyzed job description
def matcher_agent(client, parsed_resume, analyzed_jd):
    system_prompt = """You are a candidate matching agent.
Compare the parsed resume against the job requirements.
Consider related/equivalent skills as matches (e.g. "PyTorch" counts toward "Deep Learning").
Return JSON with exactly these keys:
- "match_percentage": overall fit score 0-100 (number)
- "matched_skills": required skills the candidate has
- "missing_skills": required skills the candidate lacks
- "bonus_skills": nice-to-have skills the candidate has
- "experience_fit": "meets", "below", or "exceeds"
- "reasoning": 2-3 sentence explanation of the score"""

    user_content = json.dumps({
        "parsed_resume": parsed_resume,
        "job_requirements": analyzed_jd,
    })
    return run_agent(client, system_prompt, user_content)


# Agent 4: Report Writer
# Turns the match results into a recruiter-friendly report
def report_writer_agent(client, parsed_resume, analyzed_jd, match_result):
    system_prompt = """You are a report writing agent for recruiters.
Write a screening report in Markdown based on the data provided.
Return JSON with exactly these keys:
- "recommendation": "Strong Yes", "Yes", "Maybe", or "No"
- "report": Markdown report with sections: Summary, Strengths, Gaps, Suggested Interview Questions (3 questions probing the gaps)"""

    user_content = json.dumps({
        "parsed_resume": parsed_resume,
        "job_requirements": analyzed_jd,
        "match_result": match_result,
    })
    return run_agent(client, system_prompt, user_content)


# Agent 5: ATS Scorer
# Scores how well YOUR resume matches one job posting,
# the way an Applicant Tracking System would
def ats_score_agent(client, resume_text, job):
    system_prompt = """You are an ATS (Applicant Tracking System) simulation agent.
Score how well the resume matches this specific job posting.
Focus on: keyword overlap with the job description, required skills coverage,
job title alignment, and experience level fit.
Return JSON with exactly these keys:
- "ats_score": 0-100 (number). Be realistic - most ATS matches score 40-80.
- "matched_keywords": important JD keywords found in the resume
- "missing_keywords": important JD keywords NOT in the resume
- "verdict": "Apply now", "Worth applying", "Tailor resume first", or "Skip"
- "quick_tip": one sentence on how to improve the resume for THIS job"""

    user_content = json.dumps({
        "resume": resume_text,
        "job_title": job["title"],
        "company": job["company"],
        "job_description": job["description"][:6000],
    })
    return run_agent(client, system_prompt, user_content)


# Scores a list of jobs against the resume, one by one
# on_progress(i, total) lets the UI show a progress bar
def score_jobs_against_resume(api_key, resume_text, jobs, on_progress=None):
    client = OpenAI(api_key=api_key)
    scored = []

    for i, job in enumerate(jobs):
        if on_progress:
            on_progress(i + 1, len(jobs))
        result = ats_score_agent(client, resume_text, job)
        scored.append({**job, **result})

    # Highest ATS score first
    scored.sort(key=lambda j: j["ats_score"], reverse=True)
    return scored


# Orchestrator: runs all 4 agents in order
# on_step is an optional callback to report progress to the UI
def run_screening_pipeline(api_key, resume_text, job_description, on_step=None):
    client = OpenAI(api_key=api_key)

    if on_step:
        on_step("Parsing resume...")
    parsed_resume = resume_parser_agent(client, resume_text)

    if on_step:
        on_step("Analyzing job description...")
    analyzed_jd = jd_analyzer_agent(client, job_description)

    if on_step:
        on_step("Matching candidate to role...")
    match_result = matcher_agent(client, parsed_resume, analyzed_jd)

    if on_step:
        on_step("Writing screening report...")
    report = report_writer_agent(client, parsed_resume, analyzed_jd, match_result)

    return {
        "parsed_resume": parsed_resume,
        "analyzed_jd": analyzed_jd,
        "match_result": match_result,
        "report": report,
    }
