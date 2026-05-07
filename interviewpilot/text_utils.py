"""Small text helpers for dependency-free MVP analysis."""

from __future__ import annotations

import re


SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "Python": ("python",),
    "JavaScript": ("javascript", "js",),
    "TypeScript": ("typescript", "ts"),
    "Java": ("java",),
    "Go": ("golang", " go "),
    "C++": ("c++", "cpp"),
    "React": ("react", "react.js", "reactjs"),
    "Next.js": ("next.js", "nextjs"),
    "Node.js": ("node.js", "nodejs", "node "),
    "FastAPI": ("fastapi",),
    "Django": ("django",),
    "Flask": ("flask",),
    "PostgreSQL": ("postgresql", "postgres"),
    "MySQL": ("mysql",),
    "MongoDB": ("mongodb", "mongo"),
    "Redis": ("redis",),
    "Docker": ("docker",),
    "Kubernetes": ("kubernetes", "k8s"),
    "AWS": ("aws", "amazon web services"),
    "Azure": ("azure",),
    "GCP": ("gcp", "google cloud"),
    "REST API": ("rest api", "restful", "api 设计", "api设计"),
    "GraphQL": ("graphql",),
    "Microservices": ("microservice", "microservices"),
    "System Design": ("system design", "scalability", "distributed system", "系统设计"),
    "Machine Learning": ("machine learning", "ml "),
    "LLM": ("llm", "large language model", "openai", "rag"),
    "RAG": ("rag", "retrieval augmented generation", "retrieval-augmented"),
    "CI/CD": ("ci/cd", "github actions", "continuous integration"),
    "Testing": ("unit test", "pytest", "testing", "test coverage", "自动化测试", "测试"),
}

ACTION_WORDS = (
    "built",
    "designed",
    "implemented",
    "optimized",
    "deployed",
    "led",
    "owned",
    "improved",
    "reduced",
    "increased",
    "created",
    "integrated",
    "构建",
    "设计",
    "实现",
    "优化",
    "部署",
    "负责",
    "提升",
    "降低",
)


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def split_lines(text: str) -> list[str]:
    return [line.strip(" -\t") for line in (text or "").splitlines() if line.strip(" -\t")]


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?。！？])\s+|\n+", text or "")
    return [normalize_space(part) for part in parts if normalize_space(part)]


def unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        clean = normalize_space(item)
        key = clean.casefold()
        if clean and key not in seen:
            seen.add(key)
            result.append(clean)
    return result


def extract_skills(text: str) -> list[str]:
    haystack = normalize_space(text).casefold()
    found: list[str] = []
    for canonical, aliases in SKILL_ALIASES.items():
        if any(_alias_matches(haystack, alias) for alias in aliases):
            found.append(canonical)
    return found


def _alias_matches(haystack: str, alias: str) -> bool:
    clean_alias = normalize_space(alias).casefold()
    if not clean_alias:
        return False
    escaped = re.escape(clean_alias).replace(r"\ ", r"\s+")
    return bool(re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", haystack, re.I))


def contains_metric(text: str) -> bool:
    return bool(re.search(r"\b\d+[%xX]?\b|\b\d+\s*(ms|s|sec|users|requests|qps)\b", text or "", re.I))


def contains_action_evidence(text: str) -> bool:
    lower = (text or "").casefold()
    return any(word.casefold() in lower for word in ACTION_WORDS)


def compact_list(items: list[str], limit: int) -> list[str]:
    clean = unique_preserve_order(items)
    return clean[:limit]
