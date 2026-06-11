import json
import os
from typing import List

from .scorer import ScoredCandidate
from .utils import logger


def rerank_with_llm(
    scored_candidates: List[ScoredCandidate],
    max_shorts: int,
    provider: str = "openai",
    model: str | None = None,
) -> List[ScoredCandidate]:
    if provider != "openai":
        logger.warning(f"Unsupported LLM provider '{provider}'. Keeping heuristic ranking.")
        return scored_candidates

    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY is not set. Keeping heuristic ranking.")
        return scored_candidates

    try:
        from openai import OpenAI
    except ImportError:
        logger.warning("openai package is not installed. Keeping heuristic ranking.")
        return scored_candidates

    shortlist = scored_candidates[: min(20, len(scored_candidates))]
    payload = [
        {
            "id": idx,
            "start": round(c.candidate.start_time, 2),
            "end": round(c.candidate.end_time, 2),
            "duration": round(c.candidate.duration, 2),
            "heuristic_score": round(c.score, 2),
            "reason": c.reason,
            "motion": round(c.motion_score, 2),
            "audio_db": round(c.audio_score, 2),
            "brightness": round(c.brightness, 2),
        }
        for idx, c in enumerate(shortlist)
    ]

    prompt = (
        "You are ranking candidate clips for YouTube Shorts retention. "
        "Prefer clips with strong hooks, high energy, clear audio peaks, visual action, and complete moments. "
        "Return JSON only with this shape: {\"ranked_ids\":[0,1,2],\"notes\":{\"0\":\"reason\"}}. "
        f"Pick the best {max_shorts} candidates from this JSON:\n"
        f"{json.dumps(payload, ensure_ascii=False)}"
    )

    try:
        client = OpenAI()
        response = client.chat.completions.create(
            model=model or "gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        content = response.choices[0].message.content or "{}"
        data = json.loads(content)
        ranked_ids = [int(i) for i in data.get("ranked_ids", [])]
    except Exception as exc:
        logger.warning(f"LLM ranking failed. Keeping heuristic ranking. Error: {exc}")
        return scored_candidates

    ranked = []
    used = set()
    for idx in ranked_ids:
        if 0 <= idx < len(shortlist) and idx not in used:
            ranked.append(shortlist[idx])
            used.add(idx)

    for cand in scored_candidates:
        if cand not in ranked:
            ranked.append(cand)

    logger.info(f"LLM reranked {len(shortlist)} candidate(s).")
    return ranked
