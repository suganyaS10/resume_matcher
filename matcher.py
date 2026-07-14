import voyageai
import numpy as np
from dotenv import load_dotenv
from anthropic import Anthropic
import re

load_dotenv()

anthropic = Anthropic()

vo = voyageai.Client()

def normalize(vectors):
  v = np.array(vectors)
  return v / np.linalg.norm(v, axis=1, keepdims=True)

def _embed(text, input_type):
  return normalize(vo.embed(
      text, 
      model="voyage-4", 
      input_type=input_type
    ).embeddings
  )

def chunk_requirements(text):
  text = text.replace("\n", " ")
  parts = re.split(r'(?<=[.!?]) ', text)
  return [p.strip() for p in parts if len(p.strip()) > 20]

def match(bullets, jd, threshold=0.45, top_k=5):
  requirements = chunk_requirements(jd)

  bullet_matrix = _embed(bullets, input_type="document")
  jd_matrix = _embed(requirements, input_type="query")
  jd_vector = _embed([jd], input_type="query")[0]

  rows = []
  for requirement, jd_vec in zip(requirements, jd_matrix):
    requirement_score_for_resume = bullet_matrix @ jd_vec
    best_score_index = int(np.argmax(requirement_score_for_resume))
    best_score = requirement_score_for_resume[best_score_index]
    row = {
      "requirement": requirement,
      "best_match": bullets[best_score_index],
      "score": best_score,
      "covered": best_score >= threshold,
    }
    rows.append(row)

  overall_score = float(np.mean([r["score"] for r in rows])) if rows else 0.0
  top_bullets = [bullets[i] for i in np.argsort(bullet_matrix @ jd_vector)[::-1][:top_k]]
  return {"overall": overall_score, "requirements": rows, "top_bullets": top_bullets}

def tailored_summary(top_bullets, jd):
  context = "\n".join(f"- {b}" for b in top_bullets)

  prompt = f"""You are helping a candidate tailor their job application.
    Using ONLY the candidate's real experience below, write a 3-4 sentence professional
    summary tailored to the job description. Do NOT invent skills, tools, titles, or
    experience not in the bullets — only rephrase and emphasize what is there.

    Candidate's most relevant experience:
    {context}

    Job description:
    {jd}

    Tailored summary:"""

  response = anthropic.messages.create(
    model="claude-haiku-4-5",
    max_tokens=4069,
    messages=[{"role": "user", "content": prompt}]
  )
  return next(content.text for content in response.content if content.type == "text")

if __name__ == "__main__":
    from ingest import extract_text, resume_to_bullets

    bullets = resume_to_bullets(extract_text("/Users/suganyaselvarajan/Downloads/Suganya_S.pdf"))
    jd = """We're hiring a Senior Backend Engineer for our payments platform.
You'll build and scale APIs handling financial transactions, work with background job systems,
and ensure compliance with financial regulations. Strong SQL and Ruby experience required.
Experience with fraud detection and card processing is a plus."""

    result = match(bullets, jd)
    print(f"Overall coverage: {result['overall']:.2f}\n")
    for r in result["requirements"]:
        tag = "OK " if r["covered"] else "GAP"
        print(f"[{r['score']:.3f}] {tag}  {r['requirement']}")
        print(f"         best: {r['best_match']}\n")
    print("Top bullets to lead with:")
    for b in result["top_bullets"]:
        print(" -", b)
    print("\nTailored summary:\n")
    print(tailored_summary(result["top_bullets"], jd))
    
