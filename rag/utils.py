
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    """
    Split text into overlapping chunks of approximately `chunk_size` characters.
    
    Args:
        text (str): Full text to split.
        chunk_size (int): Maximum characters per chunk.
        overlap (int): Number of characters to overlap between chunks.

    Returns:
        list: list of text chunks.
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        # Find a good cut point (prefer sentence boundaries)
        end = min(start + chunk_size, len(text))
        if end < len(text):
            # Try to break at a sentence boundary (., !, ?, or newline)
            for sep in ['. ', '! ', '? ', '\n']:
                last_sep = text.rfind(sep, start, end)
                if last_sep != -1:
                    end = last_sep + len(sep)
                    break
        chunks.append(text[start:end].strip())
        # Move start with overlap
        start = max(start + chunk_size - overlap, end - overlap)
        if start >= len(text):
            break

    return chunks