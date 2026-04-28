import os
import re
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR.parent / "model" / "data" / "portfolio_rag.txt"

load_dotenv()


def _load_sections() -> list[str]:
    if not DATA_FILE.exists():
        return []

    content = DATA_FILE.read_text(encoding="utf-8")
    return [section.strip() for section in re.split(r"\n\s*\n", content) if section.strip()]


def _score_section(section: str, question_terms: set[str]) -> int:
    section_terms = set(re.findall(r"\w+", section.lower()))
    return len(section_terms & question_terms)


def _get_llm() -> ChatGroq | None:
    if not os.getenv("GROQ_API_KEY"):
        return None

    return ChatGroq(model_name="llama-3.3-70b-versatile")


def get_response(question: str) -> str:
    cleaned_question = question.strip()
    if not cleaned_question:
        return "Ask a question about Abhishek's portfolio."

    sections = _load_sections()
    if not sections:
        return "Portfolio data is missing, so I can't answer yet."

    question_terms = set(re.findall(r"\w+", cleaned_question.lower()))
    ranked_sections = sorted(
        sections,
        key=lambda section: _score_section(section, question_terms),
        reverse=True,
    )
    context = "\n\n".join(section for section in ranked_sections[:3] if section)

    llm = _get_llm()
    if llm is None:
        return "Set GROQ_API_KEY before using chat. Right now the backend has no LLM credentials."

    response = llm.invoke(f"""
You are Abhishek's AI assistant.
You speak confidently and sarcastically about his projects and skills.
Answer the question based only on the context below:

Context:
{context}

Question:
{cleaned_question}
""")
    return getattr(response, "content", str(response))
