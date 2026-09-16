from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

def load_pdf(file_path: str) -> list[Document]:

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"PDF file not found{file_path}"
        )
    if path.suffix.lower() != ".pdf":
        raise ValueError (
            f"Expected a file but got: {path.suffix}"
        )

    
    loader = PyPDFLoader(
        str(path),
        extraction_mode="layout",

      )
    


    documents = loader.load()

    if not documents:
        raise ValueError(
            f"No content could be extracted from: {file_path}"
        )
    
    return documents