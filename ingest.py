import pdfplumber
from anthropic import Anthropic
from dotenv import load_dotenv
import json

load_dotenv()
anthropic = Anthropic()

BULLET_SCHEMA = {
  "type": "object",
  "properties": {"bullets": {"type": "array", "items": {"type": "string"}}},
  "required": ["bullets"],
  "additionalProperties": False,
}

def extract_text(source):
    if isinstance(source, str) and source.lower().endswith((".txt", ".md")):
        with open(source, encoding="utf-8") as f:
            return f.read()
    with pdfplumber.open(source) as pdf:
        return "\n".join(p.extract_text() or "" for p in pdf.pages)

def resume_to_bullets(text):
  prompt = f"""Segment this resume into a flat list of individual, self-contained bullets.

  Rules:
  - One entry per distinct experience bullet, skill line, or project point.
  - Each entry must stand on its own and preserve the original wording (light trimming only).
  - For experience bullets, prefix with the company so the bullet is self-contained,
    e.g. "Acme Payments - Developed and deployed scalable Rails apps processing 600k+ transactions/month".
  - Do NOT invent, embellish, summarize, or drop information - only split what is already there.
  - Skip contact details, section headers, and lines that are only dates.

  Resume text:
  {text}"""

  response = anthropic.messages.create(
    model="claude-opus-4-8",
    max_tokens=4096,
    output_config={"format": {"type": "json_schema", "schema": BULLET_SCHEMA}},
    messages=[{"role": "user", "content": prompt}]
  )

  resp = next(content.text for content in response.content if content.type == "text")
  return json.loads(resp)["bullets"]

if __name__ == "__main__":
  resume_text = extract_text("/Users/suganyaselvarajan/Downloads/Suganya_S.pdf")
  resume_bullets = resume_to_bullets(resume_text)
  for i, resume_bullet in enumerate(resume_bullets, 1):
    print(f"{i} {resume_bullet}")
