# Resume Screening App 🤖

An AI-powered resume screening and job search tool built with Streamlit. It uses a **multi-agent AI pipeline** to screen resumes against job descriptions, and can search **live LinkedIn job postings** and ATS-score each one against your resume.

## Features

**1. Resume Screening (AI Agents)**

Upload a resume PDF, paste a job description, and a pipeline of 4 specialized AI agents screens the candidate:

| Agent | Job |
|---|---|
| Resume Parser | Extracts skills, experience, and education from the resume |
| JD Analyzer | Identifies required skills and responsibilities from the job description |
| Matcher | Scores the fit 0–100, understanding related skills (PyTorch → Deep Learning) |
| Report Writer | Writes a recruiter-style report with strengths, gaps, and interview questions |

A basic keyword-matching mode is also included for comparison (no API needed).

**2. LinkedIn Job Search + ATS Scoring**

Search LinkedIn jobs posted as recently as the **past hour** (via the Apify scraping platform), then a 5th agent simulates an ATS (Applicant Tracking System) and scores your resume against every job — ranked best-match-first, with missing keywords and a tailoring tip for each.

## Tech Stack

- **Python + Streamlit** — web UI
- **OpenAI API (gpt-4o-mini)** — the AI agents
- **Apify** — LinkedIn job data
- **pypdf** — PDF text extraction

## Setup

```bash
git clone <this-repo>
cd resume-screening-app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run main.py
```

You'll need two API keys (entered in the app sidebar, or set as environment variables):

- `OPENAI_API_KEY` — from [platform.openai.com](https://platform.openai.com) (requires ~$5 credit; each screening costs under a cent)
- `APIFY_TOKEN` — free at [apify.com](https://apify.com) ($5/month free credit; only needed for job search)

## Project Structure

```
main.py           # Streamlit UI (two tabs)
agents.py         # The 5 AI agents + pipeline orchestrator
job_search.py     # LinkedIn job fetching via Apify
skill_matcher.py  # Basic keyword matching (non-AI mode)
pdf_reader.py     # PDF text extraction
```
