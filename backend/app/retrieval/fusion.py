from collections import defaultdict


def reciprocal_rank_fusion(
    *ranked_lists: list[dict],
    k: int = 60,
) -> list[dict]:
    """
    Standard RRF: score(d) = Σ 1/(k + rank(d))
    k=60 is the well-established default from the original paper.
    Higher RRF score = better candidate.
    """
    scores: dict[str, float] = defaultdict(float)
    chunk_map: dict[str, dict] = {}

    for ranked_list in ranked_lists:
        for rank, chunk in enumerate(ranked_list, start=1):
            cid = chunk["chunk_id"]
            scores[cid] += 1.0 / (k + rank)
            chunk_map[cid] = chunk

    # Sort by descending RRF score
    sorted_ids = sorted(scores, key=lambda cid: scores[cid], reverse=True)

    return [
        {**chunk_map[cid], "score": scores[cid]}
        for cid in sorted_ids
    ]
