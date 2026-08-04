from typing import List
import logfire


def chunk_text(text: str, chunk_size: int = 1500) -> List[str]:
    """
    Simple semantic-ish chunker that splits by paragraphs
    Ensures chunks do no exceed the specified size.
    """
    with logfire.span(" Text Chunking", text_length=len(text)):
        if not text.strip():
            return []
        
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunks = ""
        
        for p in paragraphs:
            if len(current_chunks) + len(p) < chunk_size:
                current_chunks += p + "\n\n"
                
            else:
                if current_chunks.strip():
                    chunks.append(current_chunks.strip())
                current_chunks = p + "\n\n"
                
        if current_chunks.strip():
            chunks.append(current_chunks.strip())
            
            
        valid_chunks = [c for c in chunks if c.strip()]
        logfire.info(f"Generated {len(valid_chunks)} chunks")
        return valid_chunks