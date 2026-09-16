from dataclasses import dataclass
from functools import lru_cache
from math import isfinite

import numpy as np
from langchain_core.documents import Document
from sentence_transformers import CrossEncoder


@dataclass(frozen=True)
class RerankedDocument:
    document: Document
    retrieval_score: float
    reranker_score: float


@lru_cache(maxsize=1)
def get_reranker(
    model_name: str = "BAAI/bge-reranker-v2-m3",
    device: str = "cpu",
) -> CrossEncoder:
    return CrossEncoder(
        model_name,
        device=device,
        max_length=512,
    )


def rerank_documents(
    question: str,
    results: list[tuple[Document, float]],
    reranker: CrossEncoder,
    top_k: int = 4,
    batch_size: int = 8,
    min_score: float | None = None,
) -> list[RerankedDocument]:
    question = question.strip()

    if not question:
        raise ValueError("Question cannot be empty.")

    if top_k <= 0:
        raise ValueError("top_k must be greater than 0.")

    if batch_size <= 0:
        raise ValueError("batch_size must be greater than 0.")

    if min_score is not None and not isfinite(min_score):
        raise ValueError("min_score must be finite.")

    # Keep original documents and metadata.
    candidates = [
        (document, score)
        for document, score in results
        if document.page_content.strip()
    ]

    if not candidates:
        return []

    # Each pair contains the question and one candidate chunk.
    pairs = [
        (question, document.page_content.strip())
        for document, _ in candidates
    ]

    predictions = reranker.predict(
        pairs,
        batch_size=batch_size,
        show_progress_bar=False,
        convert_to_numpy=True,
    )

    scores = np.asarray(
        predictions,
        dtype=float,
    ).reshape(-1)

    if len(scores) != len(candidates):
        raise ValueError(
            "Reranker must return one score per document."
        )

    if not np.isfinite(scores).all():
        raise ValueError(
            "Reranker returned a non-finite score."
        )

    ranked_results = [
        RerankedDocument(
            document=document,
            retrieval_score=float(retrieval_score),
            reranker_score=float(reranker_score),
        )
        for (document, retrieval_score), reranker_score
        in zip(candidates, scores)
        if min_score is None or reranker_score >= min_score
    ]

    # Higher reranker scores come first.
    ranked_results.sort(
        key=lambda result: result.reranker_score,
        reverse=True,
    )

    return ranked_results[:top_k]