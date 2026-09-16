from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

def build_vector_store(
        chunks: list[Document],
        embedding_model:Embeddings)-> FAISS:


    if not chunks:
        raise ValueError(
            "Cannot create vector store from empty chunks."
        )


    vector_store = FAISS.from_documents(
        documents = chunks,
        embedding = embedding_model
    )

    return vector_store

def save_vector_store(
        vector_store: FAISS,
        directory:str
)->None:
    path = Path(directory)
    path.mkdir(
        parents=True,
        exist_ok=True
    )
    vector_store.save_local(
        str(path)
    )

def load_vector_store(
        directory: str,
        embedding_model: Embeddings
    )->FAISS:
        path = Path(directory)
        if not path.exists():
            raise FileNotFoundError(
                f"Vector Store not found {directory}"
            )

        vector_store = FAISS.load_local(
            folder_path=str(path),
            embeddings=embedding_model,
            allow_dangerous_deserialization=True
        )

        return vector_store