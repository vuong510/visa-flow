from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List
import anthropic
import httpx
import io

try:
    from pypdf import PdfReader
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

router = APIRouter()
_claude = anthropic.Anthropic()


def extract_text_from_cv(data: bytes, filename: str) -> str:
    name = filename.lower()
    if name.endswith(".pdf") and HAS_PDF:
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    # plain text / docx fallback
    try:
        return data.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def claude_extract_skills(cv_text: str) -> List[str]:
    msg = _claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": (
                "Extract the top core technical and professional skills from this CV.\n"
                "Return ONLY a JSON array of strings, e.g. [\"Python\",\"React\",\"SQL\"].\n"
                "Include at most 15 skills. No explanation, just the JSON array.\n\n"
                f"CV:\n{cv_text[:6000]}"
            ),
        }],
    )
    import json, re
    text = msg.content[0].text.strip()
    match = re.search(r"\[.*?\]", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return []


@router.post("/cv/extract-skills")
async def extract_skills(file: UploadFile = File(...)):
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file")
    cv_text = extract_text_from_cv(data, file.filename or "cv.pdf")
    if len(cv_text.strip()) < 50:
        raise HTTPException(400, "Could not extract text from file")
    skills = claude_extract_skills(cv_text)
    if not skills:
        raise HTTPException(500, "Could not extract skills")
    return {"skills": skills}


class SearchRequest(BaseModel):
    skills: List[str]


@router.post("/cv/search-jobs")
async def search_jobs(req: SearchRequest):
    if not req.skills:
        raise HTTPException(400, "No skills provided")

    query = " ".join(req.skills[:5])
    jobs = []

    # Remotive free API
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            for skill in req.skills[:4]:
                resp = await client.get(
                    "https://remotive.com/api/remote-jobs",
                    params={"search": skill, "limit": 5},
                )
                if resp.status_code == 200:
                    for j in resp.json().get("jobs", []):
                        if not any(x["url"] == j["url"] for x in jobs):
                            jobs.append({
                                "title": j.get("title", ""),
                                "company": j.get("company_name", ""),
                                "location": j.get("candidate_required_location", "Remote"),
                                "url": j.get("url", ""),
                                "tags": j.get("tags", [])[:5],
                                "source": "Remotive",
                            })
    except Exception:
        pass

    # Search links per skill on major job boards
    from urllib.parse import quote_plus
    board_links = []
    boards = [
        ("LinkedIn",   "https://www.linkedin.com/jobs/search/?keywords={q}&f_TPR=r2592000"),
        ("Indeed",     "https://www.indeed.com/jobs?q={q}&sort=date"),
        ("Glassdoor",  "https://www.glassdoor.com/Job/jobs.htm?sc.keyword={q}"),
        ("ITviec",     "https://itviec.com/it-jobs/{slug}"),
        ("TopDev",     "https://topdev.vn/jobs?q={q}"),
    ]
    for skill in req.skills[:5]:
        q = quote_plus(skill)
        slug = skill.lower().replace(" ", "-").replace("/", "-")
        for name, template in boards:
            url = template.replace("{q}", q).replace("{slug}", slug)
            board_links.append({
                "title": f"{skill} jobs",
                "company": name,
                "location": "All locations",
                "url": url,
                "tags": [skill],
                "source": name,
            })

    return {"jobs": jobs[:15] + board_links}
