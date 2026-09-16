from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

def split_documents(
        documents: list[Document],
        chunk_size : int = 500,
        chunk_overlap: int = 100
) -> list[Document]:


    if not documents:
        raise ValueError(
            f"No documents were provided"
        )

    if chunk_size <= 0 :
        raise ValueError(
            f"Chunk must be greater than 0."
        )

    if chunk_overlap < 0:
        raise ValueError(
            f"Chunk overlap can not be Negative."
        )

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be smaller than chunk_size."
        )



    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=True,
    )

    chunks = splitter.split_documents(documents)

    return chunks