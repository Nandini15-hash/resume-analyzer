import re
from pathlib import Path
import pdfplumber
import docx

COMMON_SKILLS = [
    "python", "java", "javascript", "sql", "excel", "data analysis", "communication",
    "teamwork", "project management", "machine learning", "aws", "azure", "react", "django",
    "flask", "git", "html", "css", "leadership", "research", "presentation",
]


def extract_text_from_resume(path):
    path = Path(path)
    text = ""
    if path.suffix.lower() == ".pdf":
        with pdfplumber.open(str(path)) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
            text = "\n".join(pages)
    elif path.suffix.lower() == ".docx":
        document = docx.Document(str(path))
        paragraphs = [paragraph.text for paragraph in document.paragraphs]
        text = "\n".join(paragraphs)
    else:
        raise ValueError("Unsupported file type")
    return text.strip()


def normalize_text(text):
    return re.sub(r"\s+", " ", text.lower()).strip()


def extract_emails(text):
    return re.findall(r"[\w\.-]+@[\w\.-]+\.[a-z]{2,}", text, re.I)


def extract_phone_numbers(text):
    phones = re.findall(r"\+?\d[\d\s\-\(\)]{7,}\d", text)
    return phones


def extract_skills(text):
    normalized = normalize_text(text)
    found = []
    for skill in COMMON_SKILLS:
        if skill in normalized and skill not in found:
            found.append(skill)
    return found


def count_keywords(text, keywords):
    normalized = normalize_text(text)
    return sum(1 for keyword in keywords if keyword in normalized)


def score_resume_and_extract_skills(text):
    normalized = normalize_text(text)
    keywords = ["experience", "education", "degree", "project", "lead", "develop", "analysis", "skill", "work"]
    email = extract_emails(text)
    phone = extract_phone_numbers(text)
    skills = extract_skills(text)

    score = 0
    score += min(20, len(normalized.split()))
    score += 20 if email else 0
    score += 20 if phone else 0
    score += min(20, count_keywords(text, keywords) * 5)
    score += min(20, len(skills) * 5)
    score += 10 if "summary" in normalized or "objective" in normalized else 0

    score = min(100, max(15, score))

    advice_pieces = []
    if not email:
        advice_pieces.append("Add a professional email address.")
    if not phone:
        advice_pieces.append("Include a phone number so recruiters can contact you.")
    if len(skills) < 3:
        advice_pieces.append("List more skills and use keywords found in job descriptions.")
    if "experience" not in normalized and "project" not in normalized:
        advice_pieces.append("Add a dedicated experience or project section.")
    if "education" not in normalized:
        advice_pieces.append("Mention your education or relevant training.")
    if not advice_pieces:
        advice_pieces.append("Your resume has a solid structure. Keep focusing on achievements and measurable results.")

    advice = " ".join(advice_pieces)
    return score, ", ".join(skills), advice
