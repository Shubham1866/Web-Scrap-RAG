def chunk(text, size=300, overlap=50):
    words = text.split()
    chunks = []

    start = 0
    while start < len(words):
        end = start + size
        chunk_words = words[start:end]

        chunks.append(" ".join(chunk_words))

        start += size - overlap

    return chunks

