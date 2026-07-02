import logging

import numpy as np

logger = logging.getLogger(__name__)

_model = None


def _get_model(model_name: str):
    global _model
    if _model is None:
        from sentence_transformers import CrossEncoder

        logger.info("Loading cross-encoder model: %s", model_name)
        _model = CrossEncoder(model_name)
    return _model


def rerank(
    query: str,
    candidates: list[dict],
    top_n: int,
    model_name: str,
) -> list[dict]:
    if not candidates:
        return []

    model = _get_model(model_name)
    pairs = [(query, c["text"]) for c in candidates]
    # ms-marco cross-encoders output raw logits; sigmoid maps them to [0,1]
    # so confidence_threshold is comparable across queries.
    scores = 1.0 / (1.0 + np.exp(-model.predict(pairs)))

    scored = sorted(
        zip(candidates, scores),
        key=lambda x: x[1],
        reverse=True,
    )

    return [{**chunk, "score": float(score)} for chunk, score in scored[:top_n]]
