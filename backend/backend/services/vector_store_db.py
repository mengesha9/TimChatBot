from langchain_community.document_loaders import  (
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredHTMLLoader,
    TextLoader,
    UnstructuredCSVLoader,
    UnstructuredExcelLoader

)

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings


from langchain_chroma import Chroma
from typing import List, Dict
from langchain_core.documents import Document
import os


from dotenv import load_dotenv
from .netsuite_scraper import NetSuiteScraper
import logging

# Load environment variables from .env file
load_dotenv()

# Initialize environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT")
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2")

print("OPENAI_API_KEY:",OPENAI_API_KEY)

EMBEDDING_MODEL = "nomic-embed-text"


# Initialize text splitter and embedding function
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len)
embedding_function = OpenAIEmbeddings()

# Initialize Chroma vector store
vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embedding_function)


def load_and_split_document(file_path: str) -> List[Document]:
    if file_path.endswith('.pdf'):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith('.docx'):
        loader = Docx2txtLoader(file_path)
    elif file_path.endswith('.html'):
        loader = UnstructuredHTMLLoader(file_path)
    elif file_path.endswith('.txt'):
        loader = TextLoader(file_path, encoding='UTF-8')
    elif file_path.endswith('.csv'):
        loader = UnstructuredCSVLoader(file_path,mode="elements")
    elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
        loader = UnstructuredExcelLoader(file_path,mode="elements")
    else:
        raise ValueError(f"Unsupported file type: {file_path}")

    documents = loader.load()
    return text_splitter.split_documents(documents)



def index_document_to_chroma(file_path: str, file_id: int,user_id:int) -> bool:
    try:
        splits = load_and_split_document(file_path)

        # Add metadata to each split
        for split in splits:
            split.metadata['file_id'] = file_id
            split.metadata['user_id'] = user_id

        vectorstore.add_documents(splits)

        return True
    except Exception as e:
        print(f"Error indexing document: {e}")
        return False


def delete_doc_from_chroma(file_id: int,user_id:int):
    try:
        docs = vectorstore.get(where={"file_id": file_id} and {"user_id": user_id})
        print(f"Found {len(docs['ids'])} document chunks for file_id {file_id}")

        vectorstore._collection.delete(where={"file_id": file_id} and {"user_id": user_id})
        print(f"Deleted all documents with file_id {file_id}")

        return True
    except Exception as e:
        print(f"Error deleting document with file_id {file_id} from Chroma: {str(e)}")
        return False

def index_netsuite_docs():
    """Index NetSuite documentation into the vector store"""
    try:
        print("\nStarting to index NetSuite documentation into vector store...")
        scraper = NetSuiteScraper()
        chunks = scraper.get_chunked_documentation()
        
        # Prepare documents for indexing
        documents = []
        metadatas = []
        
        print("\nPreparing documents for indexing...")
        for chunk in chunks:
            documents.append(chunk["content"])
            metadatas.append({
                "title": chunk["title"],
                "url": chunk["url"]
            })
        
        print(f"\nIndexing {len(documents)} chunks into vector store...")
        # Add documents to Chroma
        vectorstore.add_texts(
            texts=documents,
            metadatas=metadatas
        )
        
        # Persist the database
        print("Persisting vector store...")
        vectorstore.persist()
        
        print(f"\nSuccessfully indexed {len(documents)} chunks into vector store!")
        return len(documents)
    except Exception as e:
        print(f"Error indexing NetSuite docs: {str(e)}")
        return 0

def get_relevant_docs(query: str, k: int = 4) -> List[Dict]:
    """Retrieve relevant documents from the vector store"""
    try:
        results = vectorstore.similarity_search_with_metadata(
            query=query,
            k=k
        )
        
        return [{
            "content": doc.page_content,
            "title": doc.metadata.get("title", ""),
            "url": doc.metadata.get("url", "")
        } for doc in results]
    except Exception as e:
        logging.error(f"Error retrieving documents: {str(e)}")
        return []

def clear_vector_store():
    """Clear all documents from the vector store"""
    try:
        vectorstore.delete_collection()
        vectorstore = Chroma(
            persist_directory="./chroma_db",
            embedding_function=embedding_function
        )
        return True
    except Exception as e:
        logging.error(f"Error clearing vector store: {str(e)}")
        return False
