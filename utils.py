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


ACTION_VERBS = [
    "led", "managed", "developed", "built", "created", "improved", "increased",
    "decreased", "reduced", "achieved", "delivered", "designed", "implemented",
    "launched", "coordinated", "executed", "streamlined", "optimized",
    "collaborated", "mentored", "trained", "analyzed", "presented", "spearheaded",
]


def generate_improvement_suggestions(text):
    normalized = normalize_text(text)
    emails = extract_emails(text)
    phones = extract_phone_numbers(text)
    skills = extract_skills(text)
    word_count = len(normalized.split())
    found_verbs = [v for v in ACTION_VERBS if v in normalized]
    has_metrics = bool(re.search(
        r"\d+\s*%|\$\s*\d+|\d+\s*(million|thousand|users|customers|clients|members|employees)",
        normalized,
    ))

    categories = []

    contact_tips = []
    if not emails:
        contact_tips.append("Add a professional email address (e.g. name@domain.com).")
    if not phones:
        contact_tips.append("Include a phone number so recruiters can reach you.")
    if "linkedin" not in normalized:
        contact_tips.append("Add your LinkedIn profile URL to increase credibility.")
    if "github" not in normalized:
        contact_tips.append("Consider adding your GitHub profile if you are in a technical role.")
    categories.append({
        "name": "Contact Information",
        "status": "good" if not contact_tips else "needs-work",
        "tips": contact_tips or ["All key contact details are present."],
    })

    summary_tips = []
    if not any(kw in normalized for kw in ["summary", "objective", "profile", "about me"]):
        summary_tips.append("Add a professional summary (3-4 sentences) at the top of your resume.")
        summary_tips.append("Highlight your key skills, years of experience, and career goal.")
    categories.append({
        "name": "Professional Summary",
        "status": "good" if not summary_tips else "needs-work",
        "tips": summary_tips or ["Professional summary or objective section is present."],
    })

    experience_tips = []
    if not any(kw in normalized for kw in ["experience", "employment", "work history", "position", "role"]):
        experience_tips.append("Add a dedicated Work Experience section.")
    if len(found_verbs) < 3:
        experience_tips.append("Use more action verbs — e.g. led, developed, improved, achieved, delivered.")
    if not has_metrics:
        experience_tips.append("Quantify achievements (e.g. 'Increased sales by 30%', 'Managed a team of 5').")
    if not any(kw in normalized for kw in ["project", "projects"]):
        experience_tips.append("Add a Projects section if you lack extensive formal work experience.")
    categories.append({
        "name": "Work Experience",
        "status": "good" if not experience_tips else "needs-work",
        "tips": experience_tips or ["Work experience section looks solid with action verbs and metrics."],
    })

    education_tips = []
    if not any(kw in normalized for kw in [
        "education", "degree", "university", "college",
        "bachelor", "master", "phd", "diploma", "certification",
    ]):
        education_tips.append("Add an Education section with your degree, institution, and graduation year.")
    categories.append({
        "name": "Education",
        "status": "good" if not education_tips else "needs-work",
        "tips": education_tips or ["Education section is present."],
    })

    skills_tips = []
    if "skill" not in normalized:
        skills_tips.append("Add a dedicated Skills section.")
    if len(skills) < 5:
        skills_tips.append(f"Only {len(skills)} skill(s) detected. Aim for 8-12 relevant skills.")
        skills_tips.append("Include both technical skills (tools, languages) and soft skills.")
    elif len(skills) < 8:
        skills_tips.append("Consider adding a few more skills to strengthen your profile.")
    categories.append({
        "name": "Skills",
        "status": "good" if len(skills) >= 8 else "needs-work",
        "tips": skills_tips or [f"{len(skills)} skills detected — strong skills section."],
    })

    format_tips = []
    if word_count < 200:
        format_tips.append(f"Resume is very short ({word_count} words). Aim for at least 400 words.")
    elif word_count > 900:
        format_tips.append(f"Resume may be too long ({word_count} words). Keep it concise — under 700 words for most roles.")
    if not re.search(
        r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|january|february|march|april|june|july|august|september|october|november|december|20\d\d|19\d\d)\b",
        normalized,
    ):
        format_tips.append("Include dates (month/year) for each experience and education entry.")
    categories.append({
        "name": "Length & Format",
        "status": "good" if not format_tips else "needs-work",
        "tips": format_tips or [f"Good resume length ({word_count} words) with dates present."],
    })

    good_count = sum(1 for c in categories if c["status"] == "good")
    return categories, good_count, len(categories)


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
