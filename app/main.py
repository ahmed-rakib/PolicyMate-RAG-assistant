import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from starlette.concurrency import run_in_threadpool

from app.services.embeddings import get_embedding_model
from app.services.vector_store import load_vector_store
from app.services.retriever import retrieve_with_scores
from app.services.reranker_service import (
    get_reranker,
    rerank_documents,
)
from app.services.llm_service import get_llm
from app.services.rag_service import generate_answer


PROJECT_DIR = Path(__file__).resolve().parents[1]

INDEX_DIR = PROJECT_DIR / "data" / "vector_store"

HTML_FILE = (
    Path(__file__).resolve().parent
    / "static"
    / "index.html"
)

RETRIEVAL_TOP_K = 20
RERANK_TOP_K = 4

# Set a cutoff only after evaluating your own questions.
RERANK_MIN_SCORE: float | None = None

logger = logging.getLogger("uvicorn.error")


class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(
        min_length=1,
        max_length=2000,
        strict=True,
    )

    @field_validator("question", mode="before")
    @classmethod
    def strip_question(cls, value):
        return (
            value.strip()
            if isinstance(value, str)
            else value
        )


class Source(BaseModel):
    document_number: int
    filename: str
    page: str
    retrieval_score: float
    reranker_score: float
    content: str


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    retrieved_count: int
    elapsed_seconds: float


def load_resources() -> dict:
    # Validate the existing FAISS files.
    for filename in ("index.faiss", "index.pkl"):
        file_path = INDEX_DIR / filename

        if not file_path.is_file():
            raise FileNotFoundError(
                f"Missing FAISS file: {file_path}"
            )

    logger.info("Loading embeddings and FAISS index...")

    embeddings = get_embedding_model()

    vector_store = load_vector_store(
        directory=str(INDEX_DIR),
        embedding_model=embeddings,
    )

    logger.info("Loading reranker...")

    reranker = get_reranker(
        model_name="BAAI/bge-reranker-v2-m3",
        device="cpu",
    )

    return {
        "vector_store": vector_store,
        "reranker": reranker,
        "llm": get_llm(),
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not HTML_FILE.is_file():
        raise FileNotFoundError(
            f"UI file not found: {HTML_FILE}"
        )

    # Load shared resources once per server process.
    app.state.resources = await run_in_threadpool(
        load_resources
    )

    app.state.inference_lock = asyncio.Lock()

    logger.info("RAG resources loaded. UI is ready.")

    try:
        yield
    finally:
        app.state.resources.clear()
        get_reranker.cache_clear()


app = FastAPI(
    title="Document Assistant",
    lifespan=lifespan,
)

app.mount(
    "/static",
    StaticFiles(directory=HTML_FILE.parent),
    name="static",
)


def answer_question(
    question: str,
    resources: dict,
) -> AskResponse:
    start = perf_counter()

    # 1. Retrieve candidates.
    candidates = retrieve_with_scores(
        vector_store=resources["vector_store"],
        question=question,
        top_k=RETRIEVAL_TOP_K,
        min_score=None,
    )

    # 2. Rerank candidates.
    ranked = rerank_documents(
        question=question,
        results=candidates,
        reranker=resources["reranker"],
        top_k=RERANK_TOP_K,
        min_score=RERANK_MIN_SCORE,
    )

    # 3. Generate an answer using selected documents.
    # Your existing function handles an empty document list.
    answer = generate_answer(
        question=question,
        documents=[
            item.document
            for item in ranked
        ],
        llm=resources["llm"],
    )

    # 4. Prepare the exact sources sent to the LLM.
    sources = []

    for number, item in enumerate(ranked, start=1):
        document = item.document

        raw_source = str(
            document.metadata.get("source") or "Unknown"
        )

        # Handles both Windows and Unix-style paths.
        filename = (
            raw_source
            .replace("\\", "/")
            .rsplit("/", 1)[-1]
        )

        page = document.metadata.get("page_label")

        sources.append(
            Source(
                document_number=number,
                filename=filename,
                page=(
                    str(page)
                    if page is not None
                    else "Unknown"
                ),
                retrieval_score=item.retrieval_score,
                reranker_score=item.reranker_score,
                content=document.page_content,
            )
        )

    return AskResponse(
        answer=answer,
        sources=sources,
        retrieved_count=len(candidates),
        elapsed_seconds=round(
            perf_counter() - start,
            2,
        ),
    )


@app.get("/", response_class=FileResponse)
async def home():
    return FileResponse(
        HTML_FILE,
        media_type="text/html",
    )


@app.post(
    "/api/ask",
    response_model=AskResponse,
)
async def ask(
    payload: AskRequest,
    request: Request,
):
    lock = request.app.state.inference_lock

    # Avoid overlapping inference on the shared models.
    if lock.locked():
        raise HTTPException(
            status_code=429,
            detail=(
                "Another question is processing. "
                "Please try again shortly."
            ),
        )

    async with lock:
        try:
            return await run_in_threadpool(
                answer_question,
                payload.question,
                request.app.state.resources,
            )

        except Exception:
            logger.exception("RAG question failed")

            raise HTTPException(
                status_code=503,
                detail=(
                    "Could not generate an answer. "
                    "Check Ollama and the server terminal, "
                    "then retry."
                ),
            ) from None