from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever


def create_retriever(
    vector_store: FAISS,
    top_k: int = 4,
) -> VectorStoreRetriever:
    if top_k <= 0:
        raise ValueError("top_k must be greater than 0.")

    return vector_store.as_retriever(
        search_kwargs={"k": top_k}
    )


def retrieve_with_scores(
    vector_store: FAISS,
    question: str,
    top_k: int = 20,
    min_score: float | None = None,
) -> list[tuple[Document, float]]:
    question = question.strip()

    if not question:
        raise ValueError("Question cannot be empty.")

    if top_k <= 0:
        raise ValueError("top_k must be greater than 0.")

    if min_score is not None and not 0 <= min_score <= 1:
        raise ValueError("min_score must be between 0 and 1.")

    results = vector_store.similarity_search_with_relevance_scores(
        query=question,
        k=top_k,
    )

    return [
        (document, float(score))
        for document, score in results
        if document.page_content.strip()
        and (min_score is None or score >= min_score)
    ]