from __future__ import annotations


def _clamp(value: float) -> float:
    return round(min(max(value, 0.0), 1.0), 4)


def analyze_behavior(answer: str, state: dict | None = None) -> dict[str, object]:
    words = [word.strip(".,!?;:").lower() for word in answer.split()]
    lowered = answer.lower()
    filler_words = {"um", "uh", "like", "basically"}
    filler_count = sum(1 for word in words if word in filler_words) + lowered.count("you know")
    filler_score = _clamp(1.0 - min(filler_count / 4.0, 1.0))

    confident_markers = ["i led", "i decided", "i built", "i measured", "i improved", "i learned", "i recommend", "i owned"]
    uncertain_markers = ["maybe", "sort of", "kind of", "i guess", "probably", "not sure"]
    word_count = max(len(words), 1)
    confidence_score = _clamp(
        0.45
        + min(word_count / 80.0, 0.20)
        + 0.10 * sum(1 for marker in confident_markers if marker in lowered)
        - 0.12 * sum(1 for marker in uncertain_markers if marker in lowered)
    )

    structure_markers = ["first", "then", "because", "for example", "result", "learned", "situation", "task", "action", "impact"]
    clarity_score = _clamp(min(word_count / 70.0, 0.35) + 0.65 * min(sum(1 for marker in structure_markers if marker in lowered) / 3.0, 1.0))

    comments = []
    comments.append("Low filler usage." if filler_score >= 0.8 else "Reduce filler words such as um, uh, like, basically, or you know.")
    comments.append("Confident delivery." if confidence_score >= 0.7 else "Use more decisive phrasing and own your actions.")
    comments.append("Clear structure." if clarity_score >= 0.7 else "Add structure, examples, and a measurable result.")

    return {
        "filler_score": filler_score,
        "confidence_score": confidence_score,
        "clarity_score": clarity_score,
        "comments": " ".join(comments),
    }
