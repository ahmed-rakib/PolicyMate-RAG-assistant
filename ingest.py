from app.services.document_loader import load_pdf
from app.services.text_splitter import split_documents
from app.services.embeddings import get_embedding_model
from app.services.vector_store import build_vector_store,save_vector_store


pdf_path = "data/documents/Company_Policy_Manual.pdf"

vector_store_path = "data/vector_store"

def main()-> None:
    print("starting Document Ingestion...")

    #load pdf
    documents = load_pdf(pdf_path)

    print(f"Documents Loaded {len(documents)}")


    #Split into chunks
    chunks = split_documents(
        documents=documents,
        chunk_size=500,
        chunk_overlap=100
    )
    print(f"Chunk created {len(chunks)}")

    #load embedding Model
    embedding_model = (
        get_embedding_model()
    )
    print("Embedding model Loaded")


    # Build faiss index
    vector_store = build_vector_store(
        chunks=chunks,
        embedding_model=embedding_model
    )
    print("Faiss index created")

    #save index
    save_vector_store(
        vector_store=vector_store,
        directory=vector_store_path
    )
    print(
        f"Vector store saved to {vector_store_path}"
    )

if __name__ == "__main__":
    main()




