import faiss
import numpy as np

# Use Inner Product for cosine similarity (with normalized vectors)
dimension = 384  # all-MiniLM-L6-v2 produces 384-dimensional embeddings
index = faiss.IndexFlatIP(dimension)
stored_chunks = []


def store(vectors, chunks):
    if not vectors:
        return

    # Normalize vectors for cosine similarity
    arr = np.array(vectors).astype("float32")
    faiss.normalize_L2(arr)

    index.add(arr)
    stored_chunks.extend(chunks)


def search(query_vector, k=5):
    query = np.array([query_vector]).astype("float32")
    faiss.normalize_L2(query)

    distances, indices = index.search(query, k)

    results = []
    for i in indices[0]:
        if i < len(stored_chunks):
            results.append(stored_chunks[i])

    return results