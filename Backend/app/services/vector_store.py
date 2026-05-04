import chromadb
from chromadb.config import Settings
import uuid

# Persistent Chroma client
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(
    name="rag_data",
    metadata={"hnsw:space": "cosine"}
)


def store(embeddings, chunks, metadatas=None):
    """
    Store vectors, chunks, and metadata in ChromaDB
    metadatas: list of dicts same len as chunks
    """
    if not embeddings:
        return
    
    # Generate unique IDs for chunks
    ids = [str(uuid.uuid4()) for _ in chunks]
    
    if metadatas is None:
        metadatas = [{'id': i} for i in range(len(chunks))]
    
    collection.add(
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
        ids=ids
    )
    print(f"Stored {len(chunks)} chunks in ChromaDB")


def search(question_embedding, job_id=None, k=5):
    """
    Semantic search with optional job_id filter
    """
    query_filter = {"job_id": job_id} if job_id else None
    
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=k,
        where=query_filter
    )
    
    return {
        'documents': results['documents'][0],
        'metadatas': results['metadatas'][0],
        'distances': results['distances'][0]
    }

