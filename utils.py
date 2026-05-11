import re
from pathlib import Path
import pdfplumber
import docx

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can", "need",
    "this", "that", "these", "those", "i", "you", "we", "they", "he", "she",
    "it", "its", "our", "your", "their", "my", "his", "her", "who", "which",
    "what", "when", "where", "how", "why", "if", "then", "than", "so", "yet",
    "both", "either", "neither", "not", "no", "nor", "only", "own", "same",
    "such", "too", "very", "just", "more", "most", "other", "some", "any",
    "all", "each", "every", "few", "less", "also", "about", "above", "after",
    "before", "between", "through", "during", "including", "without", "per",
    "up", "down", "out", "off", "over", "under", "again", "further", "once",
    "here", "there", "while", "although", "because", "since", "until",
    "unless", "however", "therefore", "thus", "hence", "must", "use",
    "using", "used", "well", "new", "good", "high", "strong", "able",
    "across", "within", "into", "upon", "toward", "towards", "work",
    "working", "s", "e", "re", "ve", "ll", "t", "d", "m",
}

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


def extract_jd_keywords(text):
    normalized = normalize_text(text)
    words = re.findall(r"\b[a-z][a-z+#.\-]*\b", normalized)
    freq = {}
    for w in words:
        if len(w) > 2 and w not in STOP_WORDS:
            freq[w] = freq.get(w, 0) + 1
    return sorted(freq.keys(), key=lambda k: -freq[k])


def compute_ats_score(resume_text, job_description):
    resume_normalized = normalize_text(resume_text)
    keywords = extract_jd_keywords(job_description)
    if not keywords:
        return 0, [], []
    matched = [kw for kw in keywords if kw in resume_normalized]
    missing = [kw for kw in keywords if kw not in resume_normalized]
    score = round(len(matched) / len(keywords) * 100)
    return score, matched, missing
