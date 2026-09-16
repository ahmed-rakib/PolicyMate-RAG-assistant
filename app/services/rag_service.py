from langchain_core.documents import Document
from langchain_core.language_models.chat_models import BaseChatModel
from app.prompts.rag_prompt import RAG_PROMPT


def format_context(
    documents: list[Document],
) -> str:

    context_parts: list[str] = []

    for index, document in enumerate(
        documents,
        start=1,
    ):
        page = document.metadata.get(
            "page_label",
            "Unknown",
        )

        content = document.page_content.strip()

        context_parts.append(
            f"[Document {index} | Page {page}]\n"
            f"{content}"
        )

    return "\n\n".join(context_parts)


def generate_answer(
    question: str,
    documents: list[Document],
    llm: BaseChatModel,
) -> str:

    if not question.strip():
        raise ValueError(
            "Question cannot be empty."
        )

    if not documents:
        return (
            "I could not find relevant information "
            "in the provided document."
        )

    context = format_context(
        documents
    )

    messages = RAG_PROMPT.format_messages(
        context=context,
        question=question,
    )

    response = llm.invoke(
        messages
    )

    return str(response.content)