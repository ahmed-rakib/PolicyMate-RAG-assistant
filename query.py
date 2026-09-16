from pathlib import Path

from app.services.embeddings import get_embedding_model
from app.services.vector_store import load_vector_store
from app.services.retriever import retrieve_with_scores
from app.services.reranker_service import (
    get_reranker,
    rerank_documents,
)
from app.services.llm_service import get_llm
from app.services.rag_service import generate_answer


BASE_DIR = Path(__file__).resolve().parent
VECTOR_STORE_PATH = BASE_DIR / "data" / "vector_store"

RETRIEVAL_TOP_K = 20
RERANK_TOP_K = 4

RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"
RERANKER_DEVICE = "cpu"

# Set only after evaluating scores on your own question/document pairs.
RERANK_MIN_SCORE: float | None = 0.3


def main() -> None:
    # 1. Read and validate the question.
    question = input("Enter question: ").strip()

    if not question:
        print("Question cannot be empty.")
        return

    # 2. Load the embedding model and existing FAISS index.
    embedding_model = get_embedding_model()

    vector_store = load_vector_store(
        directory=str(VECTOR_STORE_PATH),
        embedding_model=embedding_model,
    )

    print("FAISS index loaded.")

    # 3. Retrieve candidate chunks without a fixed score cutoff.
    candidates = retrieve_with_scores(
        vector_store=vector_store,
        question=question,
        top_k=RETRIEVAL_TOP_K,
        min_score=None,
    )

    print(
        f"Retrieved {len(candidates)} candidate chunks."
    )

    if not candidates:
        print(
            "No usable document chunks were retrieved."
        )
        return

    # 4. Load the reranker.
    print("Loading reranker...")

    reranker = get_reranker(
        model_name=RERANKER_MODEL,
        device=RERANKER_DEVICE,
    )

    # 5. Rerank candidates and select the best chunks.
    results = rerank_documents(
        question=question,
        results=candidates,
        reranker=reranker,
        top_k=RERANK_TOP_K,
        min_score=RERANK_MIN_SCORE,
    )

    if not results:
        print(
            "No document chunks passed the reranker filter."
        )
        return

    # Preserve the reranked order when preparing LLM context.
    documents = [
        result.document
        for result in results
    ]

    print(
        f"Selected {len(documents)} chunks after reranking."
    )

    # 6. Generate the answer using only selected documents.
    llm = get_llm()

    answer = generate_answer(
        question=question,
        documents=documents,
        llm=llm,
    )

    # 7. Display the answer.
    print(f"\nQuestion:\n{question}")
    print(f"\nAnswer:\n{answer}")

    # 8. Display the exact sources sent to the LLM.
    print("\nSources sent to the LLM:")

    for index, result in enumerate(
        results,
        start=1,
    ):
        document = result.document

        page = document.metadata.get(
            "page_label",
            "Unknown",
        )

        source = document.metadata.get(
            "source",
            "Unknown",
        )

        print("\n----------------------")
        print(f"Document {index}")

        print(
            f"Retrieval Score: "
            f"{result.retrieval_score:.4f}"
        )

        print(
            f"Reranker Score: "
            f"{result.reranker_score:.4f}"
        )

        print(f"Source: {source}")
        print(f"Page: {page}")

        print("Content Preview:")
        print(document.page_content[:300])


if __name__ == "__main__":
    main()