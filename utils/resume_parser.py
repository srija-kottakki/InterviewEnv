from __future__ import annotations

import re
from io import BytesIO


PROGRAMMING_LANGUAGES = [
    "python", "java", "javascript", "typescript", "c++", "c#", "c", "go", "rust", "sql", "r", "scala", "swift", "kotlin",
]
LIBRARIES_FRAMEWORKS = [
    "react", "angular", "vue", "node", "express", "fastapi", "flask", "django", "pandas", "numpy", "scikit-learn",
    "tensorflow", "pytorch", "keras", "opencv", "spring", "next.js", "tailwind", "bootstrap", "ml", "machine learning",
]
TOOLS = [
    "git", "github", "docker", "kubernetes", "aws", "gcp", "azure", "linux", "mongodb", "postgresql", "mysql",
    "tableau", "power bi", "jupyter", "figma", "postman", "spark", "hadoop",
]


def extract_resume_text(filename: str, content: bytes) -> str:
    if filename.lower().endswith(".pdf"):
        try:
            from pypdf import PdfReader

            reader = PdfReader(BytesIO(content))
            return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
        except Exception:
            return content.decode("latin-1", errors="ignore")
    return content.decode("utf-8", errors="ignore")


def parse_resume_text(text: str) -> dict[str, object]:
    clean_text = re.sub(r"\r\n?", "\n", text)
    lower = clean_text.lower()
    sections = _extract_sections(clean_text)
    skills = _detect_terms(lower, PROGRAMMING_LANGUAGES + LIBRARIES_FRAMEWORKS + TOOLS)
    projects = _extract_bullets(sections.get("projects", ""))
    experience = _extract_bullets(sections.get("experience", ""))
    education = _extract_bullets(sections.get("education", ""))
    tools = _detect_terms(lower, TOOLS)
    languages = _detect_terms(lower, PROGRAMMING_LANGUAGES)
    libraries = _detect_terms(lower, LIBRARIES_FRAMEWORKS)

    if not projects:
        projects = _guess_project_lines(clean_text)
    if not experience:
        experience = _guess_experience_lines(clean_text)

    return {
        "skills": skills,
        "projects": projects[:8],
        "experience": experience[:8],
        "education": education[:5],
        "tools_technologies": sorted(set(tools + languages + libraries)),
        "programming_languages": languages,
        "libraries_frameworks": libraries,
        "tools": tools,
    }


def _detect_terms(lower_text: str, terms: list[str]) -> list[str]:
    found = []
    for term in terms:
        pattern = r"(?<![a-z0-9])" + re.escape(term.lower()) + r"(?![a-z0-9])"
        if re.search(pattern, lower_text):
            found.append(term)
    return sorted(set(found), key=str.lower)


def _extract_sections(text: str) -> dict[str, str]:
    aliases = {
        "skills": ["skills", "technical skills"],
        "projects": ["projects", "project experience"],
        "experience": ["experience", "work experience", "internship", "internships", "employment"],
        "education": ["education", "academic background"],
    }
    headings = []
    for key, names in aliases.items():
        for name in names:
            match = re.search(rf"(?im)^\s*{re.escape(name)}\s*:?", text)
            if match:
                headings.append((match.start(), key))
                break
    headings.sort()
    sections = {}
    for index, (start, key) in enumerate(headings):
        end = headings[index + 1][0] if index + 1 < len(headings) else len(text)
        sections[key] = text[start:end]
    return sections


def _extract_bullets(section: str) -> list[str]:
    lines = []
    for line in section.splitlines()[1:]:
        cleaned = line.strip(" \t•-*")
        if len(cleaned.split()) >= 3:
            lines.append(cleaned)
    return lines


def _guess_project_lines(text: str) -> list[str]:
    return [line.strip(" \t•-*") for line in text.splitlines() if re.search(r"(?i)project|built|developed|implemented", line)][:8]


def _guess_experience_lines(text: str) -> list[str]:
    return [line.strip(" \t•-*") for line in text.splitlines() if re.search(r"(?i)intern|experience|worked|responsible|collaborated", line)][:8]
