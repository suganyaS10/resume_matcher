from pathlib import Path
from dotenv import load_dotenv

BASE = Path(__file__).resolve().parent
load_dotenv(BASE / ".env")

import os
from ingest import extract_text, resume_to_bullets
from matcher import match
from mcp.server.fastmcp import FastMCP
import json

RESUME_PATH = BASE / "resume.pdf"
CACHE = BASE / "resume_bullets.json"

def resume_bullets():
  if os.path.exists(CACHE):
    with open(CACHE) as f:
      return json.load(f)
  resume_text = extract_text(RESUME_PATH)
  bullets = resume_to_bullets(resume_text)
  with open(CACHE, "w") as f:
    json.dump(bullets, f)

  return bullets

RESUME_BULLETS = resume_bullets()
mcp = FastMCP("Resume Matcher")

@mcp.tool()
def analyze_fit(job_description: str) -> dict:
  """Analyze how well the candidate's resume fits a given job description.
    The candidate's resume is ALREADY loaded on the server - do NOT ask the user
    for it; just pass the job description. Returns an overall coverage score and a
    per-requirement breakdown with gaps."""
  result = match(RESUME_BULLETS, job_description)
  return result

@mcp.resource("resume://current")
def current_resume() -> str:
    """The candidate's résumé, as a list of experience bullets."""
    return "\n".join(f"- {b}" for b in RESUME_BULLETS)

@mcp.prompt()
def tailor_application(job_description: str) -> str:
    """A ready-made prompt: assess fit for a job and suggest how to tailor the application."""
    return (
        f"I'm applying for the following job:\n\n{job_description}\n\n"
        "My résumé is available as the resource `resume://current`. "
        "Please read it, use the `analyze_fit` tool to score how well I match and find gaps, "
        "then suggest concrete ways to tailor my application — "
        "without inventing any experience I don't have."
    )

if __name__ == "__main__":
  mcp.run()
  
