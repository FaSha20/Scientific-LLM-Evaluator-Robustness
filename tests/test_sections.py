from scientific_llm_evaluator_robustness.sections import (
    extract_target_sections,
    replace_target_sections,
)


def test_extract_target_sections_latex_abstract_and_intro():
    full_text = (
        "\\title{X}\n"
        "\\begin{abstract}Old abstract.\\end{abstract}\n"
        "\\section{1 INTRODUCTION  }\nOld intro.\n"
        "\\section{2 Method}\nMethod body."
    )

    sections = extract_target_sections(full_text)

    assert sections.abstract.text == "Old abstract."
    assert "Old intro." in sections.introduction.text
    assert "\\section{2 Method}" not in sections.introduction.text


def test_replace_target_sections_only_changes_abstract_and_intro():
    full_text = (
        "\\begin{abstract}Old abstract.\\end{abstract}\n"
        "\\section{Introduction}\nOld intro.\n"
        "\\section{Method}\nMethod body."
    )
    sections = extract_target_sections(full_text)

    updated = replace_target_sections(
        full_text,
        sections,
        abstract="New abstract.",
        introduction="\nNew intro.\n",
    )

    assert "New abstract." in updated
    assert "New intro." in updated
    assert "Method body." in updated
