from sentence_transformers import SentenceTransformer


model = SentenceTransformer("all-MiniLM-L6-v2")


def embed(chunks):
    if not chunks:
        return []

    return model.encode(chunks, show_progress_bar=False).tolist()