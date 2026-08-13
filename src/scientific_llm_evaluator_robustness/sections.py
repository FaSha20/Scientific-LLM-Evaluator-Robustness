from __future__ import annotations

from dataclasses import dataclass
import re


ABSTRACT_PATTERN = re.compile(
    r"(?P<open>\\begin\{abstract\})(?P<body>.*?)(?P<close>\\end\{abstract\})",
    re.DOTALL | re.IGNORECASE,
)

SECTION_PATTERN = re.compile(
    r"\\section\*?\{(?P<title>[^}]*)\}",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class TextSpan:
    name: str
    start: int
    end: int
    text: str


@dataclass(frozen=True)
class TargetSections:
    abstract: TextSpan
    introduction: TextSpan


def extract_target_sections(full_text: str) -> TargetSections:
    abstract_match = ABSTRACT_PATTERN.search(full_text)
    if not abstract_match:
        raise ValueError("Could not find abstract environment")

    abstract = TextSpan(
        name="abstract",
        start=abstract_match.start("body"),
        end=abstract_match.end("body"),
        text=abstract_match.group("body"),
    )

    section_matches = list(SECTION_PATTERN.finditer(full_text))
    intro_index = next(
        (
            index
            for index, match in enumerate(section_matches)
            if "introduction" in _normalize_section_title(match.group("title"))
        ),
        None,
    )
    if intro_index is None:
        raise ValueError("Could not find introduction section")

    intro_header = section_matches[intro_index]
    intro_start = intro_header.end()
    intro_end = (
        section_matches[intro_index + 1].start()
        if intro_index + 1 < len(section_matches)
        else len(full_text)
    )
    introduction = TextSpan(
        name="introduction",
        start=intro_start,
        end=intro_end,
        text=full_text[intro_start:intro_end],
    )
    return TargetSections(abstract=abstract, introduction=introduction)


def replace_target_sections(
    full_text: str,
    sections: TargetSections,
    *,
    abstract: str,
    introduction: str,
) -> str:
    replacements = [
        (sections.abstract.start, sections.abstract.end, abstract),
        (sections.introduction.start, sections.introduction.end, introduction),
    ]

    updated = full_text
    for start, end, replacement in sorted(replacements, reverse=True):
        updated = updated[:start] + replacement + updated[end:]
    return updated


def _normalize_section_title(title: str) -> str:
    title = re.sub(r"^\s*\d+(?:\.\d+)*\s*", "", title)
    return re.sub(r"\s+", " ", title).strip().lower()
